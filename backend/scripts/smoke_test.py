"""분석 파이프라인 스모크 테스트 (스펙 v2 검증).

키/모델 없이 mock 모드로 analyze()를 끝에서 끝까지 1회 실행하고,
응답 스키마 불변식(스펙 v2 2장)을 검증한다.

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
    """실제 임베딩 모드면 BGE-M3를 직접 로딩 (서버 lifespan 밖에서 실행되므로)."""
    if settings.mock_embedding:
        return
    from sentence_transformers import SentenceTransformer

    print(f"BGE-M3 로딩 중... ({settings.embed_model}, 첫 실행 시 ~2GB 다운로드)")
    model = SentenceTransformer(settings.embed_model, device=settings.embed_device)
    embedding.set_model(model)
    print("로딩 완료.\n")


JOB_POSTING = """[채용공고] 백엔드 개발자
- 협업과 코드리뷰를 중시하는 문화
- 주도적으로 문제를 정의하고 해결하는 태도
- 새로운 기술을 빠르게 학습하는 능력
"""

ITEMS = [
    {
        "question": "협업에서 가장 중요하다고 생각하는 요소와 그 사례는?",
        "answer": (
            "팀 프로젝트에서 정산 API를 함께 개발했습니다. "
            "코드리뷰 문화를 제가 먼저 제안해 도입했고, 리뷰를 통해 버그를 30% 줄였습니다. "
            "서로의 코드를 이해하려 매주 짧은 공유 세션도 열었습니다."
        ),
    },
    {
        "question": "어려운 목표에 도전해 본 경험은?",
        "answer": (
            "처음 써보는 FastAPI로 2주 만에 사내 도구를 출시해야 했습니다. "
            "공식 문서를 빠르게 읽고 작은 프로토타입부터 만들어 점진적으로 확장했습니다."
        ),
    },
]

VALID_STATUS = {"met", "weak", "missing"}


def validate(result: dict) -> list[str]:
    """스펙 v2 불변식 검증 → 위반 메시지 리스트 (빈 리스트면 통과)."""
    errors: list[str] = []
    ov = result["overall_summary"]
    items = result["items"]

    if ov["total_items"] != len(items):
        errors.append(f"total_items({ov['total_items']}) != items 수({len(items)})")

    agg = {"met": 0, "weak": 0, "missing": 0}
    total_cat = 0

    for it in items:
        sent_ids = {x["id"] for x in it["answer_sentences"]}
        cats = it["categories"]
        s = it["summary"]

        if s["total"] != len(cats):
            errors.append(f"{it['item_id']}: summary.total != categories 수")

        counts = {"met": 0, "weak": 0, "missing": 0}
        for c in cats:
            counts[c["status"]] = counts.get(c["status"], 0) + 1
            if c["status"] not in VALID_STATUS:
                errors.append(f"{it['item_id']}/{c['id']}: 잘못된 status {c['status']}")
            if "from" not in c:
                errors.append(f"{it['item_id']}/{c['id']}: from 필드 없음")
            # evidence_ids는 같은 item 내 문장만 (스코프 분리)
            for eid in c["evidence_ids"]:
                if eid not in sent_ids:
                    errors.append(f"{it['item_id']}/{c['id']}: 스코프 밖 evidence id {eid}")
            # status별 규칙
            if c["status"] == "missing" and c["evidence_ids"]:
                errors.append(f"{it['item_id']}/{c['id']}: missing인데 evidence 있음")
            if c["status"] == "met" and c["suggestion"] is not None:
                errors.append(f"{it['item_id']}/{c['id']}: met인데 suggestion 있음")
            if c["status"] in ("weak", "missing") and not c["suggestion"]:
                errors.append(f"{it['item_id']}/{c['id']}: {c['status']}인데 suggestion 없음")

        for st in ("met", "weak", "missing"):
            if counts[st] != s[st]:
                errors.append(f"{it['item_id']}: summary.{st} 불일치")
            agg[st] += counts[st]
        total_cat += s["total"]

    for st in ("met", "weak", "missing"):
        if agg[st] != ov[st]:
            errors.append(f"overall.{st}({ov[st]}) != 합({agg[st]})")
    if ov["total_categories"] != total_cat:
        errors.append(f"total_categories({ov['total_categories']}) != 합({total_cat})")

    return errors


def main() -> int:
    ensure_embed_model()
    result = analyze(JOB_POSTING, ITEMS)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n" + "=" * 50)

    errors = validate(result)
    if errors:
        print("❌ 검증 실패:")
        for e in errors:
            print("  -", e)
        return 1

    ov = result["overall_summary"]
    print(
        f"✅ 통과 — 문항 {ov['total_items']}개 / 카테고리 {ov['total_categories']}개: "
        f"🟢 {ov['met']} / 🟡 {ov['weak']} / 🔴 {ov['missing']} "
        f"(커버리지 {ov['coverage_score']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
