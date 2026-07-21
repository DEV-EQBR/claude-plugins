#!/usr/bin/env python3
"""(3) cross-reference 정합성 체크.

상세설계서 한 파일이 다른 파일의 SoT를 참조할 때, 그 참조가 실제로 존재하는지 검사한다.
spec-gen 7단계 검증 항목 중 deterministic으로 잡을 수 있는 4건과 CHANGELOG 매핑 3건을 흡수한다.

흡수 매핑:
- api_links_scenario              (7단계 6: api endpoint ↔ scenarios 트리거 매핑)
- api_field_authority_entity      (7단계 8: api 필드 ↔ entities 속성)
- api_auth_role                   (7단계 9: api 인증/인가 ↔ rules 역할별 권한)
- cross_domain_tag_exists         (7단계 4: cross-domain [도메인] 태그)
- fragment_lists_updated_files   (fragment '갱신된 상세설계서' 파일 경로 존재)
- fragment_file_version_matches  (fragment '파일 버전' ↔ spec 파일 메타데이터 '버전' 일치)
- fragment_archive_exists        (tactical-archive/<스프린트 버전>/{spec이하경로} 존재 + 메타 '버전' 일치)
- release_archive_exists         (CHANGELOG.md fold 엔트리 ## v{X.Y.Z} ↔ tactical-archive/v{X.Y.Z}/ 존재)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    CheckResult,
    Violation,
    dump_result,
    expand_file_kind,
    iter_content_lines,
    load_catalog,
    parse_metadata_block,
    parse_sections,
    read_text,
)


CHECK_NAME = "cross_refs"


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

_SCENARIO_ID = re.compile(r"\b(SC-(?:E|R)?\d+|SP-\d+)\b")
_ENTITY_AUTHORITY = re.compile(
    r"entities\.md\s+([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z][a-zA-Z0-9_]*)"
)
_DOMAIN_TAG_LINE = re.compile(r"^\s*\d+\.\s*\[([a-zA-Z][a-zA-Z0-9_-]*)\]")
_TABLE_DIVIDER = re.compile(r"^[:|\-\s]+$")
# api.md 인증 컬럼의 권위 매핑 패턴.
# 예: "rules.md 역할별 권한 EVENT_READ", "rules.md 역할별 권한 ADMIN"
# 매핑이 명시되지 않은 자유 텍스트(예: "고객", "인증 필요")는 검사 대상이 아니다.
_AUTH_AUTHORITY = re.compile(
    r"rules\.md\s+역할별\s*권한\s+([가-힣A-Za-z][가-힣A-Za-z0-9_]*)"
)


def _domain_of(path: Path) -> str | None:
    """tactical/domain/{도메인}/foo.md → 도메인명."""
    parts = path.parts
    if "domain" not in parts:
        return None
    idx = parts.index("domain")
    if idx + 1 < len(parts):
        return parts[idx + 1]
    return None


def _split_md_row(line: str) -> list[str]:
    """마크다운 표 행을 셀 리스트로 분해. `| a | b |` → [a, b]."""
    return [c.strip() for c in line.split("|")[1:-1]]


def _is_divider_row(cells: list[str]) -> bool:
    return all(_TABLE_DIVIDER.match(c) for c in cells if c) or all(
        re.fullmatch(r":?-+:?", c) for c in cells
    )


# ---------------------------------------------------------------------------
# from-side 토큰 추출
# ---------------------------------------------------------------------------

def extract_scenario_refs(content: str) -> list[tuple[str, int]]:
    """본문 어디서든 SC-NNN/SC-EXX/SC-RXX/SP-NNN 토큰 추출."""
    out: list[tuple[str, int]] = []
    for i, line in enumerate(content.splitlines(), start=1):
        for m in _SCENARIO_ID.finditer(line):
            out.append((m.group(1), i))
    return out


def extract_entity_authority_refs(content: str) -> list[tuple[str, str, int]]:
    """본문에서 'entities.md X.Y' 패턴 추출."""
    out: list[tuple[str, str, int]] = []
    for i, line in enumerate(content.splitlines(), start=1):
        for m in _ENTITY_AUTHORITY.finditer(line):
            out.append((m.group(1), m.group(2), i))
    return out


def extract_api_auth_roles(content: str) -> list[tuple[str, int]]:
    """api.md 표 인증 컬럼에서 명시적 권위 매핑(`rules.md 역할별 권한 X`)을
    찾아 역할명 X를 추출한다. 헤더 위치 자동 인식.

    인증 컬럼이 자유 텍스트(예: `고객`, `인증 필요`)면 검사 대상이 아니다 —
    작성 가이드에 enum 매칭이 강제되지 않으므로 검증도 강제하지 않는다
    (메타 원칙: sot-catalog.README.md). 자유 텍스트에서 첫 토큰을 enum과
    매칭하지 말 것.
    """
    out: list[tuple[str, int]] = []
    auth_col_idx: int | None = None
    for i, line in enumerate(content.splitlines(), start=1):
        if not line.startswith("|"):
            auth_col_idx = None
            continue
        cells = _split_md_row(line)
        if not cells:
            continue
        if auth_col_idx is None:
            if "인증" in cells:
                auth_col_idx = cells.index("인증")
            continue
        if _is_divider_row(cells):
            continue
        if len(cells) <= auth_col_idx or not cells[0].startswith("API-"):
            continue
        for m in _AUTH_AUTHORITY.finditer(cells[auth_col_idx]):
            out.append((m.group(1), i))
    return out


def extract_cross_domain_tags(content: str) -> list[tuple[str, int]]:
    """cross-domain 흐름의 '1. [도메인] ...' 패턴에서 태그 추출."""
    out: list[tuple[str, int]] = []
    for i, line in enumerate(content.splitlines(), start=1):
        m = _DOMAIN_TAG_LINE.match(line)
        if m:
            out.append((m.group(1), i))
    return out


# ---------------------------------------------------------------------------
# to-side SoT 인덱스
# ---------------------------------------------------------------------------

def index_scenario_ids_by_domain(catalog: dict, project_root: Path) -> dict[str, set[str]]:
    """domain → {scenario_id} 인덱스. scenarios.md의 헤더 제목에서 ID 추출."""
    index: dict[str, set[str]] = {}
    files = expand_file_kind(
        "domain_scenarios", catalog["file_kinds"]["domain_scenarios"], project_root
    )
    for rf in files:
        domain = _domain_of(rf.path)
        if not domain:
            continue
        ids: set[str] = set()
        for s in parse_sections(read_text(rf.path)):
            m = _SCENARIO_ID.search(s.title)
            if m:
                ids.add(m.group(1))
        index[domain] = ids
    return index


def index_entity_fields_by_domain(
    catalog: dict, project_root: Path
) -> dict[str, dict[str, set[str]]]:
    """domain → entity_name → {field_name} 인덱스.

    entities.md의 ## {엔티티} 섹션 안 ### 속성 표 첫 컬럼을 필드로 본다.
    "엔티티 관계 요약", "가정 목록"은 엔티티가 아니라 메타 섹션이므로 제외.
    """
    index: dict[str, dict[str, set[str]]] = {}
    files = expand_file_kind(
        "domain_entities", catalog["file_kinds"]["domain_entities"], project_root
    )
    skip_titles = {"엔티티 관계 요약", "가정 목록"}
    for rf in files:
        domain = _domain_of(rf.path)
        if not domain:
            continue
        content = read_text(rf.path)
        sections = parse_sections(content)
        # 엔티티 섹션 (level 2) — 메타 섹션 제외
        entity_secs = [
            s for s in sections if s.level == 2 and s.title not in skip_titles
        ]
        lines = content.splitlines()

        entities: dict[str, set[str]] = {}
        for k, sec in enumerate(entity_secs):
            entity = sec.title.strip()
            start = sec.line  # 1-based
            end = entity_secs[k + 1].line - 1 if k + 1 < len(entity_secs) else len(lines)
            fields = _extract_field_names(lines[start:end])
            entities[entity] = fields
        index[domain] = entities
    return index


def _extract_field_names(section_lines: list[str]) -> set[str]:
    """엔티티 섹션 본문 라인들에서 ### 속성 표의 첫 컬럼을 추출."""
    fields: set[str] = set()
    in_attr_section = False
    in_table = False
    header_seen = False
    for line in section_lines:
        head = re.match(r"^###\s+(.+)$", line)
        if head:
            in_attr_section = head.group(1).strip() == "속성"
            in_table = False
            header_seen = False
            continue
        if not in_attr_section:
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        cells = _split_md_row(line)
        if not cells:
            continue
        if not header_seen:
            # 첫 번째 표 라인은 헤더로 간주
            header_seen = True
            in_table = True
            continue
        if _is_divider_row(cells):
            continue
        if in_table and cells[0]:
            fields.add(cells[0])
    return fields


def index_roles_by_domain(catalog: dict, project_root: Path) -> dict[str, set[str]]:
    """domain → {role_name}. rules.md '역할별 권한' 표 첫 컬럼 추출."""
    index: dict[str, set[str]] = {}
    files = expand_file_kind(
        "domain_rules", catalog["file_kinds"]["domain_rules"], project_root
    )
    for rf in files:
        domain = _domain_of(rf.path)
        if not domain:
            continue
        roles: set[str] = set()
        in_section = False
        in_table = False
        header_seen = False
        for line in read_text(rf.path).splitlines():
            head = re.match(r"^##\s+(.+)$", line)
            if head:
                in_section = head.group(1).strip() == "역할별 권한"
                in_table = False
                header_seen = False
                continue
            if not in_section:
                continue
            if not line.startswith("|"):
                in_table = False
                continue
            cells = _split_md_row(line)
            if not cells:
                continue
            if not header_seen:
                header_seen = True
                in_table = True
                continue
            if _is_divider_row(cells):
                continue
            if in_table and cells[0]:
                roles.add(cells[0])
        index[domain] = roles
    return index


def index_existing_domains(project_root: Path) -> set[str]:
    """tactical/domain/ 하위 도메인 디렉토리명 집합 (cross-domain 제외)."""
    domain_dir = project_root / "tactical" / "domain"
    if not domain_dir.is_dir():
        return set()
    return {p.name for p in domain_dir.iterdir() if p.is_dir() and p.name != "cross-domain"}


# ---------------------------------------------------------------------------
# fragment '갱신된 상세설계서' 표 파싱
# ---------------------------------------------------------------------------

_PATH_CELL_RE = re.compile(r"`?([^`\s|]+\.md)`?")


@dataclass
class ChangelogRow:
    path: str
    file_version: str | None
    change: str
    software_version: str | None
    line: int


def extract_fragment_updated_specs(content: str) -> list[ChangelogRow]:
    """fragment(changelog.d/*.md)의 '## 갱신된 상세설계서' 표를 파싱.

    각 행에서 ChangelogRow(path, file_version, change, software_version, line)를 반환한다.
    표 컬럼은 '파일 | 파일 버전 | 변경'. 헤더에 '파일'과 '파일 버전'이 있으면 그
    인덱스를 잡고, 없으면 첫 컬럼을 파일로 본다. software_version(archive 키)은
    fragment 상단 메타데이터 '> 스프린트 버전'(예 1.4.0-add-discount)에서 가져온다.
    """
    out: list[ChangelogRow] = []
    sprint_version = parse_metadata_block(content).get("스프린트 버전")

    in_section = False
    in_table = False
    file_idx: int | None = None
    version_idx: int | None = None
    change_idx: int | None = None

    for i, raw in enumerate(content.splitlines(), start=1):
        head = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw)
        if head:
            in_section = (len(head.group(1)) == 2
                          and head.group(2).strip() == "갱신된 상세설계서")
            in_table = False
            file_idx = version_idx = change_idx = None
            continue

        if not in_section:
            continue

        if not raw.startswith("|"):
            in_table = False
            file_idx = version_idx = change_idx = None
            continue

        cells = _split_md_row(raw)
        if not cells:
            continue

        if file_idx is None:
            # 헤더 행으로 간주
            try:
                file_idx = cells.index("파일")
            except ValueError:
                file_idx = 0
            try:
                version_idx = cells.index("파일 버전")
            except ValueError:
                version_idx = None
            try:
                change_idx = cells.index("변경")
            except ValueError:
                change_idx = None
            in_table = True
            continue

        if _is_divider_row(cells):
            continue

        if not in_table or len(cells) <= file_idx:
            continue

        path_cell = cells[file_idx].strip()
        if not path_cell:
            continue
        m = _PATH_CELL_RE.search(path_cell)
        if not m:
            continue
        path = m.group(1)

        version: str | None = None
        if version_idx is not None and len(cells) > version_idx:
            v = cells[version_idx].strip().strip("`")
            version = v or None

        change = ""
        if change_idx is not None and len(cells) > change_idx:
            change = cells[change_idx].strip()

        out.append(ChangelogRow(
            path=path,
            file_version=version,
            change=change,
            software_version=sprint_version,
            line=i,
        ))
    return out


def extract_release_versions(
    content: str, version_header_pattern: str
) -> list[tuple[str, int]]:
    """CHANGELOG.md(release_changelog)의 '## v{X.Y.Z}' fold 엔트리 헤더에서
    버전 문자열 X.Y.Z 와 라인 번호를 추출한다.

    version_header_pattern은 첫 캡처 그룹이 X.Y.Z가 되도록 정의한다
    (예 '^##\\s+v?(\\d+\\.\\d+\\.\\d+)\\b'). 패턴에 매칭되지 않는 '##' 헤더
    (예 'Unreleased', 다른 섹션)는 릴리스 엔트리가 아니므로 대상에서 제외한다.
    코드 펜스 내부는 무시한다.
    """
    out: list[tuple[str, int]] = []
    pat = re.compile(version_header_pattern)
    for i, raw in iter_content_lines(content):
        m = pat.match(raw)
        if m:
            out.append((m.group(1), i))
    return out


def _is_deletion_row(change: str, deletion_marker_prefix: str) -> bool:
    """'변경' 칸이 deletion_marker_prefix로 시작하면 삭제 행으로 본다.

    공백/구두점 허용: '삭제', '삭제 — ...', '삭제: ...', '삭제됨' 등 모두 매칭.
    """
    if not deletion_marker_prefix:
        return False
    return change.lstrip().startswith(deletion_marker_prefix)


def _normalize_version(v: str | None) -> str | None:
    """버전 표기 형식(v 접두사)은 작성 가이드가 강제하지 않으므로
    `1.50.0`과 `v1.50.0`을 동치로 본다. 비교는 정규화 후 수행.

    메타 원칙: 검증↔작성 1:1 정렬 (sot-catalog.README.md).
    """
    if v is None:
        return None
    s = v.strip().strip("`").strip()
    if s[:1] in ("v", "V"):
        s = s[1:]
    return s


def _normalize_domain_name(name: str) -> str:
    """도메인 태그/엔티티 이름의 단복수 변형을 동치로 본다 (영문 간단 규칙).

    작성 에이전트는 도메인을 의미로 참조하므로(`todo`/`todos`/`event`/`events` 등
    자연어 변형 자유), 검증도 자연어 동치를 인정한다.

    메타 원칙: 검증↔작성 1:1 정렬 (sot-catalog.README.md).
    """
    n = name.strip().lower()
    if n.endswith("ies") and len(n) > 3:
        return n[:-3] + "y"
    if n.endswith("ses") and len(n) > 3:
        return n[:-2]
    if n.endswith("es") and len(n) > 2 and n[-3] in ("s", "x", "z", "h"):
        return n[:-2]
    if n.endswith("s") and len(n) > 1 and not n.endswith("ss"):
        return n[:-1]
    return n


# ---------------------------------------------------------------------------
# 체크 실행
# ---------------------------------------------------------------------------

def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    fk = catalog["file_kinds"]

    scenarios_idx = index_scenario_ids_by_domain(catalog, project_root)
    entities_idx = index_entity_fields_by_domain(catalog, project_root)
    roles_idx = index_roles_by_domain(catalog, project_root)
    domain_dirs = index_existing_domains(project_root)

    # api.md 순회
    for rf in expand_file_kind("domain_api", fk["domain_api"], project_root):
        domain = _domain_of(rf.path)
        if not domain:
            continue
        content = read_text(rf.path)

        existing_scenarios = scenarios_idx.get(domain, set())
        for sc_id, line_no in extract_scenario_refs(content):
            if sc_id not in existing_scenarios:
                result.add(Violation(
                    file=str(rf.path), line=line_no, file_kind="domain_api",
                    rule="api_links_scenario",
                    message=f"참조한 시나리오 {sc_id}이 {domain}/scenarios.md에 없다",
                ))

        existing_entities = entities_idx.get(domain, {})
        # 엔티티 이름의 단/복수형 변형을 동치로 인정 (메타 원칙: 작성 가이드에
        # 단복수 룰이 없으므로 검증도 자연어 동치). 정규화 키로 보조 인덱스.
        normalized_entities = {
            _normalize_domain_name(name): (name, fields)
            for name, fields in existing_entities.items()
        }
        for entity, field, line_no in extract_entity_authority_refs(content):
            if entity in existing_entities:
                fields = existing_entities[entity]
            else:
                hit = normalized_entities.get(_normalize_domain_name(entity))
                fields = hit[1] if hit else None
            if fields is None:
                result.add(Violation(
                    file=str(rf.path), line=line_no, file_kind="domain_api",
                    rule="api_field_authority_entity",
                    message=f"권위 참조 엔티티 '{entity}'이 {domain}/entities.md에 없다",
                ))
            elif field not in fields:
                result.add(Violation(
                    file=str(rf.path), line=line_no, file_kind="domain_api",
                    rule="api_field_authority_entity",
                    message=f"권위 참조 필드 '{entity}.{field}'이 {domain}/entities.md에 없다",
                ))

        existing_roles = roles_idx.get(domain, set())
        for role, line_no in extract_api_auth_roles(content):
            if role not in existing_roles:
                result.add(Violation(
                    file=str(rf.path), line=line_no, file_kind="domain_api",
                    rule="api_auth_role",
                    message=f"인증 역할 '{role}'이 {domain}/rules.md 역할별 권한에 없다",
                ))

    # cross-domain 흐름 순회. 도메인 단/복수형 변형은 동치로 인정 (메타 원칙).
    normalized_dirs = {_normalize_domain_name(d): d for d in domain_dirs}
    for rf in expand_file_kind("cross_domain_flow", fk["cross_domain_flow"], project_root):
        for tag, line_no in extract_cross_domain_tags(read_text(rf.path)):
            if tag in domain_dirs:
                continue
            if _normalize_domain_name(tag) in normalized_dirs:
                continue
            result.add(Violation(
                file=str(rf.path), line=line_no, file_kind="cross_domain_flow",
                rule="cross_domain_tag_exists",
                message=f"흐름이 참조한 도메인 [{tag}]에 해당하는 tactical/domain/{tag}/ 디렉토리가 없다",
            ))

    # fragment(changelog.d/*.md)의 '갱신된 상세설계서' 표 검증
    cross_refs_cfg = catalog.get("cross_refs") or {}
    archive_cfg = cross_refs_cfg.get("fragment_archive_exists") or {}
    deletion_marker = archive_cfg.get("deletion_marker_prefix", "삭제")

    if "fragment" in fk:
        for rf in expand_file_kind("fragment", fk["fragment"], project_root):
            if not rf.exists:
                continue
            content = read_text(rf.path)
            for row in extract_fragment_updated_specs(content):
                # 삭제 행은 path/version/archive 검증 모두 스킵
                if _is_deletion_row(row.change, deletion_marker):
                    continue

                target = project_root / row.path
                if not target.is_file():
                    result.add(Violation(
                        file=str(rf.path), line=row.line, file_kind="fragment",
                        rule="fragment_lists_updated_files",
                        message=f"fragment가 참조한 파일 '{row.path}'이 실제로 존재하지 않는다",
                    ))
                    continue
                if row.file_version:
                    actual = parse_metadata_block(read_text(target)).get("버전")
                    if actual is None:
                        result.add(Violation(
                            file=str(rf.path), line=row.line, file_kind="fragment",
                            rule="fragment_file_version_matches",
                            message=(
                                f"'{row.path}'에 메타데이터 '> 버전'이 없어 "
                                f"fragment의 파일 버전 '{row.file_version}'과 비교할 수 없다"
                            ),
                        ))
                    elif _normalize_version(actual) != _normalize_version(row.file_version):
                        result.add(Violation(
                            file=str(rf.path), line=row.line, file_kind="fragment",
                            rule="fragment_file_version_matches",
                            message=(
                                f"fragment의 '{row.path}' 파일 버전 '{row.file_version}'이 "
                                f"파일 메타데이터 '버전: {actual}'과 일치하지 않는다"
                            ),
                        ))

                # archive 스냅샷 존재 + 메타 일치 검증
                if row.software_version is None:
                    # fragment 메타 '스프린트 버전' 누락 — 다른 체크에서 검출되므로 스킵
                    continue
                if not row.path.startswith("tactical/"):
                    # tactical/ 외 파일은 archive 매핑이 없으므로 스킵 (현재 정책상 발생하지 않아야 함)
                    continue
                rel_under_spec = row.path[len("tactical/"):]
                archive_path = (
                    project_root / "tactical-archive" / row.software_version / rel_under_spec
                )
                if not archive_path.is_file():
                    result.add(Violation(
                        file=str(rf.path), line=row.line, file_kind="fragment",
                        rule="fragment_archive_exists",
                        message=(
                            f"tactical-archive 스냅샷 '{archive_path.relative_to(project_root)}' "
                            f"이 존재하지 않는다 ({row.software_version} 시점의 '{row.path}' 본문 보관 누락)"
                        ),
                    ))
                    continue
                if row.file_version:
                    archived_version = parse_metadata_block(
                        read_text(archive_path)
                    ).get("버전")
                    if archived_version is None:
                        result.add(Violation(
                            file=str(rf.path), line=row.line, file_kind="fragment",
                            rule="fragment_archive_exists",
                            message=(
                                f"archive '{archive_path.relative_to(project_root)}' 에 "
                                f"메타데이터 '> 버전'이 없어 fragment의 파일 버전 "
                                f"'{row.file_version}'과 비교할 수 없다"
                            ),
                        ))
                    elif _normalize_version(archived_version) != _normalize_version(row.file_version):
                        result.add(Violation(
                            file=str(rf.path), line=row.line, file_kind="fragment",
                            rule="fragment_archive_exists",
                            message=(
                                f"archive '{archive_path.relative_to(project_root)}' "
                                f"메타데이터 '버전: {archived_version}'이 fragment의 "
                                f"파일 버전 '{row.file_version}'과 일치하지 않는다"
                            ),
                        ))

    # release(CHANGELOG.md) fold 엔트리 ↔ 최종 tactical-archive 디렉토리 검증.
    # CHANGELOG.md 부재(스프린트 시점)면 release_changelog가 optional이라 no-op.
    release_cfg = cross_refs_cfg.get("release_archive_exists") or {}
    if "release_changelog" in fk and release_cfg:
        version_header_pattern = release_cfg.get(
            "version_header_pattern", r"^##\s+v?(\d+\.\d+\.\d+)\b"
        )
        for rf in expand_file_kind(
            "release_changelog", fk["release_changelog"], project_root
        ):
            if not rf.exists:
                continue
            content = read_text(rf.path)
            for version, line_no in extract_release_versions(
                content, version_header_pattern
            ):
                # tactical-archive/v{X.Y.Z}/ 또는 v 접두사 없는 {X.Y.Z}/ 둘 다 인정.
                # (작성 가이드가 v 접두사를 강제하지 않으므로 — 메타 원칙)
                candidates = [
                    project_root / "tactical-archive" / f"v{version}",
                    project_root / "tactical-archive" / version,
                ]
                if not any(d.is_dir() for d in candidates):
                    result.add(Violation(
                        file=str(rf.path), line=line_no, file_kind="release_changelog",
                        rule="release_archive_exists",
                        message=(
                            f"릴리스 엔트리 'v{version}'에 대응하는 tactical-archive 스냅샷 "
                            f"'tactical-archive/v{version}/'이 존재하지 않는다 "
                            f"(릴리스 fold 시 최종 상세설계서 스냅샷 누락)"
                        ),
                    ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="cross-reference 정합성 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
