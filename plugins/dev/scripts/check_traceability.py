#!/usr/bin/env python3
"""(12) 경계 커버리지 체크 — 상류 전항목이 하류 목록에 대응됐는가.

라이브 워크플로의 세 산출물을 ID로 조인해 "상류 항목이 하나도 안 빠지고
하류 목록이 됐는가"를 결정론으로 강제한다. 기존 check_cross_refs가 "하류가
참조한 ID가 상류에 존재하나"(dangling 방지, 방향 반대)만 보던 사각을 메운다.

체인
----
  R-n (요구사항, design/requirements.md)
    → 완료 기준 표 (design/design.md `## 완료 기준`, AC·요구사항 칼럼)
      → AC-n 블록 (원장 tactical/verification-ledger.md `## AC-n`)

불변식
------
- COV-1  요구사항 커버: 상태 ∈ {active,승계}인 모든 R-n이 완료 기준 표 요구사항 칸에서 ≥1회 참조.
- COV-1b 요구사항 존재: 완료 기준 표가 참조한 R-n이 requirements.md에 실제 존재(dangling).
- COV-2  완료기준 커버: 완료 기준 표의 모든 AC-n이 원장에 `## AC-n` 블록으로 존재.
- COV-2b AC 역추적: 원장의 모든 `## AC-n`이 완료 기준 표에 존재(원장이 완료기준 없는 AC 발명 금지).
         직전 스프린트 승계 블록(승계≠신규)은 타이밍 스큐 방지로 면제.

채택 스위치 / 하위호환
--------------------
requirements.md **부재** → 전체 no-op PASS(초기·레거시 스프린트). design.md **부재**
→ no-op(check_design가 소유). requirements.md 존재 = 팀 채택 = 완료 기준 표에 AC·요구사항
칼럼 필수(없으면 위반). 원장 부재(상세설계 전) → COV-2/2b no-op.

라이브 규율(활성+승계만) 덕에 릴리스된 요구사항은 라이브 집합에 없어 change-scoped
스프린트 오탐 0. R-n itemization·완료기준이 요구사항을 진짜 담는가는 ⓪ 사람 게이트(의미).
여기선 ID 존재·집합 대응만 본다. 원장은 전역 산출물이라 GLOBAL_ONLY(--domain skip).

설정: 카탈로그 `traceability`에서 관리(경로·정규식·상태·칼럼 라벨).
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
    parse_sections,
    read_text,
)

CHECK_NAME = "traceability"

# 원장은 전역 산출물이라 --domain 로컬 스코프에선 skip(check_ledger와 동일 이유).
GLOBAL_ONLY = True

_DEFAULTS = {
    "requirements_path": "design/requirements.md",
    "design_path": "design/design.md",
    "ledger_path": "tactical/verification-ledger.md",
    "requirement_id_pattern": r"\bR-\d+\b",
    "ac_id_pattern": r"\bAC-\d+\b",
    "requirement_status_field": "상태",
    "requirement_active_statuses": ["active", "승계"],
    "acceptance_section": "완료 기준",
    "acceptance_ac_columns": ["AC"],
    "acceptance_req_columns": ["요구사항"],
    "ledger_carryforward_meta_field": "승계",
    "ledger_carryforward_new_value": "신규",
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_TABLE_DIVIDER = re.compile(r"^[:|\-\s]+$")


def _cfg(catalog: dict) -> dict:
    c = dict(_DEFAULTS)
    c.update(catalog.get("traceability") or {})
    return c


def _split_md_row(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")[1:-1]]


def _is_divider_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-+:?", c or "-") for c in cells)


def _col_of(cells: list[str], names: list[str]) -> int | None:
    for n in names:
        if n in cells:
            return cells.index(n)
    return None


# ---------------------------------------------------------------------------
# 요구사항 파싱: `### R-n` 헤더 + 그 아래 `> 상태: <값>` 메타
# ---------------------------------------------------------------------------

def _collect_active_requirements(
    content: str, id_pat: str, status_field: str, active: list[str]
) -> tuple[set[str], set[str]]:
    """(활성 R-n 집합, 전체 R-n 집합)을 반환한다.

    상태 메타(`> 상태: X`)가 없으면 활성으로 본다(기본값). 상태가 active_statuses에
    들지 않으면(예 released) 비활성 → 커버리지 강제 대상에서 제외.
    """
    id_re = re.compile(id_pat)
    status_re = re.compile(rf"^\s*>\s*{re.escape(status_field)}\s*:\s*(.+?)\s*$")
    active_set: set[str] = set()
    all_set: set[str] = set()
    in_fence = False
    current: str | None = None
    current_status: str | None = None

    def _flush():
        if current is not None:
            all_set.add(current)
            st = (current_status or "").strip()
            if not st or any(a in st for a in active):
                active_set.add(current)

    for raw in content.splitlines():
        if re.match(r"^\s*```", raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        h = _HEADING_RE.match(raw)
        if h:
            m = id_re.search(h.group(2))
            if m:
                _flush()
                current = m.group(0)
                current_status = None
                continue
            # 다른 헤더 → 현재 R 블록 종료
            _flush()
            current = None
            current_status = None
            continue
        if current is not None and current_status is None:
            sm = status_re.match(raw)
            if sm:
                current_status = sm.group(1)
    _flush()
    return active_set, all_set


# ---------------------------------------------------------------------------
# design.md 완료 기준 표 파싱
# ---------------------------------------------------------------------------

def _acceptance_body(content: str, section: str) -> list[str]:
    lines = content.splitlines()
    out: list[str] = []
    capturing = False
    for raw in lines:
        m = _HEADING_RE.match(raw)
        if m:
            lvl, t = len(m.group(1)), m.group(2).strip()
            if capturing and lvl <= 2:
                break
            if lvl == 2 and t == section:
                capturing = True
                continue
        if capturing:
            out.append(raw)
    return out


def _parse_acceptance_table(
    body: list[str], ac_cols: list[str], req_cols: list[str]
) -> tuple[bool, int | None, int | None, list[tuple[list[str], list[str], int]]]:
    """완료 기준 표를 파싱한다.

    반환: (표 존재, AC 칼럼 idx, 요구사항 칼럼 idx, [(AC토큰들, R토큰들, 상대라인)…]).
    AC/요구사항 칼럼 인덱스는 헤더 라벨로 잡는다(없으면 None → 채택 위반 판정용).
    """
    ac_re = re.compile(_DEFAULTS["ac_id_pattern"])
    req_re = re.compile(_DEFAULTS["requirement_id_pattern"])
    have_table = False
    ac_idx: int | None = None
    req_idx: int | None = None
    rows: list[tuple[list[str], list[str], int]] = []
    in_header = False
    for j, raw in enumerate(body):
        if not raw.lstrip().startswith("|"):
            in_header = False
            continue
        cells = _split_md_row(raw)
        if not cells:
            continue
        if not in_header and (_col_of(cells, ac_cols) is not None
                              or "완료 기준" in cells or "요구사항" in cells):
            # 헤더 행
            have_table = True
            ac_idx = _col_of(cells, ac_cols)
            req_idx = _col_of(cells, req_cols)
            in_header = True
            continue
        if not in_header:
            continue
        if _is_divider_row(cells):
            continue
        ac_cell = cells[ac_idx] if ac_idx is not None and ac_idx < len(cells) else ""
        req_cell = cells[req_idx] if req_idx is not None and req_idx < len(cells) else ""
        ac_tokens = ac_re.findall(ac_cell)
        req_tokens = req_re.findall(req_cell)
        if ac_tokens or req_tokens or any(cells):
            rows.append((ac_tokens, req_tokens, j))
    return have_table, ac_idx, req_idx, rows


# ---------------------------------------------------------------------------
# 원장 AC 블록 파싱 (id, is_carryforward, line)
# ---------------------------------------------------------------------------

def _ledger_ac_blocks(
    content: str, ac_pat: str, cf_field: str, cf_new: str
) -> list[tuple[str, bool, int]]:
    ac_id_re = re.compile(r"^(" + ac_pat.strip(r"\b") + r")\b")
    ac_search = re.compile(ac_pat)
    blocks: list[tuple[str, bool, int]] = []
    lines = content.splitlines()
    in_fence = False
    i = 0
    while i < len(lines):
        raw = lines[i]
        if re.match(r"^\s*```", raw):
            in_fence = not in_fence
            i += 1
            continue
        if not in_fence:
            h = _HEADING_RE.match(raw)
            if h and h.group(1) == "##":
                m = ac_search.search(h.group(2))
                if m:
                    ac_id = m.group(0)
                    # 블록 상단 메타(`>` 인용)에서 승계 필드 값 탐색
                    is_cf = False
                    k = i + 1
                    while k < len(lines):
                        nxt = lines[k]
                        hh = _HEADING_RE.match(nxt)
                        if hh and len(hh.group(1)) <= 2:
                            break
                        if nxt.lstrip().startswith(">"):
                            for seg in nxt.split("|"):
                                sm = re.search(
                                    rf"{re.escape(cf_field)}\s*:\s*(\S+)", seg)
                                if sm:
                                    val = sm.group(1).strip("`*")
                                    is_cf = cf_new not in val and re.search(
                                        r"\d+\.\d+", val) is not None
                                    break
                        # 표 시작하면 메타 종료
                        if nxt.lstrip().startswith("|"):
                            break
                        k += 1
                    blocks.append((ac_id, is_cf, i + 1))
        i += 1
    return blocks


# ---------------------------------------------------------------------------
# 체크 실행
# ---------------------------------------------------------------------------

def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    cfg = _cfg(catalog)

    req_path = project_root / cfg["requirements_path"]
    design_path = project_root / cfg["design_path"]
    ledger_path = project_root / cfg["ledger_path"]

    # 채택 스위치: requirements.md 부재 → 전체 no-op(하위호환).
    if not req_path.is_file():
        return result.finalize()
    # design.md 부재 → check_design가 소유(중복 노이즈 회피).
    if not design_path.is_file():
        return result.finalize()

    req_content = read_text(req_path)
    design_content = read_text(design_path)

    active_reqs, all_reqs = _collect_active_requirements(
        req_content,
        cfg["requirement_id_pattern"],
        cfg["requirement_status_field"],
        cfg["requirement_active_statuses"],
    )

    body = _acceptance_body(design_content, cfg["acceptance_section"])
    have_table, ac_idx, req_idx, rows = _parse_acceptance_table(
        body, cfg["acceptance_ac_columns"], cfg["acceptance_req_columns"]
    )

    # 채택했는데 완료 기준 표/칼럼 부재 → 위반(부드러운 no-op 아님).
    if not have_table:
        result.add(Violation(
            file=str(design_path), file_kind="design",
            rule="traceability_adoption",
            message=(
                f"requirements.md를 채택했으나 design.md '## {cfg['acceptance_section']}'에 "
                "표가 없다 — 완료 기준을 AC·요구사항 칼럼 표로 작성해야 추적이 성립한다."
            ),
        ))
        return result.finalize()
    if ac_idx is None:
        result.add(Violation(
            file=str(design_path), file_kind="design", rule="traceability_adoption",
            message="완료 기준 표에 'AC' 칼럼이 없다 (requirements.md 채택 시 필수 — AC-n 부여).",
        ))
    if req_idx is None:
        result.add(Violation(
            file=str(design_path), file_kind="design", rule="traceability_adoption",
            message="완료 기준 표에 '요구사항' 칼럼이 없다 (requirements.md 채택 시 필수 — R-n 참조).",
        ))

    design_reqs: set[str] = set()
    design_acs: list[str] = []
    for ac_tokens, req_tokens, _ln in rows:
        design_reqs.update(req_tokens)
        design_acs.extend(ac_tokens)

    # COV-1: 활성 R-n이 완료 기준에서 참조되나
    if req_idx is not None:
        for rid in sorted(active_reqs):
            if rid not in design_reqs:
                result.add(Violation(
                    file=str(design_path), file_kind="requirements",
                    rule="traceability_requirement_covered",
                    message=(
                        f"요구사항 {rid}에 대응하는 완료 기준이 없다 — 활성 요구사항은 "
                        "design.md 완료 기준 표의 요구사항 칸에서 ≥1회 참조돼야 한다(누락)."
                    ),
                ))
    # COV-1b: 완료 기준이 참조한 R-n이 존재하나
    for rid in sorted(design_reqs):
        if rid not in all_reqs:
            result.add(Violation(
                file=str(design_path), file_kind="design",
                rule="traceability_acceptance_req_exists",
                message=(
                    f"완료 기준이 참조한 요구사항 {rid}이 requirements.md에 없다 "
                    "(dangling 참조 — R-n 오타 또는 요구사항 누락)."
                ),
            ))

    # AC-n 중복(완료 기준 표 = 헤더 아닌 표행이라 check_uniqueness 미적용, 여기서 탐지)
    seen: set[str] = set()
    for ac in design_acs:
        if ac in seen:
            result.add(Violation(
                file=str(design_path), file_kind="design",
                rule="traceability_ac_unique",
                message=f"완료 기준 표에 AC-n '{ac}' 중복 (AC ID는 유일해야 한다).",
            ))
        seen.add(ac)
    design_ac_set = set(design_acs)

    # COV-2 / COV-2b: 원장 존재 시에만
    if ledger_path.is_file():
        ledger_content = read_text(ledger_path)
        blocks = _ledger_ac_blocks(
            ledger_content,
            cfg["ac_id_pattern"],
            cfg["ledger_carryforward_meta_field"],
            cfg["ledger_carryforward_new_value"],
        )
        ledger_ac_ids = {b[0] for b in blocks}
        # COV-2: 완료 기준 AC가 원장 블록으로 존재
        for ac in sorted(design_ac_set):
            if ac not in ledger_ac_ids:
                result.add(Violation(
                    file=str(ledger_path), file_kind="verification_ledger",
                    rule="traceability_acceptance_covered_by_ac",
                    message=(
                        f"완료 기준 {ac}에 대응하는 원장 블록 `## {ac}`가 없다 — "
                        "완료 기준은 원장 AC 블록으로 1:1 분해돼야 한다(누락)."
                    ),
                ))
        # COV-2b: 원장 AC가 완료 기준에 존재(승계 블록 면제)
        for ac_id, is_cf, line in blocks:
            if is_cf:
                continue
            if ac_id not in design_ac_set:
                result.add(Violation(
                    file=str(ledger_path), line=line, file_kind="verification_ledger",
                    rule="traceability_ac_traces_to_acceptance",
                    message=(
                        f"원장 블록 `## {ac_id}`가 design.md 완료 기준에 없다 — "
                        "원장이 완료 기준 없는 AC를 발명했거나 승계 표기가 누락됐다."
                    ),
                ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="경계 커버리지(추적) 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
