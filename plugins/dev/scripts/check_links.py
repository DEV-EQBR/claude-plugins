#!/usr/bin/env python3
"""(2) 링크 무결성 체크.

명세서 본문의 [text](path) 마크다운 링크를 모두 추출하여 path가 가리키는
파일이 존재하는지 검사한다.

규칙:
- http://, https://, mailto: 로 시작하는 외부 링크는 (현재) 화이트리스트가 비어
  있으므로 통과시킨다 (네트워크 검사를 하지 않는다)
- 코드 블록 내부 링크는 무시한다 (예시 텍스트일 가능성이 높음)
- 앵커(#section)는 분리하여 파일 존재만 검사한다 — 헤더 슬러그 매칭은 추후
- 상대 경로는 링크가 적힌 파일의 부모 디렉토리 기준으로 해석
- 절대 경로(/로 시작)는 project_root 기준
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


CHECK_NAME = "links"

_DEFAULT_PATTERN = r"\[([^\]]+)\]\(([^)]+)\)"


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    links_cfg = catalog.get("links") or {}
    pattern = links_cfg.get("internal_link_pattern") or _DEFAULT_PATTERN
    regex = re.compile(pattern)

    project_root = project_root.resolve()

    for rf in expand_all_file_kinds(catalog, project_root):
        if not rf.exists:
            continue
        content = read_text(rf.path)
        for line_no, line in iter_content_lines(content):
            for m in regex.finditer(line):
                target_full = m.group(2).strip()
                # 앵커 분리
                target = target_full.split("#", 1)[0]
                if not target:
                    continue  # 같은 파일 내 앵커 (#foo) — 파일 존재 검사 생략
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                # 경로 해석
                if target.startswith("/"):
                    abs_path = project_root / target.lstrip("/")
                else:
                    abs_path = (rf.path.parent / target).resolve()
                if not abs_path.exists():
                    result.add(Violation(
                        file=str(rf.path), line=line_no, file_kind=rf.kind,
                        rule="broken_link",
                        message=f"링크 대상 '{target_full}'이 존재하지 않는다",
                    ))
    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="링크 무결성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
