"""분석 결과 저장/조회 (DB 접근 계층)."""
from app.services.supabase_client import get_supabase


def save_analysis(
    result: dict,
    user_id: str | None,
    cover_letter_id: str | None = None,
    job_posting_id: str | None = None,
) -> None:
    get_supabase().table("analyses").insert({
        "id": result["analysis_id"],
        "user_id": user_id,
        "cover_letter_id": cover_letter_id,
        "job_posting_id": job_posting_id,
        "result_json": result,
    }).execute()


def get_analysis(analysis_id: str) -> dict | None:
    """공유용 조회 — result_json 통째 반환."""
    res = get_supabase().table("analyses").select("result_json").eq("id", analysis_id).execute()
    if not res.data:
        return None
    return res.data[0]["result_json"]


def list_analyses(user_id: str) -> list[dict]:
    """내 분석 기록 — summary만 가볍게."""
    res = (
        get_supabase().table("analyses")
        .select("id, created_at, result_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "overall_summary": (row.get("result_json") or {}).get("overall_summary"),
        }
        for row in res.data
    ]
