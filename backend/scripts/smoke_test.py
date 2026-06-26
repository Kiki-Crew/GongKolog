"""분석 파이프라인 스모크 테스트 (스펙 8장 Tier 1 검증).

키/모델 없이 mock 모드로 analyze()를 끝에서 끝까지 1회 실행하고,
응답 스키마 불변식(스펙 3장)을 검증한다.

실행:
    cd backend
    MOCK_LLM=true MOCK_EMBEDDING=true python scripts/smoke_test.py

실제 LLM으로 돌리려면 .env에 키 채우고 MOCK_* 빼고 실행.
"""
import json
import os
import sys

# settings 인스턴스화 전에 mock 강제 (인자 없이 실행해도 mock으로)
os.environ.setdefault("MOCK_LLM", "true")
os.environ.setdefault("MOCK_EMBEDDING", "true")

# backend/ 를 import 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.core import embedding  # noqa: E402
from app.core.pipeline import analyze  # noqa: E402


def ensure_embed_model() -> None:
    """실제 임베딩 모드면 BGE-M3를 직접 로딩 (서버 lifespan 밖에서 실행되므로).

    mock_embedding=true 면 모델이 필요 없으니 건너뛴다.
    """
    if settings.mock_embedding:
        return
    from sentence_transformers import SentenceTransformer

    print(f"BGE-M3 로딩 중... ({settings.embed_model}, 첫 실행 시 ~2GB 다운로드)")
    model = SentenceTransformer(settings.embed_model, device=settings.embed_device)
    embedding.set_model(model)
    print("로딩 완료.\n")

JOB_POSTING = """[채용공고] iOS 개발자
- iOS 앱 개발 및 출시 경험
- Swift 능숙
- 데이터 분석 역량
- 팀 프로젝트 리더십 경험
- 컴퓨터공학 전공 또는 그에 준하는 경력
"""

COVER_LETTER = """저는 스위프트로 앱을 출시한 경험이 있습니다.
팀 프로젝트로 일정 관리 서비스를 만들었습니다.
사용자 피드백을 받아 UI를 개선했습니다.
앱스토어에 직접 배포하고 리뷰에 대응했습니다.
"""

VALID_STATUS = {"met", "weak", "missing"}


def validate(result: dict) -> list[str]:
    """스펙 3장 불변식 검증 → 위반 메시지 리스트 (빈 리스트면 통과)."""
    errors: list[str] = []
    s = result["summary"]
    reqs = result["requirements"]
    sent_ids = {x["id"] for x in result["cover_letter_sentences"]}

    # met+weak+missing == total
    if s["met"] + s["weak"] + s["missing"] != s["total"]:
        errors.append(f"summary 합 불일치: {s}")
    if s["total"] != len(reqs):
        errors.append(f"total({s['total']}) != requirements 수({len(reqs)})")

    counts = {"met": 0, "weak": 0, "missing": 0}
    for r in reqs:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] not in VALID_STATUS:
            errors.append(f"{r['id']}: 잘못된 status {r['status']}")
        # evidence_ids는 실제 문장 id만
        for eid in r["evidence_ids"]:
            if eid not in sent_ids:
                errors.append(f"{r['id']}: 존재하지 않는 evidence id {eid}")
        # status별 규칙 (스펙 3장 표)
        if r["status"] == "missing" and r["evidence_ids"]:
            errors.append(f"{r['id']}: missing인데 evidence 있음")
        if r["status"] == "met" and r["suggestion"] is not None:
            errors.append(f"{r['id']}: met인데 suggestion 있음")
        if r["status"] in ("weak", "missing") and not r["suggestion"]:
            errors.append(f"{r['id']}: {r['status']}인데 suggestion 없음")

    for st in ("met", "weak", "missing"):
        if counts[st] != s[st]:
            errors.append(f"summary.{st}({s[st]}) != 실제 count({counts[st]})")

    return errors


def main() -> int:
    ensure_embed_model()
    result = analyze(JOB_POSTING, COVER_LETTER)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n" + "=" * 50)

    errors = validate(result)
    if errors:
        print("❌ 검증 실패:")
        for e in errors:
            print("  -", e)
        return 1

    s = result["summary"]
    print(
        f"✅ 통과 — 요구사항 {s['total']}개: "
        f"🟢 {s['met']} / 🟡 {s['weak']} / 🔴 {s['missing']} "
        f"(커버리지 {s['coverage_score']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
