#!/usr/bin/env python3
"""(13) 개발 진단 로그 선언 체크.

`conventions/system/local-verification.md`의 **개발 진단 로그** 결정 항목이
`tactical/system.md`의 `## 검증 환경 컨벤션`에 선언됐는지 결정론으로 확인한다.

배경
----
검증 빌드는 실패를 소리 없이 삼키지 않아야 한다 — 에러·예외·경계 이탈을 구조화
진단 로그(`diag:<이음매> ...`, 사실만·판정 없음, 검증 빌드 한정)로 관측 가능하게
해서, 검증 실패 시 코더·검증자가, 개발자 실행 시 사용자가 같은 로그로 원인을
즉시 국소화한다. 코더는 이 로그를 상시 구현하고(의미), verifier는 FAIL 시 발췌해
진단에 담는다(의미). 결정론은 그 앞단 — **스펙이 로그를 선언했는지**만 본다.

트리거 (self-consistent)
------------------------
system.md에 `## 검증 환경 컨벤션`(또는 `검증 환경 컨벤션 …` 추가분) 섹션이 있으면
= local-verification 컨벤션이 적용되는 프로젝트 = 진단 로그 선언 필수. 그 섹션(들)
본문에 라벨 "개발 진단 로그"가 없으면 위반.

no-op (하위호환)
----------------
- system.md 부재(스프린트 초기) → PASS
- 검증 환경 컨벤션 섹션 부재(서비스 없는 프로젝트 등) → PASS

전역 산출물(system.md)이라 --domain 로컬 스코프에선 run_all이 skip(GLOBAL_ONLY).
설정: 카탈로그 `dev_diagnostic_log`(경로·섹션 접두사·라벨).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    Violation,
    dump_result,
    load_catalog,
    read_text,
)

CHECK_NAME = "dev_log"

# system.md는 전역 산출물 — 도메인별로 나눌 수 없다(ledger/traceability와 동일).
GLOBAL_ONLY = True

_DEFAULTS = {
    "system_path": "tactical/system.md",
    "convention_section_prefix": "검증 환경 컨벤션",
    "declaration_label": "개발 진단 로그",
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _cfg(catalog: dict) -> dict:
    c = dict(_DEFAULTS)
    c.update(catalog.get("dev_diagnostic_log") or {})
    return c


def _convention_bodies(content: str, prefix: str) -> tuple[bool, str, int]:
    """제목이 prefix로 시작하는 level-2 섹션(들)의 본문을 합쳐 반환한다.

    반환: (섹션 존재 여부, 합친 본문 텍스트, 첫 섹션 헤더 라인). 코드펜스 내부는
    섹션 판정에 영향 주되(펜스 안 헤더 무시), 본문은 그대로 포함한다(선언 예시 표는
    펜스 안에 있으므로 — 본문 텍스트에 라벨이 있으면 인정).
    """
    lines = content.splitlines()
    in_fence = False
    capturing = False
    found = False
    first_line = 0
    buf: list[str] = []
    for i, raw in enumerate(lines, start=1):
        if re.match(r"^\s*```", raw):
            in_fence = not in_fence
            if capturing:
                buf.append(raw)
            continue
        h = None if in_fence else _HEADING_RE.match(raw)
        if h:
            lvl, title = len(h.group(1)), h.group(2).strip()
            if lvl <= 2:
                if title.startswith(prefix):
                    capturing = True
                    if not found:
                        found = True
                        first_line = i
                    continue
                # 다른 level<=2 헤더 → 캡처 종료
                capturing = False
                continue
        if capturing:
            buf.append(raw)
    return found, "\n".join(buf), first_line


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    cfg = _cfg(catalog)

    system_path = project_root / cfg["system_path"]
    if not system_path.is_file():
        return result.finalize()  # 스프린트 초기 no-op

    content = read_text(system_path)
    found, body, header_line = _convention_bodies(
        content, cfg["convention_section_prefix"])
    if not found:
        return result.finalize()  # 검증 환경 컨벤션 없음 → 컨벤션 미적용 no-op

    if cfg["declaration_label"] not in body:
        try:
            shown = str(system_path.relative_to(project_root))
        except ValueError:
            shown = str(system_path)
        result.add(Violation(
            file=shown, line=header_line, file_kind="system",
            rule="dev_diagnostic_log_declared",
            message=(
                f"'## {cfg['convention_section_prefix']}'에 '{cfg['declaration_label']}' "
                "선언이 없다 — 검증 빌드는 실패를 구조화 진단 로그(diag:…, 사실만·검증 빌드 "
                "한정)로 관측 가능하게 해야 한다(local-verification 컨벤션 결정 항목). "
                "검증 환경 컨벤션 표에 '개발 진단 로그' 행을 추가한다(출력 형식·이음매·"
                "빌드 게이팅·조회 명령)."
            ),
        ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="개발 진단 로그 선언 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
