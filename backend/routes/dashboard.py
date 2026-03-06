"""Rotas do Dashboard - comparativos e análises por período"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, date, timedelta
from auth.deps import require_permission
from typing import Optional, List
from collections import defaultdict
from database.connection import get_direct_connection, execute_direct_sql, get_supabase_client
from config.settings import TABLE_NAME, DIRECT_URL

router = APIRouter()

VALID_PERIODS = ("year", "semester", "quarter", "month", "week", "day", "range")
_SUPABASE_PAGE_SIZE = 1000


def _use_direct_sql() -> bool:
    """Retorna True se DIRECT_URL está disponível e a conexão funciona."""
    return get_direct_connection() is not None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _month_range(date_from: date, date_to: date):
    """Gera lista de (ano, mês) entre date_from e date_to."""
    out = []
    d = date(date_from.year, date_from.month, 1)
    while d <= date_to:
        out.append((d.year, d.month))
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)
    return out


def _day_range(date_from: date, date_to: date):
    """Gera lista de datas entre date_from e date_to."""
    out = []
    d = date_from
    while d <= date_to:
        out.append(d)
        d += timedelta(days=1)
    return out


def _fill_labels_counts(labels: list, result: list, date_key: str = "bucket", count_key: str = "count"):
    """Preenche contagens por rótulo; result vem do SQL com date_key e count_key."""
    by_label = {str(row[date_key]): int(row[count_key]) for row in result} if result else {}
    counts = [by_label.get(str(lb), 0) for lb in labels]
    return list(zip(labels, counts))


def _fetch_supabase_date_range(column: str, date_from_d: date, date_to_d: date, is_timestamp: bool) -> List[dict]:
    """Busca todas as linhas no intervalo de datas via Supabase (paginação)."""
    supabase = get_supabase_client()
    if is_timestamp:
        from_iso = date_from_d.isoformat() + "T00:00:00"
        to_iso = date_to_d.isoformat() + "T23:59:59.999999"
    else:
        from_iso = date_from_d.isoformat()
        to_iso = date_to_d.isoformat()
    all_rows: List[dict] = []
    offset = 0
    while True:
        q = (
            supabase.table(TABLE_NAME)
            .select(column)
            .gte(column, from_iso)
            .lte(column, to_iso)
            .range(offset, offset + _SUPABASE_PAGE_SIZE - 1)
        )
        resp = q.execute()
        rows = resp.data or []
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < _SUPABASE_PAGE_SIZE:
            break
        offset += _SUPABASE_PAGE_SIZE
    return all_rows


def _bucket_date(d: date, group_by: str) -> date:
    """Retorna a chave de agrupamento (primeiro dia do mês ou da semana, ou o próprio dia)."""
    if group_by == "day":
        return d
    if group_by == "month":
        return date(d.year, d.month, 1)
    if group_by == "week":
        start = d - timedelta(days=d.weekday())
        return start
    return d


def _aggregate_fallback_cadastrados_modificados(
    rows: List[dict], labels: list, group_by: str, date_key: str = "created_at"
) -> list:
    """Agrega linhas do Supabase por bucket e preenche labels (cadastrados ou modificados)."""
    bucket_count: dict = defaultdict(int)
    for row in rows:
        raw = row.get(date_key)
        if raw is None:
            continue
        if isinstance(raw, str):
            try:
                if "T" in raw:
                    d = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
                else:
                    d = datetime.strptime(raw, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
        elif isinstance(raw, datetime):
            d = raw.date()
        elif isinstance(raw, date):
            d = raw
        else:
            continue
        bucket = _bucket_date(d, group_by)
        bucket_count[bucket] = bucket_count.get(bucket, 0) + 1
    return [(lb, bucket_count.get(lb, 0)) for lb in labels]


def _fetch_supabase_aggregate(
    columns: str, date_from_d: Optional[date] = None, date_to_d: Optional[date] = None
) -> List[dict]:
    """Busca colunas da tabela via Supabase, com filtro opcional por date_of_creation."""
    supabase = get_supabase_client()
    select_cols = columns if isinstance(columns, str) else ", ".join(columns)
    q = supabase.table(TABLE_NAME).select(select_cols)
    if date_from_d is not None and date_to_d is not None:
        from_iso = date_from_d.isoformat()
        to_iso = date_to_d.isoformat()
        q = q.gte("date_of_creation", from_iso).lte("date_of_creation", to_iso)
    all_rows: List[dict] = []
    offset = 0
    while True:
        resp = q.range(offset, offset + _SUPABASE_PAGE_SIZE - 1).execute()
        rows = resp.data or []
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < _SUPABASE_PAGE_SIZE:
            break
        offset += _SUPABASE_PAGE_SIZE
    return all_rows


@router.get("/dashboard/cadastrados", summary="Itens cadastrados por período")
def get_cadastrados(
    current_user: dict = Depends(require_permission(2)),
    period: str = Query(..., description="year, semester, quarter, month, week, day, range"),
    year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None, ge=1, le=2),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    month: Optional[int] = Query(None, ge=1, le=12),
    single_date: Optional[str] = Query(None, alias="date", description="Uma data (YYYY-MM-DD) para day/week"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Contagem de itens cadastrados (created_at) no período, agregado por mês ou dia."""
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period deve ser um de: {VALID_PERIODS}")

    today = date.today()
    y = year if year is not None else today.year
    date_from_d: Optional[date] = None
    date_to_d: Optional[date] = None
    group_by = "month"
    labels: list = []

    if period == "year":
        date_from_d = date(y, 1, 1)
        date_to_d = date(y, 12, 31)
        labels = [date(y, m, 1) for m in range(1, 13)]
    elif period == "semester":
        if semester is None:
            raise HTTPException(status_code=400, detail="semester (1 ou 2) é obrigatório")
        if semester == 1:
            date_from_d = date(y, 1, 1)
            date_to_d = date(y, 6, 30)
            labels = [date(y, m, 1) for m in range(1, 7)]
        else:
            date_from_d = date(y, 7, 1)
            date_to_d = date(y, 12, 31)
            labels = [date(y, m, 1) for m in range(7, 13)]
    elif period == "quarter":
        if quarter is None:
            raise HTTPException(status_code=400, detail="quarter (1-4) é obrigatório")
        start_month = (quarter - 1) * 3 + 1
        date_from_d = date(y, start_month, 1)
        end_month = start_month + 2
        if end_month == 12:
            date_to_d = date(y, 12, 31)
        else:
            date_to_d = date(y, end_month + 1, 1) - timedelta(days=1)
        labels = [date(y, m, 1) for m in range(start_month, start_month + 3)]
    elif period == "month":
        m = month if month is not None else today.month
        date_from_d = date(y, m, 1)
        if m == 12:
            date_to_d = date(y, 12, 31)
        else:
            date_to_d = date(y, m + 1, 1) - timedelta(days=1)
        labels = _day_range(date_from_d, date_to_d)
        group_by = "day"
    elif period == "week":
        d = _parse_date(single_date) or today
        start = d - timedelta(days=d.weekday())
        date_from_d = start
        date_to_d = start + timedelta(days=6)
        labels = _day_range(date_from_d, date_to_d)
        group_by = "day"
    elif period == "day":
        d = _parse_date(single_date) or today
        date_from_d = date_to_d = d
        labels = [d]
        group_by = "day"
    else:  # range
        date_from_d = _parse_date(date_from)
        date_to_d = _parse_date(date_to)
        if not date_from_d or not date_to_d:
            raise HTTPException(status_code=400, detail="date_from e date_to são obrigatórios para period=range")
        if date_from_d > date_to_d:
            date_from_d, date_to_d = date_to_d, date_from_d
        delta = (date_to_d - date_from_d).days
        if delta <= 31:
            labels = _day_range(date_from_d, date_to_d)
            group_by = "day"
        else:
            # agrupar por semana: rótulo = início da semana
            labels = []
            w = date_from_d
            while w <= date_to_d:
                labels.append(w)
                w += timedelta(days=7)
            group_by = "week"
    if date_from_d is None or date_to_d is None:
        raise HTTPException(status_code=400, detail="Parâmetros de período inválidos")

    if _use_direct_sql():
        if group_by == "month":
            sql = f"""
                SELECT date_trunc('month', created_at)::date AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (created_at::date >= %s AND created_at::date <= %s)
                GROUP BY date_trunc('month', created_at)
                ORDER BY 1
            """
        elif group_by == "day":
            sql = f"""
                SELECT (created_at::date) AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (created_at::date >= %s AND created_at::date <= %s)
                GROUP BY created_at::date
                ORDER BY 1
            """
        else:
            sql = f"""
                SELECT date_trunc('week', created_at)::date AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (created_at::date >= %s AND created_at::date <= %s)
                GROUP BY date_trunc('week', created_at)
                ORDER BY 1
            """
        result = execute_direct_sql(sql, (date_from_d, date_to_d))
        if result is None:
            raise HTTPException(status_code=500, detail="Erro ao executar consulta no banco.")
        rows = _fill_labels_counts(labels, result)
    else:
        # Tabela pode não ter created_at; usar date_of_creation (DATE) como fallback no Supabase
        raw_rows = _fetch_supabase_date_range("date_of_creation", date_from_d, date_to_d, is_timestamp=False)
        rows = _aggregate_fallback_cadastrados_modificados(raw_rows, labels, group_by, "date_of_creation")
    return {
        "status": "success",
        "period": period,
        "date_from": str(date_from_d),
        "date_to": str(date_to_d),
        "data": [{"label": str(lb), "count": c} for lb, c in rows],
    }


@router.get("/dashboard/modificados", summary="Itens modificados por período")
def get_modificados(
    current_user: dict = Depends(require_permission(2)),
    period: str = Query(..., description="year, semester, quarter, month, week, day, range"),
    year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None, ge=1, le=2),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    month: Optional[int] = Query(None, ge=1, le=12),
    single_date: Optional[str] = Query(None, alias="date"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Contagem de itens modificados (review_date) no período."""
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period deve ser um de: {VALID_PERIODS}")

    today = date.today()
    y = year if year is not None else today.year
    date_from_d: Optional[date] = None
    date_to_d: Optional[date] = None
    group_by = "month"
    labels: list = []

    if period == "year":
        date_from_d = date(y, 1, 1)
        date_to_d = date(y, 12, 31)
        labels = [date(y, m, 1) for m in range(1, 13)]
    elif period == "semester":
        if semester is None:
            raise HTTPException(status_code=400, detail="semester (1 ou 2) é obrigatório")
        if semester == 1:
            date_from_d = date(y, 1, 1)
            date_to_d = date(y, 6, 30)
            labels = [date(y, m, 1) for m in range(1, 7)]
        else:
            date_from_d = date(y, 7, 1)
            date_to_d = date(y, 12, 31)
            labels = [date(y, m, 1) for m in range(7, 13)]
    elif period == "quarter":
        if quarter is None:
            raise HTTPException(status_code=400, detail="quarter (1-4) é obrigatório")
        start_month = (quarter - 1) * 3 + 1
        date_from_d = date(y, start_month, 1)
        end_month = start_month + 2
        date_to_d = date(y, end_month + 1, 1) - timedelta(days=1) if end_month < 12 else date(y, 12, 31)
        labels = [date(y, m, 1) for m in range(start_month, start_month + 3)]
    elif period == "month":
        m = month if month is not None else today.month
        date_from_d = date(y, m, 1)
        date_to_d = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y, 12, 31)
        labels = _day_range(date_from_d, date_to_d)
        group_by = "day"
    elif period == "week":
        d = _parse_date(single_date) or today
        start = d - timedelta(days=d.weekday())
        date_from_d = start
        date_to_d = start + timedelta(days=6)
        labels = _day_range(date_from_d, date_to_d)
        group_by = "day"
    elif period == "day":
        d = _parse_date(single_date) or today
        date_from_d = date_to_d = d
        labels = [d]
        group_by = "day"
    else:
        date_from_d = _parse_date(date_from)
        date_to_d = _parse_date(date_to)
        if not date_from_d or not date_to_d:
            raise HTTPException(status_code=400, detail="date_from e date_to são obrigatórios para period=range")
        if date_from_d > date_to_d:
            date_from_d, date_to_d = date_to_d, date_from_d
        delta = (date_to_d - date_from_d).days
        if delta <= 31:
            labels = _day_range(date_from_d, date_to_d)
            group_by = "day"
        else:
            labels = []
            w = date_from_d
            while w <= date_to_d:
                labels.append(w)
                w += timedelta(days=7)
            group_by = "week"

    if date_from_d is None or date_to_d is None:
        raise HTTPException(status_code=400, detail="Parâmetros de período inválidos")

    if _use_direct_sql():
        if group_by == "month":
            sql = f"""
                SELECT date_trunc('month', review_date)::date AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (review_date >= %s AND review_date <= %s)
                GROUP BY date_trunc('month', review_date)
                ORDER BY 1
            """
        elif group_by == "day":
            sql = f"""
                SELECT review_date AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (review_date >= %s AND review_date <= %s)
                GROUP BY review_date
                ORDER BY 1
            """
        else:
            sql = f"""
                SELECT date_trunc('week', review_date)::date AS bucket, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (review_date >= %s AND review_date <= %s)
                GROUP BY date_trunc('week', review_date)
                ORDER BY 1
            """
        result = execute_direct_sql(sql, (date_from_d, date_to_d))
        if result is None:
            raise HTTPException(status_code=500, detail="Erro ao executar consulta no banco.")
        rows = _fill_labels_counts(labels, result)
    else:
        raw_rows = _fetch_supabase_date_range("review_date", date_from_d, date_to_d, is_timestamp=False)
        rows = _aggregate_fallback_cadastrados_modificados(raw_rows, labels, group_by, "review_date")
    return {
        "status": "success",
        "period": period,
        "date_from": str(date_from_d),
        "date_to": str(date_to_d),
        "data": [{"label": str(lb), "count": c} for lb, c in rows],
    }


@router.get("/dashboard/origin", summary="Contagem por Origin")
def get_origin(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Contagem de itens por valor de origin. Filtro opcional por período (created_at)."""
    date_from_d = _parse_date(date_from) if date_from and date_to else None
    date_to_d = _parse_date(date_to) if date_from and date_to else None
    if date_from and date_to and (not date_from_d or not date_to_d):
        raise HTTPException(status_code=400, detail="date_from e date_to devem ser YYYY-MM-DD")
    if _use_direct_sql():
        if date_from_d and date_to_d:
            sql = f"""
                SELECT COALESCE(origin::text, 'NULL') AS value, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (created_at::date >= %s AND created_at::date <= %s)
                GROUP BY origin
                ORDER BY count DESC
            """
            result = execute_direct_sql(sql, (date_from_d, date_to_d))
        else:
            sql = f"""
                SELECT COALESCE(origin::text, 'NULL') AS value, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                GROUP BY origin
                ORDER BY count DESC
            """
            result = execute_direct_sql(sql)
        if result is None:
            raise HTTPException(status_code=500, detail="Erro ao executar consulta no banco.")
        data = [{"value": row["value"], "count": row["count"]} for row in result]
    else:
        rows = _fetch_supabase_aggregate("origin", date_from_d, date_to_d)
        cnt: dict = defaultdict(int)
        for row in rows:
            v = row.get("origin")
            key = str(v) if v is not None else "NULL"
            cnt[key] += 1
        data = [{"value": k, "count": c} for k, c in sorted(cnt.items(), key=lambda x: -x[1])]
    return {"status": "success", "data": data}


@router.get("/dashboard/situation-osgt", summary="Contagem por Situation_OSGT")
def get_situation_osgt(
    current_user: dict = Depends(require_permission(2)),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Contagem de itens por valor de Situation_OSGT, incluindo NULL como (vazio)."""
    date_from_d = _parse_date(date_from) if date_from and date_to else None
    date_to_d = _parse_date(date_to) if date_from and date_to else None
    if date_from and date_to and (not date_from_d or not date_to_d):
        raise HTTPException(status_code=400, detail="date_from e date_to devem ser YYYY-MM-DD")
    if _use_direct_sql():
        if date_from_d and date_to_d:
            sql = f"""
                SELECT COALESCE("Situation_OSGT", '(vazio)') AS value, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                WHERE (created_at::date >= %s AND created_at::date <= %s)
                GROUP BY "Situation_OSGT"
                ORDER BY count DESC
            """
            result = execute_direct_sql(sql, (date_from_d, date_to_d))
        else:
            sql = f"""
                SELECT COALESCE("Situation_OSGT", '(vazio)') AS value, COUNT(*)::int AS count
                FROM {TABLE_NAME}
                GROUP BY "Situation_OSGT"
                ORDER BY count DESC
            """
            result = execute_direct_sql(sql)
        if result is None:
            raise HTTPException(status_code=500, detail="Erro ao executar consulta no banco.")
        data = [{"value": row["value"], "count": row["count"]} for row in result]
    else:
        # No banco a coluna pode ser situation_osgt (minúsculo); PostgREST/Supabase usa o nome real
        rows = _fetch_supabase_aggregate("situation_osgt", date_from_d, date_to_d)
        cnt = defaultdict(int)
        for row in rows:
            v = row.get("situation_osgt", row.get("Situation_OSGT"))
            if v is None:
                key_val = "(vazio)"
            else:
                key_val = str(v)
            cnt[key_val] += 1
        data = [{"value": k, "count": c} for k, c in sorted(cnt.items(), key=lambda x: -x[1])]
    return {"status": "success", "data": data}
