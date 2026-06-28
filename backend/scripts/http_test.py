"""실행 중인 FastAPI 서버에 실제 HTTP 요청을 보내 /api/analyze 검증.

stdlib(urllib)만 사용 — 별도 설치 불필요.

사용법:
    # 1) 다른 터미널에서 서버 먼저 띄우기
    cd backend
    MOCK_LLM=false MOCK_EMBEDDING=false uvicorn app.main:app --port 8000
    # (빠른 점검만 하려면 MOCK_LLM=true MOCK_EMBEDDING=true 로)

    # 2) 이 스크립트로 요청
    python scripts/http_test.py
    # 다른 주소면: python scripts/http_test.py http://localhost:8000
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

PAYLOAD = {
    "job_posting": (
        "[채용공고] 백엔드 개발자\n"
        "- 협업과 코드리뷰를 중시하는 문화\n"
        "- 주도적으로 문제를 정의하고 해결하는 태도"
    ),
    "items": [
        {
            "question": "협업에서 중요한 요소와 그 사례는?",
            "answer": (
                "팀에서 코드리뷰 문화를 제가 먼저 제안해 도입했고, "
                "리뷰를 통해 버그를 30% 줄였습니다."
            ),
        },
        {
            "question": "어려운 목표에 도전한 경험은?",
            "answer": "처음 써보는 FastAPI로 2주 만에 사내 도구를 출시했습니다.",
        },
    ],
}


def main() -> int:
    # health 먼저
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as r:
            print("health:", r.read().decode())
    except urllib.error.URLError as e:
        print(f"❌ 서버에 연결 실패 ({BASE}). uvicorn 띄웠는지 확인. {e}")
        return 1

    # analyze 호출
    req = urllib.request.Request(
        f"{BASE}/api/analyze",
        data=json.dumps(PAYLOAD).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ {e.code}: {e.read().decode()}")
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    ov = result["overall_summary"]
    print(
        f"\n✅ HTTP 응답 정상 — 문항 {ov['total_items']}개 / 카테고리 {ov['total_categories']}개: "
        f"🟢 {ov['met']} / 🟡 {ov['weak']} / 🔴 {ov['missing']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
