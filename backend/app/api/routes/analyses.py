"""분석 결과 조회 / 기록 목록 (스펙 6장)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_user
from app.db.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["analyses"])


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    """결과 조회 (공유용 — 인증 불필요)."""
    res = supabase.table("analyses").select("result_json").eq("id", analysis_id).execute()
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "분석 결과를 찾을 수 없습니다.")
    return res.data[0]["result_json"]


@router.get("/analyses")
def list_analyses(user_id: str = Depends(require_user)):
    """내 분석 기록 목록 (인증 필요)."""
    res = (
        supabase.table("analyses")
        .select("id, created_at, result_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    # 목록은 summary만 가볍게 추려서 반환
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "summary": (row.get("result_json") or {}).get("summary"),
        }
        for row in res.data
    ]
