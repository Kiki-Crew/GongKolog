"""채용공고에서 자소서 평가에 필요한 직무 관련 컨텍스트를 만드는 역할"""
import hashlib
import logging
import re

from app.config import settings
from app.core.llm import call_with_model_fallback_messages
from app.core.prompts import JOB_CONTEXT_SYSTEM_PROMPT, JOB_CONTEXT_USER_TEMPLATE
from app.core.utils import safe_json


logger = logging.getLogger(__name__)
_JOB_CONTEXT_CACHE: dict[str, str] = {}
_LLM_CONTEXT_MIN_ITEMS = 3
_LLM_CONTEXT_MIN_SOURCE_CHARS = 1800
_LLM_CONTEXT_MIN_EXPECTED_SAVE_CHARS = 700


INCLUDE_SECTION_HINTS = (
    "주요업무",
    "주요 업무",
    "담당업무",
    "담당 업무",
    "업무내용",
    "업무 내용",
    "직무소개",
    "직무 소개",
    "수행업무",
    "수행 업무",
    "역할",
    "role",
    "responsibilities",
    "자격요건",
    "자격 요건",
    "지원자격",
    "지원 자격",
    "필수요건",
    "필수 요건",
    "필수사항",
    "필수 사항",
    "요구사항",
    "requirements",
    "우대사항",
    "우대 사항",
    "우대조건",
    "우대 조건",
    "preferred",
    "기술스택",
    "기술 스택",
    "사용기술",
    "사용 기술",
    "역량",
    "경험",
    "이런 분",
    "이런분",
    "이런 사람",
    "이런사람",
    "찾고 있어요",
    "찾고있어요",
    "인재상",
)

EXCLUDE_SECTION_HINTS = (
    "복리후생",
    "복지",
    "혜택",
    "benefits",
    "근무조건",
    "근무 조건",
    "근무지",
    "근무시간",
    "근무 시간",
    "고용형태",
    "고용 형태",
    "급여",
    "연봉",
    "전형절차",
    "전형 절차",
    "전형방법",
    "전형 방법",
    "채용절차",
    "채용 절차",
    "채용과정",
    "채용 과정",
    "합격자 발표",
    "지원방법",
    "지원 방법",
    "지원서 접수",
    "접수기간",
    "접수 기간",
    "접수마감",
    "접수 마감",
    "제출서류",
    "제출 서류",
    "서류반환",
    "서류 반환",
    "문의",
    "유의사항",
    "기타사항",
)

HEADER_RE = re.compile(
    r"^\s*(?:[#>*\-•·◦▶▷■□◆◇\[\]【】()\d.]+)?\s*(.+?)\s*(?:[:：]|$)"
)
SPACE_RE = re.compile(r"\s+")
COMPACT_RE = re.compile(r"[^0-9a-zA-Z가-힣]+")


def _clean(line: str) -> str:
    return SPACE_RE.sub(" ", line.strip()).strip()


def _compact(text: str) -> str:
    return COMPACT_RE.sub("", text).lower()


def _has_hint(line: str, hints: tuple[str, ...]) -> bool:
    compact_line = _compact(line)
    return any(_compact(hint) in compact_line for hint in hints)


def _header_kind(line: str) -> str | None:
    cleaned = _clean(line)
    if not cleaned or len(cleaned) > 90:
        return None

    match = HEADER_RE.match(cleaned)
    title = match.group(1) if match else cleaned

    if _has_hint(title, EXCLUDE_SECTION_HINTS):
        return "exclude"
    if _has_hint(title, INCLUDE_SECTION_HINTS):
        return "include"
    if cleaned.endswith((":", "：")):
        return "neutral"
    return None


_SPLIT_HEADER_KEYS = {
    _compact(hint)
    for hint in (*INCLUDE_SECTION_HINTS, *EXCLUDE_SECTION_HINTS)
    if 2 <= len(_compact(hint)) <= 16
}


def _merge_split_header_lines(lines: list[str]) -> list[str]:
    """짧게 쪼개진 섹션 제목만 복원합니다.

    예: ["근무", "조건"] -> "근무 조건".
    본문과 다음 제목을 붙이지 않도록 합친 문자열이 섹션명과 정확히 같을 때만 병합합니다.
    """
    merged: list[str] = []
    i = 0

    while i < len(lines):
        if _header_kind(lines[i]) is not None:
            merged.append(lines[i])
            i += 1
            continue

        matched = False
        for span in (3, 2):
            if i + span > len(lines):
                continue

            parts = lines[i : i + span]
            compact_parts = [_compact(part) for part in parts]
            if any(not part or len(part) > 8 for part in compact_parts):
                continue

            if "".join(compact_parts) in _SPLIT_HEADER_KEYS:
                merged.append(" ".join(parts))
                i += span
                matched = True
                break

        if not matched:
            merged.append(lines[i])
            i += 1

    return merged


def _append_with_limit(lines: list[str], line: str, max_chars: int) -> bool:
    current = sum(len(item) + 1 for item in lines)
    if current + len(line) + 1 > max_chars:
        return False
    lines.append(line)
    return True


def _without_excluded_sections(lines: list[str]) -> list[str]:
    result: list[str] = []
    section: str | None = None

    for line in lines:
        kind = _header_kind(line)
        if kind is not None:
            section = kind

        if section == "exclude":
            continue
        result.append(line)

    return result


def compact_job_posting(job_posting: str, max_chars: int = 2800) -> str:
    """직무 관련 섹션은 보존하고 행정 섹션만 줄여 EXTRACT 입력을 낮춤"""
    normalized_posting = normalize_job_posting_text(job_posting)

    cleaned_lines = [_clean(line) for line in normalized_posting.splitlines()]
    lines = _merge_split_header_lines([line for line in cleaned_lines if line])

    if not lines:
        return normalized_posting.strip()

    original = "\n".join(lines)
    has_exclude_section = any(_header_kind(line) == "exclude" for line in lines)
    if len(original) <= max_chars and not has_exclude_section:
        return original

    if len(original) <= max_chars and has_exclude_section:
        filtered = "\n".join(_without_excluded_sections(lines)).strip()
        return filtered or original

    selected: list[str] = []
    section: str | None = None
    found_include = False

    for line in lines:
        kind = _header_kind(line)
        if kind is not None:
            section = kind

        if section != "include":
            continue

        found_include = True
        if not _append_with_limit(selected, line, max_chars):
            break

    if found_include and selected:
        return "\n".join(selected)

    fallback_lines = _without_excluded_sections(lines)
    fallback: list[str] = []
    for line in fallback_lines:
        if not _append_with_limit(fallback, line, max_chars):
            break

    return "\n".join(fallback).strip() or original[:max_chars]


def _string_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
        if len(result) >= limit:
            break

    return result


def _append_section(lines: list[str], title: str, items: list[str]) -> None:
    if not items:
        return

    lines.append(f"{title}:")
    for item in items:
        lines.append(f"- {item}")


def _format_job_context(data: dict) -> str:
    lines: list[str] = []

    role_summary = str(data.get("role_summary") or "").strip()
    if role_summary:
        lines.append(f"직무 요약: {role_summary}")

    _append_section(lines, "주요 업무 신호", _string_list(data.get("work_signals"), 4))
    _append_section(lines, "필요 역량 신호", _string_list(data.get("capability_signals"), 4))
    _append_section(lines, "우대/기술 신호", _string_list(data.get("preferred_signals"), 4))
    _append_section(lines, "직무 뉘앙스", _string_list(data.get("nuance"), 2))
    _append_section(lines, "원문 핵심 표현", _string_list(data.get("source_terms"), 8))

    return "\n".join(lines).strip()


def build_job_context(job_posting: str, item_count: int = 1) -> str:
    """공고 원문을 문항별 EXTRACT에 재사용할 짧은 직무 컨텍스트로 변환합니다."""
    fallback_context = compact_job_posting(job_posting)
    source = compact_job_posting(job_posting, max_chars=7000)

    if not source:
        return fallback_context

    expected_save_chars = len(source) - len(fallback_context)

    # 짧은 공고나 문항 수가 적은 요청에서는 Qwen 1회 호출 비용이 절감분보다 큰 이슈
    if (
        settings.mock_llm
        or item_count < _LLM_CONTEXT_MIN_ITEMS
        or len(source) < _LLM_CONTEXT_MIN_SOURCE_CHARS
        or expected_save_chars < _LLM_CONTEXT_MIN_EXPECTED_SAVE_CHARS
    ):
        logger.warning(
            "[JOB_CONTEXT] mode=compact source_chars=%s context_chars=%s items=%s",
            len(source),
            len(fallback_context),
            item_count,
        )
        return fallback_context

    cache_key = hashlib.sha256(source.encode("utf-8")).hexdigest()
    cached = _JOB_CONTEXT_CACHE.get(cache_key)
    if cached:
        return cached

    messages = [
        {
            "role": "system",
            "content": JOB_CONTEXT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": JOB_CONTEXT_USER_TEMPLATE.format(job_posting=source),
        },
    ]

    try:
        raw = call_with_model_fallback_messages(
            messages,
            primary_model=settings.groq_job_context_primary_model,
            backup_model=settings.groq_job_context_backup_model,
            max_completion_tokens=700,
        )
        context = _format_job_context(safe_json(raw))

        if context:
            _JOB_CONTEXT_CACHE[cache_key] = context
            logger.warning(
                "[JOB_CONTEXT] mode=llm source_chars=%s context_chars=%s",
                len(source),
                len(context),
            )
            return context

        logger.warning("[JOB_CONTEXT EMPTY] raw=%s", raw)

    except Exception as e:  # noqa: BLE001
        logger.warning("[JOB_CONTEXT FALLBACK] error=%s", repr(e))

    return fallback_context

def normalize_job_posting_text(text: str) -> str:
    """공고 복붙 텍스트 정리"""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 과도한 공백 정리
    normalized = re.sub(r"[ \t]+", " ", normalized)

    # 한 글자 단위로 깨진 줄바꿈 일부 복구
    normalized = re.sub(r"([가-힣A-Za-z0-9])\n([가-힣A-Za-z0-9])", r"\1 \2", normalized)

    # 기호 앞 줄바꿈 유지
    normalized = re.sub(r"\n\s*▪", "\n▪", normalized)
    normalized = re.sub(r"\n\s*[-•]", "\n- ", normalized)

    # 빈 줄 정리
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()