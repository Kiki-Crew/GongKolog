"""분석 라우터 — 실행 + 결과 조회/기록 (스펙 v2 2장).

엔드포인트 정의만. 분석 로직은 core, 저장/조회는 services로 위임.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import optional_user, require_user
from app.core.llm import LLMDailyTokenLimitError, LLMRequestTooLargeError
from app.core.pipeline import analyze
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services import analyses as analyses_service

router = APIRouter(prefix="/api", tags=["analyze"])
logger = logging.getLogger(__name__)

MAX_ITEMS = 5  # 문항 상한 (LLM 2N 호출 → 무료 한도 보호, 스펙 v2 TODO)


@router.post("/analyze", response_model=AnalyzeResponse)
def run_analyze(req: AnalyzeRequest, user_id: str | None = Depends(optional_user)):
    """분석 실행 + 결과 저장 (비로그인 가능)."""
    if not req.job_posting.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "채용공고를 입력하세요.")
    if not req.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "문항을 1개 이상 입력하세요.")
    if len(req.items) > MAX_ITEMS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"문항은 최대 {MAX_ITEMS}개까지 가능합니다."
        )
    for it in req.items:
        if not it.question.strip() or not it.answer.strip():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "각 문항의 질문과 답변을 모두 입력하세요."
            )

    try:
        result = analyze(req.job_posting, [it.model_dump() for it in req.items])
    except LLMDailyTokenLimitError as e:
        logger.warning("[ANALYZE ERROR] status=429 error=%s", e)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e))
    except LLMRequestTooLargeError as e:
        logger.warning("[ANALYZE ERROR] status=413 error=%s", e)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(e))
    except Exception as e:  # LLM/임베딩 실패
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"분석 실패: {e}")

    # 비로그인 분석은 저장하지 않음 — "분석 후 즉시 폐기" (개인정보 보호, 스펙 9장)
    # 로그인 사용자만 analyses에 저장 → 마이페이지 기록·공유로 재열람 가능.
    if user_id:
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
