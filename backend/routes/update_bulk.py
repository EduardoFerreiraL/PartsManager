"""Rotas de atualização em massa via planilha Excel"""
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
import pandas as pd
import io
import json
from pathlib import Path

from database.connection import get_supabase_client
from config.settings import TABLE_NAME
from routes import stats
from auth.deps import require_permission

router = APIRouter()
supabase = get_supabase_client()

# Colunas incluídas na planilha de atualização (identificador + editáveis)
EXPORT_COLUMNS = [
    "part_number",         # A
    "chinese_description", # B
    "description",        # C
    "ncm",                # D
    "origin",             # E
    "requester",          # F
    "machine",            # G
    "Situation_OSGT",     # H
]
# Larguras das colunas em pixels (A a H) para a planilha gerada
COLUMN_WIDTHS_PX = [105, 294, 455, 90, 60, 100, 80, 105]
ALLOWED_UPDATE_FIELDS = {
    "chinese_description",
    "description",
    "ncm",
    "origin",
    "requester",
    "machine",
    "Situation_OSGT",
}
MAX_PART_NUMBERS = 500
EXPORT_ALL_DIR = Path(__file__).resolve().parents[1] / "tmp_exports"
EXPORT_ALL_META_FILE = EXPORT_ALL_DIR / "pecas_latest.json"
EXPORT_ALL_FILE_BASENAME = "pecas"


def _format_filename_from_date(dt: datetime) -> str:
    return f"{EXPORT_ALL_FILE_BASENAME}-{dt.strftime('%d%m%Y')}.xlsx"


def _read_export_all_metadata() -> dict:
    if not EXPORT_ALL_META_FILE.exists():
        return {"available": False}
    try:
        data = json.loads(EXPORT_ALL_META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"available": False}

    filepath = data.get("filepath")
    if not filepath:
        return {"available": False}
    file_path = Path(filepath)
    if not file_path.exists():
        return {"available": False}

    return {
        "available": True,
        "filename": data.get("filename") or file_path.name,
        "generated_at": data.get("generated_at"),
        "generated_at_display": data.get("generated_at_display"),
        "filepath": str(file_path),
    }


def _save_export_all_metadata(file_path: Path, filename: str, generated_at: datetime) -> dict:
    EXPORT_ALL_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "filename": filename,
        "filepath": str(file_path),
        "generated_at": generated_at.isoformat(),
        "generated_at_display": generated_at.strftime("%d/%m/%Y %H:%M:%S"),
    }
    EXPORT_ALL_META_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "available": True,
        "filename": filename,
        "generated_at": payload["generated_at"],
        "generated_at_display": payload["generated_at_display"],
    }


def _generate_export_all_file() -> dict:
    generated_at = datetime.now()
    filename = _format_filename_from_date(generated_at)
    file_path = EXPORT_ALL_DIR / filename

    # Limpa arquivos antigos do padrão para manter somente o último gerado
    if EXPORT_ALL_DIR.exists():
        for old_file in EXPORT_ALL_DIR.glob(f"{EXPORT_ALL_FILE_BASENAME}-*.xlsx"):
            if old_file != file_path:
                try:
                    old_file.unlink()
                except Exception:
                    pass

    response = supabase.table(TABLE_NAME).select("*").order("part_number", desc=False).execute()
    data = response.data or []
    df = pd.DataFrame(data)

    if "position" in df.columns:
        df = df.drop(columns=["position"])

    for col in ["date_of_creation", "review_date", "created_at"]:
        if col in df.columns and len(df) > 0:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    EXPORT_ALL_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Pecas", index=False)

    meta = _save_export_all_metadata(file_path=file_path, filename=filename, generated_at=generated_at)
    meta["total_itens"] = len(df.index)
    return meta


class ExportPecasBody(BaseModel):
    part_numbers: str = ""


def _parse_part_numbers(part_numbers_str: str) -> list:
    """Parse string de PNs separados por vírgula; retorna lista de inteiros quando possível."""
    if not part_numbers_str or not part_numbers_str.strip():
        return []
    parts = [p.strip() for p in part_numbers_str.split(",") if p.strip()]
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(p)
    return result


def _validate_update_row(row, linha: int):
    """
    Valida uma linha para atualização. Retorna (payload, None) se válido
    ou (None, mensagem_erro) se inválido.
    """
    col_map = {str(c).lower(): c for c in row.index if isinstance(c, str)}
    part_number = None
    for k, v in row.items():
        if str(k).lower() == "part_number" and pd.notna(v) and str(v).strip():
            try:
                part_number = int(float(v))
            except (ValueError, TypeError):
                return None, "Part number inválido"
            break
    if part_number is None:
        return None, "Part number vazio ou ausente"

    update_data = {}
    for col in row.index:
        if not isinstance(col, str):
            continue
        col_lower = col.lower()
        if col_lower == "part_number":
            continue
        if col_lower not in {f.lower(): f for f in ALLOWED_UPDATE_FIELDS}:
            continue
        # Mapear para nome real do banco (ex: Situation_OSGT)
        key = next((f for f in ALLOWED_UPDATE_FIELDS if f.lower() == col_lower), None)
        if not key:
            continue
        val = row[col]
        if pd.isna(val) or (isinstance(val, str) and not val.strip()):
            if key in ("description", "ncm"):
                return None, f"Campo '{key}' não pode ficar vazio"
            continue
        if key == "origin":
            try:
                o = int(float(val))
                if o < 0 or o > 9:
                    return None, "Origin deve ser um número de 0 a 9"
                update_data[key] = o
            except (ValueError, TypeError):
                return None, "Origin deve ser um número"
        elif key == "ncm":
            try:
                n = int(float(val))
                if n <= 0 or len(str(n)) > 8:
                    return None, "NCM inválido"
                update_data[key] = n
            except (ValueError, TypeError):
                return None, "NCM deve ser um número"
        else:
            update_data[key] = str(val).strip() if val is not None else None

    if not update_data:
        return None, "Nenhum campo editável preenchido para atualização"

    if "description" in update_data and (not update_data["description"] or not update_data["description"].strip()):
        return None, "Descrição não pode ficar vazia"
    if "ncm" in update_data and update_data["ncm"] is None:
        return None, "NCM não pode ficar vazio"

    return {"part_number": part_number, "update_data": update_data}, None


@router.post("/export-pecas-for-update", summary="Gerar planilha para atualização em massa")
async def export_pecas_for_update(body: ExportPecasBody, current_user: dict = Depends(require_permission(2))):
    """
    Gera planilha Excel com as linhas completas dos PNs informados (separados por vírgula).
    Body: { "part_numbers": "32326449, 78456132, 78651235" }
    """
    part_numbers_str = body.part_numbers or ""
    pns = _parse_part_numbers(part_numbers_str)
    if not pns:
        raise HTTPException(status_code=400, detail="Informe ao menos um Part Number (separados por vírgula).")
    if len(pns) > MAX_PART_NUMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo de {MAX_PART_NUMBERS} Part Numbers por vez.",
        )

    try:
        # Garantir que colunas existem na tabela (usar nomes exatos)
        table_structure = stats.get_table_structure_impl()
        if table_structure.get("status") == "success" and table_structure.get("colunas_encontradas"):
            available = {c.lower(): c for c in table_structure["colunas_encontradas"]}
            select_cols = [available[c.lower()] for c in EXPORT_COLUMNS if c.lower() in available]
        else:
            select_cols = [c for c in EXPORT_COLUMNS]

        if not select_cols or "part_number" not in [c.lower() for c in select_cols]:
            select_cols = list(EXPORT_COLUMNS)

        response = supabase.table(TABLE_NAME).select(",".join(select_cols)).in_("part_number", pns).execute()
        data = response.data or []

        if not data:
            # Planilha só com cabeçalhos
            df = pd.DataFrame(columns=select_cols)
        else:
            df = pd.DataFrame(data)
            # Ordenar pela ordem dos PNs solicitados
            if "part_number" in df.columns:
                order = {pn: i for i, pn in enumerate(pns)}
                df["_order"] = df["part_number"].map(lambda x: order.get(x, 999))
                df = df.sort_values("_order").drop(columns=["_order"])

        # Formatar datas para exibição legível
        for col in ["date_of_creation", "review_date"]:
            if col in df.columns and len(df) > 0:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Atualização", index=False)
            ws = writer.sheets["Atualização"]
            # Excel: width em unidades de caractere ≈ (pixels - 5) / 7
            for i, px in enumerate(COLUMN_WIDTHS_PX):
                if i < len(EXPORT_COLUMNS):
                    col_letter = chr(65 + i)
                    ws.column_dimensions[col_letter].width = max(1, (px - 5) / 7)
        output.seek(0)
        content = output.read()

        filename = f"Atualizacao_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar planilha: {str(e)}")


@router.get("/export-pecas-all/latest", summary="Metadados da última planilha completa")
async def export_pecas_all_latest(current_user: dict = Depends(require_permission(3))):
    """
    Retorna dados da última planilha completa gerada, se houver.
    """
    try:
        return _read_export_all_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar última planilha: {str(e)}")


@router.get("/export-pecas-all/download", summary="Baixar última planilha completa")
async def export_pecas_all_download(current_user: dict = Depends(require_permission(3))):
    """
    Faz download da última planilha completa gerada.
    """
    meta = _read_export_all_metadata()
    if not meta.get("available"):
        raise HTTPException(status_code=404, detail="Nenhuma planilha completa foi gerada ainda.")

    file_path = Path(meta["filepath"])
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=meta["filename"],
    )


@router.post("/export-pecas-all/generate", summary="Gerar nova planilha completa")
async def export_pecas_all_generate(current_user: dict = Depends(require_permission(3))):
    """
    Gera uma nova planilha completa com todos os itens, salva no servidor
    e retorna seus metadados.
    """
    try:
        return _generate_export_all_file()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar planilha completa: {str(e)}")


@router.post("/upload-excel-update", summary="Enviar planilha para atualização em massa")
async def upload_excel_update(file: UploadFile = File(...), current_user: dict = Depends(require_permission(2))):
    """
    Recebe planilha Excel com part_number e campos editáveis; atualiza cada linha no banco.
    """
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsx são aceitos.")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # Normalizar nomes de colunas (Excel pode vir com variações)
        col_lower = {str(c).lower(): c for c in df.columns}
        if "part_number" not in col_lower:
            raise HTTPException(
                status_code=400,
                detail="A planilha deve conter a coluna 'part_number'.",
            )

        # Obter nomes reais das colunas na tabela (PostgREST é sensível a maiúsculas/minúsculas)
        table_structure = stats.get_table_structure_impl()
        table_columns = table_structure.get("colunas_encontradas") or []
        table_col_by_lower = {str(c).lower(): c for c in table_columns}

        def _filter_update_to_table_columns(payload):
            """Mantém apenas chaves que existem na tabela, usando o nome exato do esquema."""
            out = {}
            for key, value in payload.items():
                if key == "review_date":
                    out[key] = value
                elif key.lower() in table_col_by_lower:
                    out[table_col_by_lower[key.lower()]] = value
            return out

        atualizados = 0
        erros = []

        for idx, row in df.iterrows():
            linha = int(idx) + 2
            validated, err = _validate_update_row(row, linha)
            if err:
                pn = row.get("part_number", row.get("Part_number", "?"))
                erros.append({"linha": linha, "part_number": str(pn), "mensagem": err})
                continue
            part_number = validated["part_number"]
            update_data = validated["update_data"].copy()
            update_data["review_date"] = datetime.now(timezone.utc).date().isoformat()

            # Carimba pelo usuário logado (JWT) quando a coluna existir.
            update_data["added_modified"] = current_user.get("nome")
            update_data = _filter_update_to_table_columns(update_data)

            if len(update_data) <= 1 and "review_date" in update_data:
                erros.append({"linha": linha, "part_number": str(part_number), "mensagem": "Nenhum campo editável existe na tabela para atualizar."})
                continue

            try:
                response = supabase.table(TABLE_NAME).update(update_data).eq("part_number", part_number).execute()
                if response.data:
                    atualizados += 1
                else:
                    erros.append({"linha": linha, "part_number": str(part_number), "mensagem": "Peça não encontrada."})
            except Exception as e:
                msg = str(e)
                if hasattr(e, "args") and e.args and isinstance(e.args[0], dict) and isinstance(e.args[0].get("message"), str):
                    msg = e.args[0]["message"]
                erros.append({"linha": linha, "part_number": str(part_number), "mensagem": msg[:300]})

        if atualizados == 0 and not erros:
            status = "error"
            mensagem = "Nenhuma linha válida para atualização (verifique part_number e colunas)."
        elif erros and atualizados == 0:
            status = "error"
            mensagem = f"Nenhuma peça atualizada. {len(erros)} erro(s) encontrado(s)."
        elif erros:
            status = "partial"
            mensagem = f"{atualizados} peça(s) atualizada(s). {len(erros)} erro(s)."
        else:
            status = "success"
            mensagem = f"{atualizados} peça(s) atualizada(s) com sucesso."

        return {
            "status": status,
            "atualizados": atualizados,
            "erros": erros,
            "mensagem": mensagem,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar planilha: {str(e)}")
