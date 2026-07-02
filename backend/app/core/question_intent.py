from __future__ import annotations


JOB_SIGNAL_LIMIT = 4


def _normalize(text: str) -> str:
    return (text or "").replace(" ", "").replace("\n", "")


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _extract_job_signals(job_context: str, limit: int = JOB_SIGNAL_LIMIT) -> list[str]:
    """공고 신호 추출"""
    signals: list[str] = []

    normalized = (
        job_context or ""
    ).replace("·", "\n").replace("▪", "\n").replace("•", "\n")

    for raw_line in normalized.splitlines():
        line = raw_line.strip(" -•▪·\t")
        if not line:
            continue

        if len(line) < 4:
            continue

        if _has_any(line, ("자격", "TOEIC", "TOEFL", "TEPS", "성적", "졸업", "재학", "휴학")):
            continue

        if _has_any(line, ("정규직 직장 경력", "최소 6개월", "근무할 수", "현재 대학교 휴학")):
            continue

        signals.append(line)

        if len(signals) >= limit:
            break

    return signals


def _category(
    cid: str,
    name: str,
    criteria: str,
    sources: list[str],
    job_signals: list[str] | None = None,
    required_evidence: list[str] | None = None,
) -> dict:
    return {
        "id": cid,
        "category": name,
        "from": sources,
        "criteria": criteria,
        "job_signals": job_signals or [],
        "required_evidence": required_evidence or [],
    }


def detect_question_intent(question: str, job_context: str = "") -> dict:
    """문항 의도 감지"""
    q = _normalize(question)
    job_signals = _extract_job_signals(job_context)

    if _has_any(q, ("지원동기", "지원하게된동기")) and _has_any(q, ("목표", "달성", "인턴기간")):
        return {
            "type": "motivation_goal",
            "use_template": True,
            "allow_job_category": True,
            "categories": [
                _category(
                    "c1",
                    "지원 동기와 경험 연결",
                    "지원자가 제공된 채용공고의 기관이나 직무에 관심을 갖게 된 계기와 본인의 경험이 논리적으로 연결됩니다.",
                    ["문항", "채용공고"],
                    job_signals,
                    required_evidence=[
                        "제공된 채용공고의 기관 또는 직무에 관심을 갖게 된 구체적 계기",
                        "제공된 채용공고의 기관 또는 직무를 선택한 이유",
                        "본인의 경험 또는 준비 과정과 제공된 채용공고 사이의 연결",
                    ],
                ),
                _category(
                    "c2",
                    "인턴 기간 목표의 구체성",
                    "인턴 기간 동안 달성하고자 하는 목표와 실행 방식이 본인의 경험 또는 제공된 채용공고의 업무와 연결됩니다.",
                    ["문항", "채용공고"],
                    job_signals,
                    required_evidence=[
                        "인턴 기간 동안의 명확한 목표",
                        "제공된 채용공고의 업무와 연결된 실행 방식",
                        "목표와 본인의 경험 사이의 연결",
                    ],
                ),
            ],
        }

    if _has_any(q, ("지원분야", "직무", "관련하여")) and _has_any(q, ("강점", "역량", "경험")):
        return {
            "type": "strength_related",
            "use_template": True,
            "allow_job_category": True,
            "categories": [
                _category(
                    "c1",
                    "강점의 경험 근거",
                    "지원자가 제시한 경험에서 본인의 역할, 문제 해결 과정, 산출물, 결과가 구체적으로 확인됩니다.",
                    ["문항"],
                    required_evidence=[
                        "본인이 맡은 역할",
                        "문제 상황 또는 해결 필요성",
                        "구체적인 수행 과정",
                        "결과 또는 산출물",
                    ],
                ),
                _category(
                    "c2",
                    "강점의 업무 전이 가능성",
                    "경험에서 드러난 강점이 제공된 채용공고의 업무 수행 방식으로 어떻게 전이될 수 있는지 확인됩니다.",
                    ["문항", "채용공고"],
                    job_signals,
                    required_evidence=[
                        "경험에서 드러난 강점",
                        "제공된 채용공고의 핵심 업무 요소",
                        "강점이 해당 업무에서 작동하는 구체적 장면",
                    ],
                ),
            ],
        }

    if _has_any(q, ("협업", "타인과", "팀원", "공동", "갈등")):
        return {
            "type": "collaboration",
            "use_template": True,
            "allow_job_category": False,
            "categories": [
                _category(
                    "c1",
                    "협업 상황 속 본인 역할",
                    "협업 과정에서 지원자가 맡은 역할과 실제 행동이 구체적으로 확인됩니다.",
                    ["문항"],
                    required_evidence=[
                        "협업이 필요한 상황",
                        "본인이 맡은 역할",
                        "팀 안에서 수행한 실제 행동",
                    ],
                ),
                _category(
                    "c2",
                    "문제 조율 과정과 결과",
                    "문제 상황을 어떻게 조율했는지와 그 결과 팀이나 과제에 준 영향이 확인됩니다.",
                    ["문항"],
                    required_evidence=[
                        "문제 또는 갈등 상황",
                        "조율하거나 해결한 방식",
                        "팀이나 과제에 준 결과",
                    ],
                ),
            ],
        }

    if _has_any(q, ("문제해결", "문제를해결", "어려움", "도전", "실패", "극복")):
        return {
            "type": "problem_solving",
            "use_template": True,
            "allow_job_category": False,
            "categories": [
                _category(
                    "c1",
                    "문제 인식과 실행 과정",
                    "지원자가 문제를 어떻게 인식했고 어떤 방식으로 해결을 시도했는지 확인됩니다.",
                    ["문항"],
                    required_evidence=[
                        "문제 상황 또는 해결 필요성",
                        "문제를 바라본 본인의 판단 기준",
                        "구체적인 실행 과정",
                    ],
                ),
                _category(
                    "c2",
                    "결과와 배운 점",
                    "문제 해결 과정의 결과와 그 경험을 통해 얻은 배운 점이 구체적으로 확인됩니다.",
                    ["문항"],
                    required_evidence=[
                        "실행 결과 또는 개선 효과",
                        "경험을 통해 배운 점",
                        "이후 행동이나 태도 변화",
                    ],
                ),
            ],
        }

    return {
        "type": "free",
        "use_template": False,
        "allow_job_category": True,
        "categories": [],
    }


def validate_categories(categories: list[dict], intent: dict) -> list[dict]:
    """카테고리 안전장치"""
    if not categories:
        return intent.get("categories", [])

    if intent.get("use_template"):
        return intent.get("categories", categories)

    if intent.get("allow_job_category", True):
        return categories

    blocked_words = (
        "직무 적용",
        "업무 적용",
        "직무 관련",
        "직무 연계",
        "업무 활용",
        "기여",
    )

    has_blocked = any(
        any(word in (category.get("category") or "") for word in blocked_words)
        for category in categories
    )

    if has_blocked and intent.get("categories"):
        return intent["categories"]

    return categories