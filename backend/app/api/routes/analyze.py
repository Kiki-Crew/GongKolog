"""POST /api/analyze — 분석 실행 + 결과 저장 (비로그인 가능)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import optional_user
from app.db.supabase_client import supabase
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import analyze

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def run_analyze(req: AnalyzeRequest, user_id: str | None = Depends(optional_user)):
    if not req.job_posting.strip() or not req.cover_letter.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "공고와 자소서를 모두 입력하세요.")

    try:
        result = analyze(req.job_posting, req.cover_letter)
    except Exception as e:  # LLM/임베딩 실패
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"분석 실패: {e}")

    # 결과 저장 (비로그인이면 user_id=None)
    try:
        supabase.table("analyses").insert({
            "id": result["analysis_id"],
            "user_id": user_id,
            "cover_letter_id": req.cover_letter_id,
            "job_posting_id": req.job_posting_id,
            "result_json": result,
        }).execute()
    except Exception:
        # 저장 실패해도 분석 결과는 반환 (데모 안정성)
        pass

    return result
