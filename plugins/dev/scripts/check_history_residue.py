#!/usr/bin/env python3
"""(11) 이력 잔재 체크 — 라이브 문서에 남은 변경 이력·취소선을 잡는다.

라이브 상세설계 문서는 현재 상태만 담아야 한다(작성 에이전트 공통 계약
`current_state_only`). 이력은 `CHANGELOG.md`·`tactical-archive/<버전>/`가 권위다.
그런데 스프린트가 쌓이면 writer가 이력을 아래 형태로 본문/메타에 눌러앉히는
드리프트가 생긴다 — 이 체크가 그걸 결정론으로 잡아 무한 누적을 끊는다.

잡는 잔재
---------
1. **이력 메타 필드**: `> 수정 이력:` / `> 변경 이력:` 로 시작하는 상단 메타 줄.
   sot-catalog가 요구하는 메타는 `버전`·`최종 수정`뿐이고, 이력 필드는 스키마
   밖 발명이라 check_template이 잡지 못한다(여분 필드 미검열). 여기서 잡는다.
2. **취소선**: `~~…~~` (마크다운 strikethrough). 스펙 문서에서 취소선은 "지웠지만
   흔적을 남김" = 이력이다. 현재 상태 문서에 취소선의 정당한 용도는 없다.
3. **델타/점검 블록·서사**: 리터럴 서명(`### 이전 델타`·`적용 범위 전환`·`스탠스 종료`·
   `시스템 영향 점검`·`델타 승계`)과 **버전-인접 "델타"·"점검"**(`\d+\.\d+\S*\s*(델타|점검)`).
   후자가 `**0.18.0 델타**` 블록, `> 출처:`/`> 입력:`/`> 도메인:` 메타의 "스프린트 0.X 델타"
   서사, 그리고 `## 결정 필요`에 쌓인 "스프린트 0.X 점검 … escalate 대상 0건" 감사 이력을
   함께 잡는다. 메타는 현행 근거만, `## 결정 필요`는 현재 열린 결정만 담아야 한다.

정상 처리
---------
위반은 임의 삭제가 아니라 **최종 상태로 덮어쓰기**로 해소한다 — 취소선은 최종
서술만 남기고, 이력 메타 필드는 제거하며, 델타 블록은 CHANGELOG가 이미 보유한다.

설정
----
카탈로그 `history_residue`에서 관리한다(없으면 내장 기본값 사용):

    "history_residue": {
      "metadata_history_fields": ["수정 이력", "변경 이력"],
      "delta_block_signatures": ["### 이전 델타", "영향 점검"],
      "flag_strikethrough": true
    }

코드 펜스(```...```) 내부는 검사에서 제외한다(예시 diff 등 오탐 방지).
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

CHECK_NAME = "history_residue"

RULE_META = "history_metadata_field"
RULE_STRIKE = "strikethrough_residue"
RULE_DELTA = "delta_block_residue"

DEFAULTS = {
    "metadata_history_fields": ["수정 이력", "변경 이력"],
    # 델타 블록/서사 리터럴 서명. "영향 점검"은 "시스템 영향 점검"으로 좁혀 오탐 회피
    # (참조 설명 "…클라이언트 영향 점검"이 델타 블록으로 오인되지 않게).
    "delta_block_signatures": [
        "### 이전 델타", "적용 범위 전환", "스탠스 종료", "시스템 영향 점검", "델타 승계",
    ],
    "flag_strikethrough": True,
}

# `> 수정 이력:` 형태(인용 메타 줄). 앞의 `>` 개수/공백 허용.
_META_RE = re.compile(r"^\s*>+\s*(수정 이력|변경 이력)\s*:", re.UNICODE)
# 마크다운 취소선 ~~text~~ (빈 ~~~~ 제외 위해 최소 1자).
_STRIKE_RE = re.compile(r"~~(?=\S).+?~~", re.UNICODE)
# 버전-인접 "델타"/"점검" — 델타 블록(`**0.X.0 델타**`)·메타 델타 서사
# (`> 출처: … 스프린트 0.18.0 델타 …`)·per-sprint 감사 이력(`스프린트 0.17.0 점검`)을
# 함께 잡는다. "델타"·버전인접 "점검"은 변경/감사 서술 어휘라 라이브 스펙엔 없어야 한다.
# `.dev/0.12.0/kickoff.md` 경로 참조는 버전 뒤가 `/kickoff`라 미매치(타이트).
_VERSION_HIST_RE = re.compile(r"\d+\.\d+(?:\.\d+)?\S*\s*(?:델타|점검)", re.UNICODE)


def _cfg(catalog: dict) -> dict:
    c = dict(DEFAULTS)
    c.update(catalog.get("history_residue") or {})
    return c


def run(catalog: dict, project_root: Path) -> CheckResult:
    result = CheckResult(check=CHECK_NAME)
    cfg = _cfg(catalog)
    meta_fields = cfg.get("metadata_history_fields") or []
    delta_sigs = cfg.get("delta_block_signatures") or []
    flag_strike = cfg.get("flag_strikethrough", True)

    # design + tactical 상세설계 파일만 대상. fragment/CHANGELOG(이력 권위)는 제외.
    exempt_kinds = {"fragment", "release_changelog"}

    for rf in expand_all_file_kinds(catalog, project_root):
        if not rf.exists or rf.kind in exempt_kinds:
            continue
        try:
            content = read_text(rf.path)
        except OSError:
            continue
        try:
            shown = str(rf.path.relative_to(project_root))
        except ValueError:
            shown = str(rf.path)

        for line_no, raw in iter_content_lines(content):
            # 1) 이력 메타 필드
            m = _META_RE.match(raw)
            if m and m.group(1) in meta_fields:
                result.add(Violation(
                    file=shown, line=line_no, rule=RULE_META, file_kind=rf.kind,
                    message=(
                        f"상단 메타에 이력 필드 `> {m.group(1)}:`가 있다 — 라이브 문서는 "
                        "현재 상태만 담는다. 이 줄을 제거한다(이력은 CHANGELOG·"
                        "tactical-archive 권위). 메타는 버전·최종 수정·입력(현행)·서비스까지."
                    ),
                ))
                continue
            # 2) 델타 블록/서사 — 리터럴 서명 또는 버전-인접 "델타"
            hit = next((sig for sig in delta_sigs if sig in raw), None)
            if hit is None and _VERSION_HIST_RE.search(raw):
                hit = "버전-인접 델타/점검 서사"
            if hit is not None:
                is_meta = raw.lstrip().startswith(">")
                where = (
                    "메타 줄에 스프린트 델타/점검 서사가 남았다 — `> 출처:`/`> 입력:`/`> 도메인:`은 "
                    "현행 근거만 담는다(예: `design/design.md(현행)`). 델타/점검 서술 제거."
                    if is_meta else
                    "본문에 델타/이력 블록이 있다 — 현재 상태로 덮어쓰고 이력은 CHANGELOG로 넘긴다."
                )
                result.add(Violation(
                    file=shown, line=line_no, rule=RULE_DELTA, file_kind=rf.kind,
                    message=f"이력 잔재('{hit}'). {where}",
                ))
            # 3) 취소선
            if flag_strike and _STRIKE_RE.search(raw):
                result.add(Violation(
                    file=shown, line=line_no, rule=RULE_STRIKE, file_kind=rf.kind,
                    message=(
                        "취소선(~~…~~) — 라이브 문서에 취소선의 정당한 용도는 없다. "
                        "종류별로 처리: (a) 순수 대체(`~~옛~~ → 새`)는 최종 상태만 남긴다. "
                        "(b) deprecated-but-present 필드·재사용 금지 결번 ID는 현재 제약이라 "
                        "행·상태를 보존하되 취소선 마크업만 벗겨 `deprecated`·`결번` 텍스트로 "
                        "남긴다(정보는 상태 칸이 담는다 — 취소선은 중복). 어느 경우든 `~~`는 제거."
                    ),
                ))

    return result.finalize()


def main() -> int:
    parser = argparse.ArgumentParser(description="이력 잔재 체크")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=None)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = run(catalog, args.project_root)
    print(dump_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
