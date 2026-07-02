"""4단계 — 카테고리 충족 판정 + 입력 빌더

Groq only:
- 1차: settings.groq_judge_primary_model
- 백업: settings.groq_judge_backup_model
"""

import json
import logging

from app.config import settings
from app.core import mock
from app.core.llm import (
    LLMDailyTokenLimitError,
    LLMRequestTooLargeError,
    call_with_model_fallback_messages,
)
from app.core.prompts import JUDGE_SYSTEM_PROMPT
from app.core.utils import coerce_list, safe_json

logger = logging.getLogger(__name__)


def build_judge_input(categories: list[dict], candidates: dict) -> str:
    """
    LLM 판정 입력 생성
    -> 후보 문장 하나만 넘기면 앞뒤 맥락이 끊김
    (embedding.py에서 만든 context_sentences를 함께 넘겨 흐름을 보존, job_signals는 공고 전체가 아니라 카테고리 판단에 필요한 보조 신호만 제공)
    """
    blocks = []

    for category in categories:
        lines = [
            f'카테고리 {category["id"]}: {category["category"]}',
            f'기준: {category["criteria"]}',
        ]
        required_evidence = list(category.get("required_evidence", []))
        job_signals = category.get("job_signals", [])

        alignment_condition = _job_alignment_condition(category)
        if alignment_condition and alignment_condition not in required_evidence:
            required_evidence = [alignment_condition, *required_evidence]

        if required_evidence:
            lines.append("met 충족 조건:")
            for item in required_evidence:
                lines.append(f"- {item}")

        if job_signals:
            lines.append("채용공고 보조 신호:")
            for signal in job_signals[:3]:
                lines.append(f"- {signal}")

            if _is_job_required_category(category):
                lines.append("공고 신호 판단 규칙:")
                lines.append("- 이 카테고리는 채용공고와의 연결을 직접 평가합니다")
                lines.append("- 답변의 지원 대상, 직무 방향, 업무 목표가 공고와 명확히 충돌하면 관련 조건은 fulfilled=false입니다")
                lines.append("- 공고의 세부 업무명과 표현이 완전히 같지 않아도, 같은 업무 역량으로 전이되는 설명이 있으면 긍정적으로 판단합니다")
            else:
                lines.append("공고 신호 판단 규칙:")
                lines.append("- 이 카테고리는 경험 자체의 구체성을 우선 평가합니다")
                lines.append("- 공고와의 직접 연결 부족만으로 역할, 과정, 산출물, 결과 조건을 false로 만들지 않습니다")

        cand = candidates.get(category["id"], [])

        if cand:
            lines.append("판정용 답변 근거:")

            for item in cand:
                role = item.get("role", "근거")
                context_sentences = item.get("context_sentences") or [item["sentence"]]

                context_text = " ".join(
                    f'{sentence["id"]}: {sentence["text"]}'
                    for sentence in context_sentences
                )

                lines.append(f"- 근거 관점: {role}")
                lines.append(f"  답변 근거: {context_text}")
        else:
            lines.append("판정용 답변 근거: 없음")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def build_full_answer_judge_input(
    categories: list[dict],
    answer_sentences: list[dict],
    question: str = "",
    intent_type: str = "",
) -> str:
    """전체 답변 판정 입력: 답변 문장을 한 번만 전달"""
    lines: list[str] = []

    if question:
        lines.append("[자소서 문항]")
        lines.append(question)

    if intent_type:
        lines.append("")
        lines.append("[문항 유형]")
        lines.append(intent_type)

    lines.append("")
    lines.append("[평가 카테고리]")

    for category in categories:
        lines.append(f'- {category["id"]}: {category["category"]}')
        lines.append(f'  기준: {category["criteria"]}')

        required_evidence = list(category.get("required_evidence", []))
        job_signals = category.get("job_signals", [])

        # 공고 연결 필수 카테고리에만 공고 정합성 조건 추가
        alignment_condition = _job_alignment_condition(category)
        if alignment_condition and alignment_condition not in required_evidence:
            required_evidence = [alignment_condition, *required_evidence]

        if required_evidence:
            lines.append("  met 충족 조건:")
            for item in required_evidence:
                lines.append(f"  - {item}")

        if job_signals:
            lines.append("  채용공고 보조 신호:")
            for signal in job_signals[:3]:
                lines.append(f"  - {signal}")

            if _is_job_required_category(category):
                lines.append("  공고 신호 판단 규칙:")
                lines.append("  - 이 카테고리는 채용공고와의 연결을 직접 평가합니다")
                lines.append("  - 답변의 지원 대상, 직무 방향, 업무 목표가 공고와 충돌하면 관련 조건은 fulfilled=false입니다")
                lines.append("  - 공고의 세부 업무명과 표현이 완전히 같지 않아도, 같은 업무 역량으로 전이되는 설명이 있으면 긍정적으로 판단합니다")
            else:
                lines.append("  공고 신호 판단 규칙:")
                lines.append("  - 이 카테고리는 경험 자체의 구체성을 우선 평가합니다")
                lines.append("  - 공고와의 직접 연결 부족만으로 역할, 과정, 산출물, 결과 조건을 false로 만들지 않습니다")

    lines.append("")
    lines.append("[답변 문장]")
    for sentence in answer_sentences:
        lines.append(f'{sentence["id"]}: {sentence["text"]}')

    return "\n".join(lines)


def judge(
    categories: list[dict],
    candidates: dict | None = None,
    answer_sentences: list[dict] | None = None,
    question: str = "",
    intent_type: str = "",
) -> list[dict]:
    """카테고리별 충족 판정"""
    if settings.mock_llm:
        return mock.mock_judge(categories, candidates or {})

    if not categories:
        return []

    # 짧은 답변 경로
    # pipeline.py에서 answer_sentences를 넘긴 경우 전체 답변 문장을 judge에 전달
    if answer_sentences:
        judge_input = build_full_answer_judge_input(
            categories=categories,
            answer_sentences=answer_sentences,
            question=question,
            intent_type=intent_type,
        )

    # 긴 답변 경로
    # embedding.py에서 뽑은 후보 근거를 judge에 전달
    else:
        judge_input = build_judge_input(categories, candidates or {})

    logger.warning("[JUDGE INPUT]\n%s", judge_input)

    messages = [
        {
            "role": "system",
            "content": JUDGE_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": f"아래 입력을 기준으로 각 카테고리의 met 충족 조건별 충족 여부를 판단하세요.\n\n{judge_input}",
        },
    ]

    for attempt in range(2):
        try:
            raw = call_with_model_fallback_messages(
                messages,
                primary_model=settings.groq_judge_primary_model,
                backup_model=settings.groq_judge_backup_model,
            )

            result = coerce_list(
                safe_json(raw),
                preferred_key="judgments",
            )

            if result:
                return result

            logger.warning("[JUDGE EMPTY] attempt=%s raw=%s", attempt + 1, raw)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("[JUDGE JSON ERROR] attempt=%s error=%s", attempt + 1, repr(e))
            continue

        except (LLMDailyTokenLimitError, LLMRequestTooLargeError):
            raise

        except Exception as e:  # noqa: BLE001
            # 두 Groq 모델이 모두 실패한 경우
            # 빈 리스트를 반환하면 pipeline._normalize_category()에서 missing으로 보정
            logger.warning("[JUDGE LLM ERROR] error=%s", repr(e))
            return []

    return []


def _category_text(category: dict) -> str:
    """카테고리 판단용 텍스트 결합"""
    parts = [
        category.get("category", ""),
        category.get("criteria", ""),
        " ".join(category.get("required_evidence", [])),
    ]
    return " ".join(parts)


def _is_job_required_category(category: dict) -> bool:
    """
    채용공고 연결을 필수로 봐야 하는 카테고리인지 판단

    지원동기, 인턴 목표, 직무 적용, 업무 전이처럼
    문항상 공고와의 연결이 핵심인 카테고리만 true
    """
    text = _category_text(category)

    job_required_keywords = (
        "지원 동기",
        "지원동기",
        "선택한 이유",
        "관심을 갖게 된 계기",
        "인턴 기간 목표",
        "입사 후 목표",
        "업무 목표",
        "직무 목표",
        "업무 전이",
        "전이 가능성",
        "직무 적용",
        "업무 적용",
        "업무 활용",
        "직무 활용",
        "활용 계획",
        "기여 방향",
        "직무 수행",
        "지원 직무",
        "지원 분야",
        "채용공고의 업무",
        "공고의 업무",
        "해당 업무",
    )

    experience_only_keywords = (
        "경험 근거",
        "본인 역할",
        "문제 해결 과정",
        "수행 과정",
        "산출물",
        "결과",
        "성과",
        "상황 속 행동",
        "협업 상황",
        "갈등",
        "배운 점",
    )

    has_job_required = any(keyword in text for keyword in job_required_keywords)
    has_experience_only = any(keyword in text for keyword in experience_only_keywords)

    # 경험 자체를 보는 카테고리는 공고를 필수 감점 기준으로 쓰지 않음
    if has_experience_only and not any(
        keyword in text
        for keyword in (
            "전이",
            "적용",
            "활용",
            "지원 동기",
            "지원동기",
            "목표",
            "지원 분야",
            "지원 직무",
        )
    ):
        return False

    return has_job_required


def _job_alignment_condition(category: dict) -> str | None:
    """공고 연결이 필수인 카테고리에만 추가되는 조건"""
    job_signals = category.get("job_signals", [])

    if not job_signals:
        return None

    if not _is_job_required_category(category):
        return None

    return "답변의 지원 대상, 직무 방향, 업무 목표가 채용공고 보조 신호와 충돌하지 않고 연결됨"