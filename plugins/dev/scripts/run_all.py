#!/usr/bin/env python3
"""spec 검증 deterministic 체크 오케스트레이터.

등록된 모든 체크 모듈을 순서대로 실행하고 통합 JSON 결과를 stdout으로 출력한다.
tactical-verifier 에이전트가 이 결과를 파싱해 1차 판정에 활용한다.

체크 등록은 CHECKS 리스트에서 관리한다. 새 체크를 추가하려면 check_*.py를
작성하고 `run(catalog, project_root) -> CheckResult` 시그니처의 함수를 노출한 뒤
이 리스트에 추가한다.

종료 코드:
  0 = 모든 체크 통과
  1 = 1개 이상 체크에서 위반 발견
  2 = 실행 자체가 실패 (카탈로그 로드 실패 등)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import dump_results, load_catalog  # noqa: E402

import check_coverage  # noqa: E402
import check_cross_refs  # noqa: E402
import check_dev_log  # noqa: E402
import check_glossary  # noqa: E402
import check_history_residue  # noqa: E402
import check_ledger  # noqa: E402
import check_links  # noqa: E402
import check_schemas  # noqa: E402
import check_size_budget  # noqa: E402
import check_template  # noqa: E402
import check_traceability  # noqa: E402
import check_types  # noqa: E402
import check_uniqueness  # noqa: E402


# 등록된 체크 모듈.
CHECKS = [
    check_template,        # (1) 템플릿 적합성
    check_links,           # (2) 링크 무결성
    check_cross_refs,      # (3) cross-reference 정합성
    check_glossary,        # (4) 용어 일관성
    check_schemas,         # (5) 스키마 유효성
    check_types,           # (6) 타입·포맷 정합성
    check_coverage,        # (7) 커버리지 (도메인 필수 파일)
    check_uniqueness,      # (8) 유일성
    check_ledger,          # (9) 검증 원장 백스톱 (L1~L4 + 종결 게이트 L5~L7, 전역 전용)
    check_size_budget,     # (10) 문서 크기 예산 (전량 읽기 가능성)
    check_history_residue, # (11) 이력 잔재 (라이브=현재상태만)
    check_traceability,    # (12) 경계 커버리지 (요구사항→완료기준→AC, 전역 전용)
    check_dev_log,         # (13) 개발 진단 로그 선언 (system.md 검증 환경 컨벤션, 전역 전용)
]


def _scope_to_domain(results, domain: str):
    """--domain 스코프: 해당 도메인의 파일에 대한 위반만 남긴다.

    writer/도메인별 검증의 self-verify용. 도메인 파일은 tactical/domain/{domain}/ 아래
    있으므로 위반 file 경로에 `domain/{domain}/`가 포함되는지로 필터한다(절대·상대 무관).
    cross-domain은 domain="cross-domain"으로 전달하면 tactical/domain/cross-domain/에 매칭된다.
    필터 후 각 체크 status를 재산정한다.
    """
    needle = f"domain/{domain}/"
    for r in results:
        r.violations = [v for v in r.violations if needle in str(v.file).replace("\\", "/")]
        r.status = "pass" if not r.violations else "fail"
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="spec deterministic 체크 일괄 실행")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="스코프: 이 도메인(tactical/domain/{domain}/)의 파일 위반만 보고. "
        "writer self-verify·도메인별 검증용. cross-domain도 도메인명으로 전달",
    )
    parser.add_argument(
        "--boundary",
        type=str,
        default=None,
        choices=["design", "tactical", "implement", "verify", "release"],
        help="경계 종결 게이트(GATE_AWARE 체크에 전달). 오케스트레이터가 단계 전환 전 "
        "'미종결 0'을 강제할 때 지정. 없으면 종결 게이트 미발화(작성 시점 무손상).",
    )
    args = parser.parse_args()

    try:
        catalog = load_catalog(args.catalog)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # 전역 전용 체크(GLOBAL_ONLY)는 --domain 로컬 스코프에서 skip한다.
    # 원장 백스톱은 전역 산출물(tactical/verification-ledger.md)을 보므로 도메인별로
    # 나눌 수 없다 — 도메인 스코프에서 돌리면 항상 전량 필터링돼 무의미하다.
    active = [
        m for m in CHECKS
        if not (args.domain and getattr(m, "GLOBAL_ONLY", False))
    ]
    # GATE_AWARE 모듈에만 --boundary를 전달한다(나머지는 기존 시그니처 유지 = 하위호환).
    results = [
        m.run(catalog, args.project_root, boundary=args.boundary)
        if getattr(m, "GATE_AWARE", False)
        else m.run(catalog, args.project_root)
        for m in active
    ]
    if args.domain:
        results = _scope_to_domain(results, args.domain)

    print(dump_results(results))
    fail_count = sum(1 for r in results if r.status == "fail")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
