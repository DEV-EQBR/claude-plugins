#!/usr/bin/env python3
"""design.md 구조 검증 (결정론 전용, LLM judge 없음).

`dev:design` 2단계가 호출한다. 사람 게이트(3단계)가 의미를 검토하므로,
이 스크립트는 **견고한 결정론 체크만** 한다 — 자유서술(Mermaid 등)에서
도메인명을 추출해 참조 정합을 강제하면 false positive가 쌓이므로(메타 원칙:
검증↔작성 1:1 정렬, sot-catalog.README.md), 그런 의미 정합은 사람 게이트에 맡긴다.

검사:
  1. design/design.md 존재 (없으면 hard fail — 설계 단계의 필수 산출물)
  2. 필수 섹션 7종 (## 레벨)
  3. 필수 메타데이터 (> 버전, > 최종 수정)
  4. 최종 수정 날짜 형식 (YYYY-MM-DD)
  5. 도메인 카탈로그 비어있지 않음 (표 데이터 행 1개 이상)

카탈로그(sot-catalog.json)의 file_kinds.design에서 필수 섹션·메타를 읽는다.

종료 코드: 0 = PASS, 1 = 위반, 2 = 실행 실패(카탈로그 로드 등)
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
    dump_results,
    load_catalog,
    parse_metadata_block,
    parse_sections,
    read_text,
)

CHECK_NAME = "design"
DESIGN_KIND = "design"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _section_body(content: str, title: str) -> list[str]:
    """`## {title}` 다음부터 다음 `## ` 전까지의 본문 라인을 반환한다."""
    lines = content.splitlines()
    out: list[str] = []
    capturing = False
    for raw in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw)
        if m:
            lvl, t = len(m.group(1)), m.group(2).strip()
            if capturing and lvl <= 2:
                break
            if lvl == 2 and t == title:
                capturing = True
                continue
        if capturing:
            out.append(raw)
    return out


def _catalog_has_data_row(body: list[str]) -> bool:
    """표에서 헤더·구분선이 아닌 데이터 행이 1개 이상 있는지."""
    seen_separator = False
    for line in body:
        if _TABLE_SEP_RE.match(line):
            seen_separator = True
            continue
        if seen_separator and _TABLE_ROW_RE.match(line):
            # 빈 셀만 있는 행 제외
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if any(cells):
                return True
    return False


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    kind_def = (catalog.get("file_kinds") or {}).get(DESIGN_KIND) or {}
    rel = kind_def.get("path", "design/design.md")
    path = project_root / rel

    # 1. 존재
    if not path.exists():
        result.add(Violation(
            file=str(path), file_kind=DESIGN_KIND, rule="file_exists",
            message=f"설계 산출물 누락: {rel} (dev:design은 항상 design.md를 생산해야 한다)",
        ))
        return result.finalize()

    content = read_text(path)

    # 2. 필수 섹션
    existing = {s.title for s in parse_sections(content) if s.level == 2}
    for required in kind_def.get("required_sections") or []:
        if required not in existing:
            result.add(Violation(
                file=str(path), file_kind=DESIGN_KIND, rule="required_section",
                message=f"필수 섹션 누락: '## {required}'",
            ))

    # 3. 필수 메타데이터
    metadata = parse_metadata_block(content)
    for key in kind_def.get("required_metadata") or []:
        if key not in metadata:
            result.add(Violation(
                file=str(path), file_kind=DESIGN_KIND, rule="required_metadata",
                message=f"필수 메타데이터 누락: '> {key}: ...'",
            ))

    # 4. 최종 수정 날짜 형식
    last_mod = metadata.get("최종 수정")
    if last_mod and not _DATE_RE.match(last_mod):
        result.add(Violation(
            file=str(path), file_kind=DESIGN_KIND, rule="metadata_schema",
            message=f"'최종 수정' 형식 위반(YYYY-MM-DD): '{last_mod}'",
        ))

    # 5. 도메인 카탈로그 비어있지 않음
    if "도메인 카탈로그" in existing:
        body = _section_body(content, "도메인 카탈로그")
        if not _catalog_has_data_row(body):
            result.add(Violation(
                file=str(path), file_kind=DESIGN_KIND, rule="non_empty_catalog",
                message="'## 도메인 카탈로그'에 도메인 행이 없다 (최소 1개 도메인 필요)",
            ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="design.md 구조 검증")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    try:
        catalog = load_catalog(args.catalog)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    result = run(catalog, args.project_root)
    print(dump_results([result]))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
