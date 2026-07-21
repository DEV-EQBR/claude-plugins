#!/usr/bin/env python3
"""(10) 문서 크기 예산 체크.

상세설계 문서가 "에이전트가 통째로 읽을 수 있는 크기"를 넘었는지 본다.

왜 필요한가
-----------
writer/verifier 에이전트는 권위 문서를 **전량 읽는다**는 전제 위에 서 있고,
결정론 검증과 원장은 그 전제를 근거로 삼는다. 그런데 문서가 컨텍스트 창을 넘으면
그 읽기는 실제로 일어나지 않는다 — 에이전트는 조용히 잘라 읽고, "권위 문서를
읽었다"는 전제만 형식적으로 남는다. 이건 비용 문제가 아니라 **정합성 문제**다.

크기 초과를 무엇으로 보는가
---------------------------
파일이 예산을 넘었다는 건 대개 "문서를 나눠 써야 한다"가 아니라
**도메인 경계가 너무 굵게 잡혔다**는 신호다. 도메인 경계는 전략설계(⓪dev:design)
소유이므로, 이 위반의 정상 처리는 임의 파일 분할이 아니라 **도메인 분리 검토를
위한 bubble-up**이다. 파일을 기계적으로 쪼개면 SoT 카탈로그의 file_kind 경로·
필수 섹션 계약이 깨지고 검증 체계가 함께 무너진다.

설정
----
카탈로그 최상위 `size_budget`에서 관리한다:

    "size_budget": {
      "default_max_bytes": 200000,
      "advisory_bytes": 60000,
      "per_kind": { "design": 300000 }
    }

- `default_max_bytes` 초과 → 위반(fail). 이 크기를 넘으면 전량 읽기가 물리적으로 불가능하다
- `advisory_bytes` 초과 → 위반 아님. 결과에 정보로 남지 않는다(과잉 노이즈 방지);
  writer가 반환 보고에서 스스로 언급하도록 에이전트 지시문이 담당한다
- `per_kind`로 file_kind별 상한을 덮어쓴다

카탈로그에 `size_budget`이 없으면 이 체크는 아무것도 하지 않는다(하위호환).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    Violation,
    dump_result,
    expand_all_file_kinds,
    load_catalog,
)


CHECK_NAME = "size_budget"

RULE_MAX = "doc_size_budget_exceeded"


def _budget_for(kind: str, cfg: dict) -> int | None:
    per_kind = cfg.get("per_kind") or {}
    if kind in per_kind:
        return per_kind[kind]
    return cfg.get("default_max_bytes")


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    cfg = catalog.get("size_budget") or {}
    if not cfg:
        return result.finalize()

    for rf in expand_all_file_kinds(catalog, project_root):
        if not rf.exists:
            continue
        limit = _budget_for(rf.kind, cfg)
        if not limit:
            continue
        try:
            size = rf.path.stat().st_size
        except OSError:
            continue
        if size <= limit:
            continue

        try:
            shown = str(rf.path.relative_to(project_root))
        except ValueError:
            shown = str(rf.path)

        result.add(
            Violation(
                file=shown,
                rule=RULE_MAX,
                file_kind=rf.kind,
                message=(
                    f"{size:,} bytes — 상한 {limit:,} bytes 초과. "
                    "이 크기는 에이전트가 전량 읽을 수 없어 '권위 문서를 읽는다'는 "
                    "전제가 성립하지 않는다. 파일을 임의로 쪼개지 말 것 "
                    "(file_kind 경로·필수 섹션 계약이 깨진다). "
                    "도메인 경계가 너무 굵다는 신호이므로 ⓪dev:design으로 "
                    "bubble-up 하여 도메인 분리를 검토한다."
                ),
            )
        )

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="문서 크기 예산 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
