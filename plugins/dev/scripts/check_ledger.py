#!/usr/bin/env python3
"""(9) 검증 원장 백스톱 체크.

검증 원장(`tactical/verification-ledger.md`)의 결정론 불변식 L1~L4를 검사한다.
이 체크는 릴리스(태그) 게이트다 — 미결/보류가 명시적 해소 증거 없이 조용히
"됨"으로 승격되는 걸 구조로 차단한다 (docs/요구사항-집행-수정안.md §4 백스톱·§5).

원장 스키마 (v2 — 면별 다중 단정, 코더·verifier 2칸):
- AC블록 = `## AC-<n>: ...` (level 2 헤더)
- 각 AC블록에 면별 다중 단정 테이블 `| 면 | 단정 | 채널 | 코더 | verifier | 해소 증거 |`
- 면 ∈ {UI/UX, 로직, 데이터}, 각 면 ≥1행 (해당없으면 단정칸 `N-A + 사유`)
- 단정 = `T<n>` + 절차→관측→기대(관찰 가능). 채널 ∈ {1 정적구조, 2 로직단위, 3 계약API,
  4 정적스크린샷, 5 실기기}(싼→비싼 사다리)
- 코더 = 코더 달성 상태 ∈ {PASS, FAIL, -, N/A}. verifier = verifier 확인 상태 ∈
  {PASS, FAIL, 보류, 미결, -}. 파생 판정(코더=-/FAIL→미달성 / 코더=PASS,verifier=-→구현됨·미검증 /
  verifier=PASS→done)은 칸이 아니라 두 칸의 조합이다
- 경계 계약 타입 미확정은 단정/상태 칸에 `계약 미결` 마커
- 하위호환: 옛 5컬럼 스키마 `| 면 | 검증 항목 | 채널 | 상태 | 해소 증거 |`(단일 상태)도
  파싱한다 — 옛 `상태` 칸을 verifier 칸으로 보고 코더 칸은 생략(컬럼 라벨 감지 + 위치 폴백)

불변식:
- L1 verification_ledger_facets_complete : 각 AC블록에 UI/UX·로직·데이터 3면 행 전부 존재(≥1행).
  N-A면 행은 단정 칸에 `N-A` 뒤 사유 텍스트가 있어야.
- L2 verification_ledger_pass_evidence   : 코더 또는 verifier 칸이 PASS인 행은 해소 증거 칸
  non-empty (빈칸/`-`이면 위반).
- L3 contract_unresolved_zero            : 원장 및 tactical/ 어디에도 `계약 미결` 마커가 남아 있지 않음.
- L4 verification_ledger_carryforward    : 직전 버전 archive 원장에서 미종결이던 단정
  (verifier ∈ {보류, 미결, -} 또는 코더 = FAIL)이 현재 원장에 여전히 존재 (drop 0).
  단정 단위(T<n>) 판정; 옛 스키마는 (AC, 면) 단위로 폴백.

종결 게이트 (L5~L7) — `--boundary {implement|verify|release}`에서만 발화한다.
boundary 미지정(writer self-verify·현행 run_all 경로) = L1~L4만(무손상). 직전 스프린트
승계 블록(상단 메타 `승계: <버전>`)은 L5/L6 면제(부채는 L4·L7이 관리):
- L5 verification_ledger_coder_closure    : 코더 소유 채널(1~3, 기기불필요)·비N-A 단정의
  코더 칸이 미착수(`-`)·보류면 위반. 구현 안 한 항목이 구현 경계를 통과하는 걸 차단(implement 이상).
  채널4(정적스크린샷)·5(실기기)는 verifier가 닫는다(L6).
- L6 verification_ledger_verifier_closure : 비N-A 단정의 verifier 칸이 PASS(+증거)도
  보류도 아니면(=`-`·미결·FAIL) 위반. 미검증이 release로 통과하는 걸 차단(verify 이상).
- L7 verification_ledger_hold_approved_debt: verifier=보류 단정은 채널5 + 항목별 승인 토큰
  (`승인: …`)이어야 통과. 포괄 면제 통로를 막는다(verify 이상).

원장 부재 시(스프린트 초기) 전체 no-op PASS. --domain 로컬 스코프에선 원장이 전역이므로
run_all이 이 체크를 skip한다 (GLOBAL_ONLY).
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
    iter_content_lines,
    load_catalog,
    parse_sections,
    read_text,
)


CHECK_NAME = "ledger"

# --domain 로컬 스코프에서 run_all이 skip하도록 하는 마커.
# 원장은 전역 산출물이라 도메인별 위반으로 나눌 수 없다.
GLOBAL_ONLY = True

# run_all이 --boundary를 전달하도록 하는 마커(종결 게이트 L5~L7 발화 제어).
GATE_AWARE = True

# 종결 게이트가 발화하는 경계(싼→비싼 순). boundary가 이 목록의 해당 지점 이상이면 발화.
_BOUNDARY_ORDER = ["design", "tactical", "implement", "verify", "release"]


def _gate_active(boundary: str | None, since: str) -> bool:
    """boundary가 since 경계 이상이면 True(종결 게이트 발화)."""
    if not boundary:
        return False
    try:
        return _BOUNDARY_ORDER.index(boundary) >= _BOUNDARY_ORDER.index(since)
    except ValueError:
        return False

# 카탈로그 미제공 시 사용하는 기본값 (메타 원칙: 검증↔작성 1:1 정렬 — 원장 writer
# 템플릿과 같은 라벨을 SoT로 삼는다).
_DEFAULTS = {
    "ledger_path": "tactical/verification-ledger.md",
    "archive_dir": "tactical-archive",
    "tactical_dir": "tactical",
    "facets": ["UI/UX", "로직", "데이터"],
    "pass_status": "PASS",
    "na_status": "N-A",
    "coder_fail_status": "FAIL",
    # verifier 칸이 이 값(또는 빈칸/`-`)이면 미종결 단정 → 누적 승계 대상.
    # 코더=FAIL도 미종결(coder_fail_status).
    "carryforward_statuses": ["보류", "미결", "-"],
    "contract_unresolved_marker": "계약 미결",
    "empty_evidence_markers": ["", "-"],
    # 종결 게이트(L5~L7). 코더 소유 = 구현시점 테스트로 닫는 기기불필요 채널(1·2·3).
    # 채널4(정적스크린샷)는 렌더 필요라 verifier(L6)가 닫는다.
    "channels_coder_owned": ["1", "2", "3"],
    "channel_device": "5",
    "coder_nonclosure_statuses": ["-", "보류"],
    "verifier_nonclosure_statuses": ["-", "미결", "FAIL"],
    "hold_status": "보류",
    "hold_approval_pattern": r"승인:\s*\S+",
    "carryforward_meta_field": "승계",
    "carryforward_new_value": "신규",
}

_CHANNEL_NUM_RE = re.compile(r"(\d)")


def _channel_num(cell: str) -> str | None:
    """채널 칸 앞머리 숫자(예 '3 계약API' → '3')."""
    m = _CHANNEL_NUM_RE.search(cell)
    return m.group(1) if m else None

_AC_ID_RE = re.compile(r"^(AC-\d+)\b")
_ASSERT_ID_RE = re.compile(r"\bT\d+\b")
_VERSION_DIR_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
_TABLE_DIVIDER = re.compile(r"^[:|\-\s]+$")


# ---------------------------------------------------------------------------
# 표 파싱 유틸 (check_cross_refs와 동형 — 모듈 독립 유지를 위해 로컬 정의)
# ---------------------------------------------------------------------------

def _split_md_row(line: str) -> list[str]:
    """마크다운 표 행을 셀 리스트로 분해. `| a | b |` → [a, b]."""
    return [c.strip() for c in line.split("|")[1:-1]]


def _is_divider_row(cells: list[str]) -> bool:
    return all(_TABLE_DIVIDER.match(c) for c in cells if c) or all(
        re.fullmatch(r":?-+:?", c) for c in cells
    )


def _col(cells: list[str], name: str, default: int) -> int:
    try:
        return cells.index(name)
    except ValueError:
        return default


def _col_of(cells: list[str], names: list[str], default: int) -> int:
    """헤더 라벨 후보 목록 중 첫 매칭 컬럼 인덱스. 없으면 위치 폴백 default."""
    for n in names:
        if n in cells:
            return cells.index(n)
    return default


def _col_opt(cells: list[str], names: list[str]) -> int | None:
    """옵션 컬럼(옛 스키마엔 없음). 매칭 없으면 None."""
    for n in names:
        if n in cells:
            return cells.index(n)
    return None


def _cell(cells: list[str], idx: int | None) -> str:
    if idx is None:
        return ""
    return cells[idx].strip() if 0 <= idx < len(cells) else ""


def _assertion_id(item: str) -> str | None:
    """단정 칸에서 단정 ID `T<n>`을 추출한다(옛 스키마엔 없어 None)."""
    m = _ASSERT_ID_RE.search(item)
    return m.group(0) if m else None


def _na_reason_missing(item: str, na_status: str) -> bool:
    """단정 칸이 `N-A`로 시작하지만 뒤에 사유 텍스트가 없으면 True(빈 N-A)."""
    s = item.strip()
    if not s.startswith(na_status):
        return False
    return not s[len(na_status):].strip(" —-:·,")


# ---------------------------------------------------------------------------
# 원장 파싱
# ---------------------------------------------------------------------------

@dataclass
class LedgerRow:
    facet: str
    item: str        # 단정 (v2) 또는 검증 항목 (옛 스키마)
    channel: str
    coder: str       # 코더 달성 상태 (옛 스키마엔 없음 → "")
    verifier: str    # verifier 확인 상태 (옛 스키마의 단일 `상태` 칸)
    evidence: str
    line: int


@dataclass
class ACBlock:
    ac_id: str
    title: str
    line: int
    rows: list[LedgerRow]
    carryforward: bool = False  # 직전 스프린트 이월 블록(승계≠신규) — 종결(L5/L6) 면제


def _parse_rows(block_lines: list[str], base_line: int) -> list[LedgerRow]:
    """AC블록 본문 라인들에서 면별 단정 표 데이터 행을 추출한다.

    v2 헤더 `| 면 | 단정 | 채널 | 코더 | verifier | 해소 증거 |`로 컬럼 인덱스를 잡는다.
    옛 5컬럼 `| 면 | 검증 항목 | 채널 | 상태 | 해소 증거 |`도 감지해 파싱한다(하위호환):
    `코더` 컬럼이 없으면 옛 스키마로 보고 단일 `상태` 칸을 verifier 칸으로 매핑, 코더는 "".
    헤더 라벨이 없으면 위치 폴백을 쓴다.
    """
    rows: list[LedgerRow] = []
    idx_map: dict[str, int | None] | None = None
    for j, raw in enumerate(block_lines):
        line_no = base_line + j
        if not raw.lstrip().startswith("|"):
            idx_map = None
            continue
        cells = _split_md_row(raw)
        if not cells:
            continue
        if idx_map is None:
            # 헤더 감지 — '면' + (verifier|상태) 컬럼이 있으면 단정 표로 인식
            if "면" in cells and ("verifier" in cells or "상태" in cells):
                is_v2 = "코더" in cells
                if is_v2:
                    idx_map = {
                        "facet": _col_of(cells, ["면"], 0),
                        "item": _col_of(cells, ["단정", "검증 항목"], 1),
                        "channel": _col_of(cells, ["채널"], 2),
                        "coder": _col_opt(cells, ["코더"]),
                        "verifier": _col_of(cells, ["verifier", "상태"], 4),
                        "evidence": _col_of(cells, ["해소 증거"], 5),
                    }
                else:
                    # 옛 5컬럼: 단일 `상태` 칸 = verifier, 코더 칸 없음
                    idx_map = {
                        "facet": _col_of(cells, ["면"], 0),
                        "item": _col_of(cells, ["검증 항목", "단정"], 1),
                        "channel": _col_of(cells, ["채널"], 2),
                        "coder": None,
                        "verifier": _col_of(cells, ["상태", "verifier"], 3),
                        "evidence": _col_of(cells, ["해소 증거"], 4),
                    }
            continue
        if _is_divider_row(cells):
            continue
        rows.append(LedgerRow(
            facet=_cell(cells, idx_map["facet"]),
            item=_cell(cells, idx_map["item"]),
            channel=_cell(cells, idx_map["channel"]),
            coder=_cell(cells, idx_map["coder"]),
            verifier=_cell(cells, idx_map["verifier"]),
            evidence=_cell(cells, idx_map["evidence"]),
            line=line_no,
        ))
    return rows


def _block_is_carryforward(
    block_lines: list[str], cf_field: str = "승계", cf_new: str = "신규"
) -> bool:
    """AC블록 상단 `> ... | 승계: <값> | ...` 메타에서 이월 여부를 판정한다.

    값이 cf_new(신규)가 아니고 버전 형태(예: v0.1.0)면 직전 스프린트 이월 블록.
    표(`|`)가 시작되면 메타 종료.
    """
    for raw in block_lines:
        stripped = raw.lstrip()
        if stripped.startswith("|"):
            break
        if not stripped.startswith(">"):
            continue
        for seg in raw.split("|"):
            m = re.search(rf"{re.escape(cf_field)}\s*:\s*(\S+)", seg)
            if m:
                val = m.group(1).strip("`*")
                return cf_new not in val and re.search(r"\d+\.\d+", val) is not None
    return False


def parse_ledger(
    content: str, cf_field: str = "승계", cf_new: str = "신규"
) -> list[ACBlock]:
    """원장 본문에서 AC블록(`## AC-<n>: ...`)과 각 블록의 3면 행을 파싱한다."""
    sections = parse_sections(content)
    lines = content.splitlines()
    blocks: list[ACBlock] = []
    for sec in sections:
        if sec.level != 2:
            continue
        m = _AC_ID_RE.match(sec.title)
        if not m:
            continue
        # 블록 경계 = 다음 level<=2 헤더 직전 (전역 순서상 가장 가까운 것)
        end = len(lines)
        for s2 in sections:
            if s2.line > sec.line and s2.level <= 2:
                end = s2.line - 1
                break
        block_lines = lines[sec.line:end]  # sec.line(1-based) = 헤더 다음 라인의 0-based 인덱스
        rows = _parse_rows(block_lines, base_line=sec.line + 1)
        cf = _block_is_carryforward(block_lines, cf_field, cf_new)
        blocks.append(ACBlock(
            ac_id=m.group(1), title=sec.title, line=sec.line, rows=rows, carryforward=cf))
    return blocks


# ---------------------------------------------------------------------------
# archive 최신 버전 판정 (check_cross_refs.release_archive_exists와 동일 규약:
# v 접두사 유무 무관, 순수 semver 디렉토리만 대상)
# ---------------------------------------------------------------------------

def latest_archive_version_dir(project_root: Path, archive_dir: str) -> tuple[str, Path] | None:
    archive = project_root / archive_dir
    if not archive.is_dir():
        return None
    best: tuple[tuple[int, int, int], str, Path] | None = None
    for d in archive.iterdir():
        if not d.is_dir():
            continue
        m = _VERSION_DIR_RE.match(d.name)
        if not m:
            continue  # 스프린트 버전 키(예 1.4.0-add-discount)는 대상 아님
        key = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if best is None or key > best[0]:
            best = (key, d.name, d)
    if best is None:
        return None
    return best[1], best[2]


# ---------------------------------------------------------------------------
# 체크 실행
# ---------------------------------------------------------------------------

def run(catalog: dict, project_root: Path, boundary: str | None = None) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    cfg = {**_DEFAULTS, **(catalog.get("verification_ledger") or {})}

    ledger_rel = cfg["ledger_path"]
    ledger_path = project_root / ledger_rel

    # 원장 부재(스프린트 초기) → 전체 no-op PASS
    if not ledger_path.is_file():
        return result.finalize()

    facets = list(cfg["facets"])
    pass_status = cfg["pass_status"]
    na_status = cfg["na_status"]
    coder_fail = cfg["coder_fail_status"]
    carryforward = set(cfg["carryforward_statuses"])
    marker = cfg["contract_unresolved_marker"]
    empty_evidence = set(cfg["empty_evidence_markers"])
    cf_field = cfg.get("carryforward_meta_field", "승계")
    cf_new = cfg.get("carryforward_new_value", "신규")

    content = read_text(ledger_path)
    blocks = parse_ledger(content, cf_field, cf_new)

    # --- L1: 3면 완비(각 면 ≥1행) + N-A 사유 ---
    for block in blocks:
        present = {row.facet for row in block.rows}
        for facet in facets:
            if facet not in present:
                result.add(Violation(
                    file=str(ledger_path), line=block.line, file_kind="verification_ledger",
                    rule="verification_ledger_facets_complete",
                    message=f"{block.ac_id} 블록에 '{facet}' 면 행이 없다 (3면 완비 위반)",
                ))
        for row in block.rows:
            # N-A면 단정 칸이 `N-A` 뒤에 사유 텍스트를 가져야 (빈 N-A 금지)
            if _na_reason_missing(row.item, na_status):
                result.add(Violation(
                    file=str(ledger_path), line=row.line, file_kind="verification_ledger",
                    rule="verification_ledger_facets_complete",
                    message=(
                        f"{block.ac_id} '{row.facet}' 면이 N-A인데 단정 칸에 "
                        f"사유 텍스트가 없다"
                    ),
                ))

    # --- L2: PASS 무결성 (코더 또는 verifier 칸=PASS면 해소 증거 non-empty) ---
    for block in blocks:
        for row in block.rows:
            if (row.coder == pass_status or row.verifier == pass_status) \
                    and row.evidence in empty_evidence:
                which = "코더" if row.coder == pass_status else "verifier"
                result.add(Violation(
                    file=str(ledger_path), line=row.line, file_kind="verification_ledger",
                    rule="verification_ledger_pass_evidence",
                    message=(
                        f"{block.ac_id} '{row.facet}' 면 단정의 {which} 칸이 PASS인데 "
                        f"해소 증거 칸이 비어 있다 (빈칸/`-`)"
                    ),
                ))

    # --- L3: 계약 미결 0 (원장 + tactical/ 트리) ---
    tactical_dir = project_root / cfg["tactical_dir"]
    scanned: set[Path] = set()
    md_files: list[Path] = []
    if tactical_dir.is_dir():
        md_files.extend(sorted(tactical_dir.rglob("*.md")))
    if ledger_path not in md_files:
        md_files.append(ledger_path)
    for md in md_files:
        if md in scanned or not md.is_file():
            continue
        scanned.add(md)
        is_ledger = md == ledger_path
        for line_no, raw in iter_content_lines(read_text(md)):
            if marker in raw:
                result.add(Violation(
                    file=str(md), line=line_no,
                    file_kind="verification_ledger" if is_ledger else None,
                    rule="contract_unresolved_zero",
                    message=(
                        f"`{marker}` 마커가 남아 있다 — 경계 계약 타입이 미확정 상태로 "
                        f"릴리스될 수 없다 (확정 또는 escalate 필요)"
                    ),
                ))

    # --- L4: 누적 승계 (직전 archive 원장의 보류/미결 행 drop 0) ---
    latest = latest_archive_version_dir(project_root, cfg["archive_dir"])
    if latest is not None:
        version_name, version_dir = latest
        archive_ledger = version_dir / ledger_rel[len(cfg["tactical_dir"]) + 1:] \
            if ledger_rel.startswith(cfg["tactical_dir"] + "/") else version_dir / Path(ledger_rel).name
        if archive_ledger.is_file():
            prev_blocks = parse_ledger(read_text(archive_ledger))
            # 현재 원장의 존재 키 집합. 면 단위(폴백)와 단정 단위(T<n>)를 모두 등록한다 —
            # 옛 스키마(T id 없음) prev 행은 면 단위로, v2 prev 행은 단정 단위로 매칭.
            current_keys: set[tuple] = set()
            for b in blocks:
                for r in b.rows:
                    current_keys.add((b.ac_id, r.facet))
                    tid = _assertion_id(r.item)
                    if tid:
                        current_keys.add((b.ac_id, r.facet, tid))
            for pb in prev_blocks:
                for pr in pb.rows:
                    # 미종결 = verifier ∈ carryforward({보류,미결,-}) 또는 코더 = FAIL.
                    # N-A 단정은 승계 대상 아님.
                    if pr.item.strip().startswith(na_status):
                        continue
                    v = pr.verifier.strip() or "-"
                    unresolved = v in carryforward or pr.coder.strip() == coder_fail
                    if not unresolved:
                        continue
                    tid = _assertion_id(pr.item)
                    key = (pb.ac_id, pr.facet, tid) if tid else (pb.ac_id, pr.facet)
                    if key not in current_keys:
                        label = f"{pb.ac_id} '{pr.facet}' 면" + (f" 단정 {tid}" if tid else " 행")
                        reason = f"코더 FAIL" if pr.coder.strip() == coder_fail else f"verifier '{v}'"
                        result.add(Violation(
                            file=str(ledger_path), line=None, file_kind="verification_ledger",
                            rule="verification_ledger_carryforward",
                            message=(
                                f"직전 버전({version_name}) 원장에서 미종결({reason})이던 "
                                f"{label}이 현재 원장에서 누락됐다 "
                                f"(승계 drop — 미종결 단정은 다음 스프린트로 승계돼야 한다)"
                            ),
                        ))

    # --- 종결 게이트 (L5~L7) — --boundary가 해당 경계 이상일 때만 발화 ---
    coder_owned = set(cfg.get("channels_coder_owned") or [])
    device_ch = str(cfg.get("channel_device") or "5")
    coder_nonclosure = set(cfg.get("coder_nonclosure_statuses") or [])
    verifier_nonclosure = set(cfg.get("verifier_nonclosure_statuses") or [])
    hold_status = cfg.get("hold_status") or "보류"
    approval_re = re.compile(cfg.get("hold_approval_pattern") or r"승인:\s*\S+")

    def _is_na(item: str) -> bool:
        return item.strip().startswith(na_status)

    gate_impl = _gate_active(boundary, "implement")
    gate_verify = _gate_active(boundary, "verify")

    for block in blocks:
        for row in block.rows:
            if _is_na(row.item):
                continue
            ch = _channel_num(row.channel)
            coder = row.coder.strip()
            verifier = row.verifier.strip() or "-"

            # L5 코더 종결 (implement 이상, 승계 블록 면제, 코더 소유 채널만)
            if gate_impl and not block.carryforward \
                    and ch in coder_owned and coder in coder_nonclosure:
                result.add(Violation(
                    file=str(ledger_path), line=row.line, file_kind="verification_ledger",
                    rule="verification_ledger_coder_closure",
                    message=(
                        f"{block.ac_id} '{row.facet}' 면 단정의 코더 칸이 '{coder or '-'}'(미종결)이다 "
                        f"— 채널 {row.channel}은 코더가 구현시점에 종결(PASS/FAIL/N/A)해야 한다. "
                        "미착수·보류로 구현 경계를 통과할 수 없다(구현 안 한 항목 차단)."
                    ),
                ))

            # L6 verifier 종결 (verify 이상, 승계 블록 면제) — PASS 또는 보류(정당성은 L7)
            if gate_verify and not block.carryforward \
                    and verifier != pass_status and verifier != hold_status:
                if verifier in verifier_nonclosure:
                    result.add(Violation(
                        file=str(ledger_path), line=row.line, file_kind="verification_ledger",
                        rule="verification_ledger_verifier_closure",
                        message=(
                            f"{block.ac_id} '{row.facet}' 면 단정의 verifier 칸이 '{verifier}'(미종결)이다 "
                            "— 검증 경계를 넘기려면 verifier=PASS(+증거) 또는 승인된 채널5 보류여야 한다. "
                            "미검증·미결·FAIL은 release를 차단한다."
                        ),
                    ))

            # L7 보류 = 승인된 부채 (verify 이상, 승계 블록 포함 전량)
            if gate_verify and verifier == hold_status:
                problems = []
                if ch != device_ch:
                    problems.append(f"채널이 {row.channel}(실기기 5 아님 — 채널1~4로 답할 것을 보류로 미룰 수 없음)")
                if not approval_re.search(row.evidence):
                    problems.append("해소 증거 칸에 항목별 승인 토큰(`승인: <개발자>·<날짜>·<사유>`) 없음")
                if problems:
                    result.add(Violation(
                        file=str(ledger_path), line=row.line, file_kind="verification_ledger",
                        rule="verification_ledger_hold_approved_debt",
                        message=(
                            f"{block.ac_id} '{row.facet}' 면 단정이 보류인데 정당한 부채가 아니다: "
                            + " / ".join(problems)
                            + ". 포괄 승인이 아니라 항목별 승인 토큰이 있어야 릴리스가 진행된다."
                        ),
                    ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="검증 원장 백스톱 체크 (L1~L7)")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    parser.add_argument(
        "--boundary",
        type=str,
        default=None,
        choices=["design", "tactical", "implement", "verify", "release"],
        help="경계 종결 게이트 발화(없으면 L1~L4만). implement→L5, verify→L5~L7, release→전량",
    )
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root, boundary=args.boundary)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
