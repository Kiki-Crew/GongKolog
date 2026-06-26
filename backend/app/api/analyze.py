"""분석 라우터 — 실행 + 결과 조회/기록 (스펙 6장).

엔드포인트 정의만. 분석 로직은 core, 저장/조회는 services로 위임.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import optional_user, require_user
from app.core.pipeline import analyze
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services import analyses as analyses_service

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def run_analyze(req: AnalyzeRequest, user_id: str | None = Depends(optional_user)):
    """분석 실행 + 결과 저장 (비로그인 가능)."""
    if not req.job_posting.strip() or not req.cover_letter.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "공고와 자소서를 모두 입력하세요.")

    try:
        result = analyze(req.job_posting, req.cover_letter)
    except Exception as e:  # LLM/임베딩 실패
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"분석 실패: {e}")

    try:
        analyses_service.save_analysis(
            result, user_id, req.cover_letter_id, req.job_posting_id
        )
    except Exception:
        # 저장 실패해도 분석 결과는 반환 (데모 안정성)
        pass

    return result


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    """결과 조회 (공유용 — 인증 불필요)."""
    result = analyses_service.get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "분석 결과를 찾을 수 없습니다.")
    return result


@router.get("/analyses")
def list_analyses(user_id: str = Depends(require_user)):
    """내 분석 기록 목록 (인증 필요)."""
    return analyses_service.list_analyses(user_id)
