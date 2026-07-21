"""
spec 검증 공통 라이브러리.

각 check_*.py 스크립트가 공유하는 기능:
- SoT 카탈로그 로딩
- file_kind 글롭 확장
- 마크다운 섹션·메타데이터 파싱
- 위반(Violation) 표현과 결과 직렬화
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

# 카탈로그는 표준 라이브러리만으로 파싱 가능한 JSON 형식을 사용한다.
# (사람용 설명은 sot-catalog.README.md, 데이터는 sot-catalog.json)


# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    file: str
    rule: str
    message: str
    line: int | None = None
    file_kind: str | None = None


@dataclass
class CheckResult:
    check: str
    status: str = "pass"
    violations: list[Violation] = field(default_factory=list)

    def add(self, v: Violation) -> None:
        self.violations.append(v)

    def finalize(self) -> "CheckResult":
        self.status = "pass" if not self.violations else "fail"
        return self

    def to_dict(self) -> dict:
        return {
            "check": self.check,
            "status": self.status,
            "violations": [asdict(v) for v in self.violations],
        }


# ---------------------------------------------------------------------------
# 카탈로그 로딩
# ---------------------------------------------------------------------------

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "sot-catalog.json"


def load_catalog(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CATALOG_PATH
    if not p.exists():
        raise FileNotFoundError(f"SoT 카탈로그를 찾을 수 없다: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f) or {}


# ---------------------------------------------------------------------------
# file_kind 확장
# ---------------------------------------------------------------------------

@dataclass
class ResolvedFile:
    path: Path
    kind: str
    kind_def: dict[str, Any]
    exists: bool


def expand_file_kind(
    kind: str,
    kind_def: dict[str, Any],
    project_root: Path,
) -> list[ResolvedFile]:
    """카탈로그의 file_kind 정의를 실제 파일 경로 목록으로 확장한다.

    - path        : 단일 파일. 없어도 항목 1개 반환 (exists=False)
    - path_glob   : glob 패턴. 매칭된 파일들만 반환
    - excluded_subdirs / excluded_files 적용
    """
    excluded_subdirs = set(kind_def.get("excluded_subdirs") or [])
    excluded_files = set(kind_def.get("excluded_files") or [])

    if "path" in kind_def:
        p = project_root / kind_def["path"]
        return [ResolvedFile(p, kind, kind_def, p.exists())]

    if "path_glob" in kind_def:
        matches = sorted(project_root.glob(kind_def["path_glob"]))
        results: list[ResolvedFile] = []
        for m in matches:
            if not m.is_file():
                continue
            rel = m.relative_to(project_root)
            if any(part in excluded_subdirs for part in rel.parts):
                continue
            if m.name in excluded_files:
                continue
            results.append(ResolvedFile(m, kind, kind_def, True))
        return results

    return []


def expand_all_file_kinds(
    catalog: dict[str, Any],
    project_root: Path,
) -> list[ResolvedFile]:
    file_kinds = catalog.get("file_kinds") or {}
    results: list[ResolvedFile] = []
    for kind, kind_def in file_kinds.items():
        results.extend(expand_file_kind(kind, kind_def, project_root))
    return results


# ---------------------------------------------------------------------------
# 마크다운 파싱
# ---------------------------------------------------------------------------

@dataclass
class Section:
    level: int
    title: str
    line: int


_FENCE_RE = re.compile(r"^\s*```")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_META_RE = re.compile(r"^>\s*([^:]+?)\s*:\s*(.+?)\s*$")


def parse_sections(content: str) -> list[Section]:
    """마크다운 ATX 헤더 목록을 추출한다. 코드 블록 내부는 무시한다."""
    in_fence = False
    sections: list[Section] = []
    for i, raw in enumerate(content.splitlines(), start=1):
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(raw)
        if m:
            sections.append(
                Section(level=len(m.group(1)), title=m.group(2).strip(), line=i)
            )
    return sections


def parse_metadata_block(content: str) -> dict[str, str]:
    """파일 상단의 첫 인용 블록(`>`로 시작)에서 키-값 메타데이터를 추출한다.

    예:
        # 제목

        > 버전: v1.0.0
        > 최종 수정: 2026-04-01

    H1과 빈 줄은 인용 블록 진입 전에 통과한다. 인용 블록을 떠나면 종료.
    """
    metadata: dict[str, str] = {}
    in_block = False
    for raw in content.splitlines():
        line = raw.rstrip()
        if line.startswith(">"):
            in_block = True
            m = _META_RE.match(line)
            if m:
                metadata[m.group(1).strip()] = m.group(2).strip()
            continue
        if in_block:
            return metadata
        if not line or line.startswith("# "):
            continue
        return metadata
    return metadata


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def iter_content_lines(content: str):
    """코드 블록(```...```) 외부의 라인만 (line_no, line) 형태로 yield."""
    in_fence = False
    for i, raw in enumerate(content.splitlines(), start=1):
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield i, raw


# ---------------------------------------------------------------------------
# 결과 직렬화
# ---------------------------------------------------------------------------

def dump_result(result: CheckResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


def dump_results(results: Iterable[CheckResult]) -> str:
    rs = list(results)
    fail_count = sum(1 for r in rs if r.status == "fail")
    payload = {
        "status": "pass" if fail_count == 0 else "fail",
        "fail_count": fail_count,
        "checks": [r.to_dict() for r in rs],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
