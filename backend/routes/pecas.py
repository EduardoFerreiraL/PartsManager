"""Rotas relacionadas a peças"""
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from database.connection import get_supabase_client
from config.settings import TABLE_NAME
from services.pecas_service import PecasService
from services.excel_service import ExcelService
from services.validation_service import ValidationService
from utils.retry import retry_with_backoff
from auth.deps import get_current_user, require_permission
from routes import stats

router = APIRouter()
pecas_service = PecasService()
excel_service = ExcelService()
validation_service = ValidationService()
supabase = get_supabase_client()

MAX_PART_NUMBERS_BULK = 500


class ByPartNumbersBody(BaseModel):
    """Corpo da busca em lote: texto colado e/ou lista de valores."""

    part_numbers_raw: str = ""
    part_numbers: List[Union[str, int]] = Field(default_factory=list)


def _tokenize_part_numbers_input(
    raw: str, part_numbers: List[Union[str, int]]
) -> List[str]:
    tokens: List[str] = []
    if raw and raw.strip():
        # Espaços, quebras de linha (Excel), tab, vírgula e ; como separadores
        tokens.extend(
            t.strip()
            for t in re.split(r"[\s,;]+", raw.strip())
            if t and str(t).strip()
        )
    for p in part_numbers or []:
        s = str(p).strip()
        if s:
            tokens.append(s)
    return tokens


def _parse_part_number_token(token: str) -> Optional[int]:
    t = token.strip()
    if not t:
        return None
    try:
        return int(float(t))
    except (ValueError, TypeError):
        return None


def _ordered_unique_part_numbers(
    tokens: List[str],
) -> Tuple[List[int], List[str]]:
    """Retorna (lista única ordenada pela primeira ocorrência, tokens inválidos)."""
    ordered: List[int] = []
    seen: set = set()
    invalid: List[str] = []
    for tok in tokens:
        val = _parse_part_number_token(tok)
        if val is None:
            if tok.strip():
                invalid.append(tok.strip())
            continue
        if val not in seen:
            seen.add(val)
            ordered.append(val)
    return ordered, invalid


def _column_exists(column_name: str) -> bool:
    """
    Verifica se uma coluna existe na tabela do Supabase.
    Usado para não quebrar ambientes onde a coluna ainda não foi criada.
    """
    structure = stats.get_table_structure_impl()
    cols = [
        c.lower()
        for c in (structure.get("colunas_encontradas") or [])
        if isinstance(c, str)
    ]
    return column_name.lower() in cols

@router.get("/pecas", summary="Buscar Peças")
@retry_with_backoff(max_retries=3, base_delay=1)
def search_pecas(
    current_user: dict = Depends(get_current_user),
    part_number: str = None,
    description: str = None,
    chinese_description: str = None,
    ncm: str = None,
    origin: str = None,
    date_of_creation: str = None,
    review_date: str = None,
    requester: str = None,
    machine: str = None,
    added_modified: str = None,
    Situation_OSGT: str = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "position",
    order_direction: str = "desc"
):
    """Busca peças com filtros opcionais e paginação otimizada"""
    try:
        # Validar parâmetros de paginação
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 100
        if offset < 0:
            offset = 0
            
        # Validar campo de ordenação
        valid_order_fields = ['part_number', 'description', 'ncm', 'date_of_creation', 'review_date', 'position']
        if order_by not in valid_order_fields:
            order_by = 'position'
            
        # Validar direção de ordenação
        if order_direction.lower() not in ['asc', 'desc']:
            order_direction = 'desc'
        
        query = supabase.table(TABLE_NAME).select("*")
        
        # Aplicar filtros
        if part_number:
            try:
                part_number_int = int(part_number)
                query = query.eq("part_number", part_number_int)
            except ValueError:
                query = query.ilike("part_number::text", f"%{part_number}%")
        
        if description:
            query = query.ilike("description", f"%{description}%")
        
        if chinese_description:
            query = query.ilike("chinese_description", f"%{chinese_description}%")
        
        if ncm:
            try:
                ncm_int = int(ncm)
                query = query.eq("ncm", ncm_int)
            except ValueError:
                query = query.ilike("ncm::text", f"%{ncm}%")
        
        if origin:
            try:
                origin_int = int(origin)
                query = query.eq("origin", origin_int)
            except ValueError:
                query = query.ilike("origin::text", f"%{origin}%")
        
        if date_of_creation:
            query = query.eq("date_of_creation", date_of_creation)
        
        if review_date:
            query = query.eq("review_date", review_date)
        
        if requester:
            query = query.ilike("requester", f"%{requester}%")
        
        if machine:
            query = query.ilike("machine", f"%{machine}%")
        
        if added_modified:
            query = query.ilike("added_modified", f"%{added_modified}%")
        
        if Situation_OSGT:
            # Tratar valores especiais para NULL
            if Situation_OSGT.lower() in ['vazio', 'null', 'none', '']:
                query = query.is_("Situation_OSGT", "null")
            else:
                query = query.eq("Situation_OSGT", Situation_OSGT)
        
        # Aplicar ordenação
        if order_direction.lower() == "desc":
            query = query.order(order_by, desc=True)
        else:
            query = query.order(order_by, desc=False)
        
        # Aplicar paginação
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        filtered_data = pecas_service.filter_position_from_data(response.data)
        
        return {
            "status": "success",
            "pecas": filtered_data,
            "total_encontrado": len(filtered_data),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "current_page": (offset // limit) + 1,
                "has_next": len(filtered_data) == limit
            },
            "filtros_aplicados": {
                "part_number": part_number,
                "description": description,
                "chinese_description": chinese_description,
                "ncm": ncm,
                "origin": origin,
                "date_of_creation": date_of_creation,
                "review_date": review_date,
                "requester": requester,
                "machine": machine,
                "added_modified": added_modified
            }
        }
        
    except Exception as e:
        error_message = str(e)
        if "operator does not exist" in error_message:
            return {
                "status": "error",
                "message": "Erro de tipo de dados nos filtros. O sistema está tentando converter automaticamente os tipos.",
                "detail": error_message,
                "suggestion": "Tente usar números para Part Number e NCM, ou texto para Descrição"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Erro na busca: {error_message}")

@router.get("/pecas/count", summary="Contar Peças com Filtros")
@retry_with_backoff(max_retries=3, base_delay=1)
def count_pecas(
    current_user: dict = Depends(get_current_user),
    part_number: str = None,
    description: str = None,
    chinese_description: str = None,
    ncm: str = None,
    origin: str = None,
    date_of_creation: str = None,
    review_date: str = None,
    requester: str = None,
    machine: str = None,
    added_modified: str = None,
    Situation_OSGT: str = None
):
    """Conta o total de peças que correspondem aos filtros aplicados"""
    try:
        query = supabase.table(TABLE_NAME).select("part_number", count="exact")
        
        # Aplicar os mesmos filtros da busca
        if part_number:
            try:
                part_number_int = int(part_number)
                query = query.eq("part_number", part_number_int)
            except ValueError:
                query = query.ilike("part_number::text", f"%{part_number}%")
        
        if description:
            query = query.ilike("description", f"%{description}%")
        
        if chinese_description:
            query = query.ilike("chinese_description", f"%{chinese_description}%")
        
        if ncm:
            try:
                ncm_int = int(ncm)
                query = query.eq("ncm", ncm_int)
            except ValueError:
                query = query.ilike("ncm::text", f"%{ncm}%")
        
        if origin:
            try:
                origin_int = int(origin)
                query = query.eq("origin", origin_int)
            except ValueError:
                query = query.ilike("origin::text", f"%{origin}%")
        
        if date_of_creation:
            query = query.eq("date_of_creation", date_of_creation)
        
        if review_date:
            query = query.eq("review_date", review_date)
        
        if requester:
            query = query.ilike("requester", f"%{requester}%")
        
        if machine:
            query = query.ilike("machine", f"%{machine}%")
        
        if added_modified:
            query = query.ilike("added_modified", f"%{added_modified}%")
        
        if Situation_OSGT:
            # Tratar valores especiais para NULL
            if Situation_OSGT.lower() in ['vazio', 'null', 'none', '']:
                query = query.is_("Situation_OSGT", "null")
            else:
                query = query.eq("Situation_OSGT", Situation_OSGT)
        
        response = query.execute()
        
        return {
            "status": "success",
            "total_count": response.count if response.count is not None else 0,
            "filtros_aplicados": {
                "part_number": part_number,
                "description": description,
                "chinese_description": chinese_description,
                "ncm": ncm,
                "origin": origin,
                "date_of_creation": date_of_creation,
                "review_date": review_date,
                "requester": requester,
                "machine": machine,
                "added_modified": added_modified,
                "Situation_OSGT": Situation_OSGT
            }
        }
        
    except Exception as e:
        error_message = str(e)
        raise HTTPException(status_code=500, detail=f"Erro ao contar peças: {error_message}")

@router.get("/pecas/all", summary="Buscar Todas as Peças")
@retry_with_backoff(max_retries=3, base_delay=1)
def get_all_pecas(current_user: dict = Depends(get_current_user)):
    """Busca todas as peças sem limitação de quantidade"""
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        filtered_data = pecas_service.filter_position_from_data(response.data)
        
        return {
            "status": "success",
            "pecas": filtered_data,
            "total_encontrado": len(filtered_data),
            "filtros_aplicados": "nenhum"
        }
        
    except Exception as e:
        error_message = str(e)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar todas as peças: {error_message}")


@router.post("/pecas/by-part-numbers", summary="Buscar peças por lista de Part Numbers")
@retry_with_backoff(max_retries=3, base_delay=1)
def search_pecas_by_part_numbers(
    body: ByPartNumbersBody,
    current_user: dict = Depends(get_current_user),
):
    """
    Recebe Part Numbers colados (Excel: uma coluna, quebras de linha, vírgulas, etc.)
    e retorna as linhas completas na ordem solicitada, com lista dos não encontrados.
    """
    tokens = _tokenize_part_numbers_input(
        body.part_numbers_raw or "", body.part_numbers or []
    )
    if not tokens:
        raise HTTPException(
            status_code=400,
            detail="Informe ao menos um Part Number (cole a lista ou envie part_numbers).",
        )

    ordered_unique, invalid_tokens = _ordered_unique_part_numbers(tokens)

    if not ordered_unique:
        raise HTTPException(
            status_code=400,
            detail="Nenhum Part Number válido encontrado na entrada.",
        )

    if len(ordered_unique) > MAX_PART_NUMBERS_BULK:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo de {MAX_PART_NUMBERS_BULK} Part Numbers por requisição.",
        )

    try:
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .in_("part_number", ordered_unique)
            .execute()
        )
        data = response.data or []
        filtered_data = pecas_service.filter_position_from_data(data)
        order_map = {pn: i for i, pn in enumerate(ordered_unique)}
        filtered_data.sort(
            key=lambda r: order_map.get(r.get("part_number"), 10**9)
        )

        found_pns = {r.get("part_number") for r in filtered_data}
        not_found = [pn for pn in ordered_unique if pn not in found_pns]

        return {
            "status": "success",
            "pecas": filtered_data,
            "total_encontrado": len(filtered_data),
            "total_solicitado": len(ordered_unique),
            "not_found_part_numbers": not_found,
            "tokens_invalidos": invalid_tokens,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na busca em lote: {str(e)}"
        )


@router.post("/pecas", summary="Adicionar Nova Peça")
def add_peca(peca_data: dict, current_user: dict = Depends(require_permission(2))):
    """Adiciona uma nova peça ao banco de dados"""
    try:
        # Validar campos obrigatórios
        required_fields = ['part_number', 'description', 'ncm']
        for field in required_fields:
            if not peca_data.get(field):
                raise HTTPException(status_code=400, detail=f"Campo obrigatório '{field}' não fornecido")
        
        # Validar tipos de dados
        try:
            peca_data['part_number'] = int(peca_data['part_number'])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Part Number deve ser um número")
        
        try:
            peca_data['ncm'] = int(peca_data['ncm'])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="NCM deve ser um número")
        
        if 'origin' in peca_data and peca_data['origin']:
            try:
                peca_data['origin'] = int(peca_data['origin'])
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Origin deve ser um número")

        # Carimba pelo usuário logado (JWT) quando a coluna existir.
        if _column_exists("added_modified"):
            peca_data["added_modified"] = current_user.get("nome")
        
        # Verificar se part_number já existe
        existing = supabase.table(TABLE_NAME).select("part_number").eq("part_number", peca_data['part_number']).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail=f"Part Number {peca_data['part_number']} já existe no banco de dados")
        
        # Limpar dados antes de inserir
        cleaned_data = excel_service.clean_data_for_supabase([peca_data], assign_positions=True)
        
        if not cleaned_data:
            raise HTTPException(status_code=400, detail="Dados inválidos após limpeza")
        
        # Inserir no banco
        response = supabase.table(TABLE_NAME).insert(cleaned_data[0]).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Erro ao inserir dados no banco")
        
        filtered_peca = pecas_service.filter_position_from_data(response.data[0])
        
        return {
            "status": "success",
            "message": "Peça adicionada com sucesso",
            "peca": filtered_peca
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"Erro ao adicionar peça: {error_message}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar peça: {error_message}")

@router.put("/pecas/part_number/{part_number}", summary="Atualizar Peça por Part Number")
def update_peca_by_part_number(part_number: str, peca_data: dict, current_user: dict = Depends(require_permission(2))):
    """Atualiza uma peça específica no banco de dados usando part_number como identificador"""
    try:
        try:
            part_number_int = int(part_number)
        except ValueError:
            part_number_int = part_number
        
        # Validar dados recebidos (campos travados: part_number, date_of_creation, review_date)
        allowed_fields = {
            'chinese_description', 'description', 'ncm', 'origin',
            'requester', 'machine', 'Situation_OSGT'
        }
        
        update_data = {k: v for k, v in peca_data.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo válido para atualização")
        
        # Validar campos obrigatórios (apenas os editáveis)
        required_fields = ['description', 'ncm']
        field_display_names = {
            'description': 'Descrição',
            'ncm': 'NCM'
        }
        
        for field in required_fields:
            if field in update_data:
                value = update_data[field]
                if not value or (isinstance(value, str) and value.strip() == ''):
                    field_name = field_display_names.get(field, field)
                    raise HTTPException(
                        status_code=400, 
                        detail=f"O campo '{field_name}' não pode ficar vazio"
                    )
        
        # Review_date só pode ser mutado pelo sistema: definir automaticamente em toda atualização
        update_data['review_date'] = datetime.now(timezone.utc).date().isoformat()

        # Carimba pelo usuário logado (JWT) quando a coluna existir.
        if _column_exists("added_modified"):
            update_data["added_modified"] = current_user.get("nome")
        
        # Atualizar no Supabase
        response = supabase.table(TABLE_NAME).update(update_data).eq("part_number", part_number_int).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Peça com part_number {part_number} não encontrada")
        
        return {
            "status": "success",
            "message": "Peça atualizada com sucesso",
            "peca_atualizada": response.data[0]
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Erro ao atualizar peça: {error_message}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar peça: {error_message}")

@router.delete("/pecas/part_number/{part_number}", summary="Excluir Peça por Part Number")
def delete_peca_by_part_number(part_number: str, current_user: dict = Depends(require_permission(2))):
    """Exclui uma peça específica do banco de dados usando part_number como identificador"""
    try:
        try:
            part_number_int = int(part_number)
        except ValueError:
            part_number_int = part_number
        
        # Verificar se a peça existe
        check_response = supabase.table(TABLE_NAME).select("part_number").eq("part_number", part_number_int).execute()
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail=f"Peça com part_number {part_number} não encontrada")
        
        # Excluir do Supabase
        response = supabase.table(TABLE_NAME).delete().eq("part_number", part_number_int).execute()
        
        return {
            "status": "success",
            "message": f"Peça com part_number {part_number} excluída com sucesso",
            "part_number_excluido": part_number,
            "linhas_afetadas": len(response.data) if response.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"Erro ao excluir peça: {error_message}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir peça: {error_message}")





