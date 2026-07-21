#!/usr/bin/env python3
"""(4) 용어 일관성 체크.

카탈로그 glossary.forbidden_synonyms에 정의된 금지 용어가 상세설계서 본문에
등장하는지 검사한다. canonical 표기 대신 forbidden 동의어를 쓰면 위반이다.

규칙:
- 한글 용어는 substring 매칭 (한국어는 단어 경계 모호)
- 영문 용어는 \\b 단어 경계 매칭
- 코드 블록 내부는 무시 (예시 텍스트 가능성)
- 카탈로그 forbidden_synonyms가 비어 있으면 (현 기본값) 즉시 PASS — 사용자
  프로젝트가 채울 영역
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
    expand_all_file_kinds,
    iter_content_lines,
    load_catalog,
    read_text,
)


CHECK_NAME = "glossary"

_HANGUL_RE = re.compile(r"[ㄱ-힣]")


def _term_matches(term: str, line: str) -> bool:
    if _HANGUL_RE.search(term):
        return term in line
    return re.search(rf"\b{re.escape(term)}\b", line) is not None


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    g = catalog.get("glossary") or {}
    forbidden_entries = g.get("forbidden_synonyms") or []
    if not forbidden_entries:
        return result.finalize()

    for rf in expand_all_file_kinds(catalog, project_root):
        if not rf.exists:
            continue
        content = read_text(rf.path)
        for line_no, line in iter_content_lines(content):
            for entry in forbidden_entries:
                canonical = entry.get("canonical") or "?"
                for term in entry.get("forbidden") or []:
                    if _term_matches(term, line):
                        result.add(Violation(
                            file=str(rf.path), line=line_no, file_kind=rf.kind,
                            rule="forbidden_synonym",
                            message=(
                                f"금지 용어 '{term}' 사용 — 정식 표기는 "
                                f"'{canonical}'"
                            ),
                        ))
    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="용어 일관성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
