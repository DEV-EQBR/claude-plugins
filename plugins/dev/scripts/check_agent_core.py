#!/usr/bin/env python3
"""작성 에이전트 공통 계약 드리프트 린트 (플러그인 내부 전용).

`scripts/writer-core.md`의 정본 블록이 각 에이전트 정의에 **바이트 그대로**
들어 있는지 검사한다.

정본을 `agents/` 밖(여기 `scripts/`)에 두는 이유: 플러그인 로더는 `agents/` 밑의
모든 `.md`를 — frontmatter가 없어도 — 경로 기반 에이전트로 등록한다. 정본을
`agents/`에 두면 `dev:_shared:writer-core` 같은 위임 불가능한 유령 에이전트가
생긴다. 정본은 이 린트만 읽는 소스이므로 린트 옆에 둔다.

run_all.py에 등록하지 않는다 — run_all은 *사용자 프로젝트의 산출물*을 검사하고,
이 스크립트는 *플러그인 자신의 소스*를 검사한다. 성격이 다르다.

왜 참조가 아니라 인라인 + 린트인가
----------------------------------
에이전트 정의에는 include 메커니즘이 없다. "이 파일을 읽어라"는 지시만 가능한데,
harness-design §6.1이 그런 지시의 이행 목표를 90%로 잡는다. 완결 반환 계약·
self-verify는 안전 장치라서 10%가 누락되는 채널에 태울 수 없다. 그래서 텍스트는
인라인으로 두고(100% 주입), 중복의 진짜 비용인 **드리프트**만 이 린트로 막는다.

사용:
    python3 check_agent_core.py            # 위반 시 exit 1
    python3 check_agent_core.py --json     # JSON 출력
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
CANONICAL = Path(__file__).resolve().parent / "writer-core.md"

BLOCK_RE = re.compile(
    r"<!--\s*block:\s*(?P<name>[\w-]+)\s*\|\s*agents:\s*(?P<agents>[^>]*?)\s*-->\n"
    r"(?P<body>.*?)\n<!--\s*/block\s*-->",
    re.DOTALL,
)


def parse_blocks(text: str) -> list[dict]:
    blocks = []
    for m in BLOCK_RE.finditer(text):
        blocks.append({
            "name": m.group("name"),
            "agents": [a.strip() for a in m.group("agents").split(",") if a.strip()],
            "body": m.group("body").strip("\n"),
        })
    return blocks


def agent_path(stem: str) -> Path:
    return AGENTS_DIR / f"{stem}-writer.md"


def run() -> list[dict]:
    if not CANONICAL.exists():
        return [{
            "block": "-", "agent": "-",
            "message": f"정본을 찾을 수 없다: {CANONICAL}",
        }]

    blocks = parse_blocks(CANONICAL.read_text(encoding="utf-8"))
    if not blocks:
        return [{
            "block": "-", "agent": "-",
            "message": f"정본에 블록이 하나도 없다: {CANONICAL}",
        }]

    violations: list[dict] = []
    for blk in blocks:
        for stem in blk["agents"]:
            p = agent_path(stem)
            if not p.exists():
                violations.append({
                    "block": blk["name"], "agent": stem,
                    "message": f"에이전트 파일이 없다: {p.name}",
                })
                continue
            if blk["body"] not in p.read_text(encoding="utf-8"):
                violations.append({
                    "block": blk["name"], "agent": stem,
                    "message": (
                        f"{p.name}의 '{blk['name']}' 블록이 정본과 다르다 (드리프트). "
                        f"정본: {CANONICAL.name}. "
                        "의도한 변경이면 정본을 먼저 고치고 전 대상 에이전트에 반영한다."
                    ),
                })
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description="작성 에이전트 공통 계약 드리프트 린트")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args()

    violations = run()
    if args.json:
        print(json.dumps(
            {"status": "pass" if not violations else "fail",
             "violations": violations},
            ensure_ascii=False, indent=2,
        ))
    elif violations:
        print(f"드리프트 {len(violations)}건:\n")
        for v in violations:
            print(f"  [{v['block']}] {v['agent']}: {v['message']}")
    else:
        blocks = parse_blocks(CANONICAL.read_text(encoding="utf-8"))
        total = sum(len(b["agents"]) for b in blocks)
        print(f"pass — 블록 {len(blocks)}종 × 대상 에이전트 {total}건 모두 정본과 일치")
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
