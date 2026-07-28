# 컨벤션 카탈로그

상세설계서 작성을 가이드하는 별도 문서 모음. 상세설계서 본문이 담는 정보(시스템/서비스/도메인)와는 별개로, 그 본문을 작성할 때 검토할 작성 기준이다.

## 정체성

| 항목 | 내용 |
|------|------|
| 정의 | 상세설계서 작성 시 검토하는 작성 기준 문서 모음 |
| 본문에 담는 것 | 메타-규칙(원칙) + 결정 항목(상세설계에 박힐 답을 가진 질문) + 상세설계 작성 예 |
| 본문에 담지 않는 것 | 구체 결정값 (그 결정은 각 프로젝트의 상세설계서에 인라인으로 박힘) |
| 변경 빈도 | 낮음. 팀 정책에 가까움 |
| 위치 | `plugins/dev/conventions/` |

상세설계서가 단일 진실 출처(SSOT)라는 원칙은 변하지 않는다. 컨벤션 본문은 상세설계서 작성을 도울 뿐, 구현 단계의 참조 대상이 아니다. 결정의 결과는 상세설계서에 인라인으로 박힌다.

## 디렉토리 구조

```
plugins/dev/conventions/
├── _template.md                # 본문 표준 템플릿
├── system/                     # system.md 차원에 박힐 컨벤션
│   ├── source-layout.md        # 서비스 소스 구조 (services/{backend|frontend}/{서비스}/, 배포 단위 = 폴더 1개)
│   ├── timezone.md
│   ├── blockchain-token-amount.md
│   ├── healthcheck.md
│   └── local-verification.md
└── service/
    ├── frontend/               # service/{프론트엔드 서비스}.md 차원에 박힐 컨벤션 (플랫폼 무관 — web·네이티브 공통)
    │   ├── number-display.md
    │   ├── date-display.md
    │   ├── phone-number.md
    │   ├── typography.md       # 본문 폰트 패밀리
    │   ├── screen-layout.md    # 폼팩터(데스크톱·태블릿·모바일) 기준 반응형 — OS 무관
    │   ├── design-tokens.md    # 색(의미 역할)·간격·radius·elevation·타입 스케일 (시각 단일 출처)
    │   ├── component-foundation.md  # UI 파운데이션 결정 + 베이스라인 컴포넌트 세트
    │   ├── component-states.md      # 상태 커버리지 (hover/focus/disabled/loading + empty/loading/error)
    │   ├── visual-hierarchy.md      # 밀도·정렬·강조 (1차 액션 1개 원칙)
    │   ├── motion.md                # 전이·피드백 모션 토큰 + reduced-motion + 모션 불변식(형용사→횟수·기하·시간 번역 카탈로그)
    │   └── a11y-baseline.md         # WCAG AA·키보드/포커스·시맨틱·터치 타깃
    #   ※ UI 검증 드라이버·배포 타깃(브라우저 vs 네이티브 시뮬레이터)은 화면 컨벤션이 아니라
    #     system/local-verification.md(배포 타깃 종류 / UI 검증 드라이버)가 정한다
    └── backend/                # service/{백엔드 서비스}.md 차원에 박힐 컨벤션 (HTTP 통신 한정)
        ├── api-path.md
        ├── http-methods.md
        ├── api-versioning.md
        ├── content-negotiation.md
        ├── field-naming.md
        ├── response-envelope.md
        ├── list-response.md
        ├── resource-representation.md
        ├── status-codes.md
        ├── error-catalog.md
        ├── idempotency.md
        ├── rate-limiting.md
        ├── caching.md
        └── async-operations.md
```

분리 축은 상세설계서의 정보 분류(시스템/서비스)를 그대로 따른다. 어느 상세설계서에 결과가 박힐지가 디렉토리 구조만 봐도 명확하다.

## 본문 구조

각 컨벤션 파일은 다음 3개 핵심 섹션을 가진다.

| 섹션 | 내용 |
|------|------|
| 메타-규칙 | 이 영역에서 항상 지켜야 할 원칙. 단정적 한두 줄. 프로젝트마다 변하지 않음 |
| 결정 항목 | 이 컨벤션을 따르려면 결정하여 상세설계서에 명시해야 할 항목 표 (결정 항목 + 명시 위치 + 형태/제약) |
| 상세설계 작성 예 | 결정의 결과가 상세설계서에 어떻게 박히는지 샘플 |

추가 메타 정보:
- 버전 / 최종 수정일
- 적용 조건 — 검사 가능한 신호 목록 (`entities.md`/`screens.md`/`system.md` 등에서 직접 확인 가능한 형태)

상세는 `_template.md` 참조.

## 적용 절차

상세설계서 작성 에이전트(`system-service-writer`)가 자기 절차에서 카탈로그를 자동 검토한다.

1. 카탈로그 전체 훑기 (`system/*.md`, `service/{레이어}/*.md`)
2. 각 컨벤션의 "적용 조건"과 설계서/기존 상세설계서를 대조하여 적용 여부 판단
3. 적용된 컨벤션의 "결정 항목"을 질문 목록에 포함하여 개발자에게 묻기
4. 답변을 받으면 "상세설계 작성 예" 형식을 참조하여 상세설계서에 인라인으로 박기
5. 보고 시 적용 컨벤션 / 미적용 컨벤션 (사유 포함) 명시

상세는 `plugins/dev/agents/system-service-writer.md`.

## 컨벤션 추가/변경

### 추가 트리거

다음 중 하나라도 해당하면 컨벤션 추가를 검토한다.

- 같은 결정/지시를 여러 프로젝트에서 반복함을 자각
- 상세설계서 작성 중 "이 결정은 컨벤션화할 만한데 카탈로그에 없음"을 발견
- 팀 표준 정립 회의에서 결정

### 작성 원칙

- 본문 표준(`_template.md`)을 따른다
- 추상화 수준은 "유즈케이스에 결합된 메타-규칙" 수준 — 너무 구체(특정 프로젝트 종속)도 너무 추상(공허)도 피한다
- 적용 조건은 검사 가능한 신호 목록으로 작성하여 false positive를 방지
- 결정 항목의 "형태/제약"은 가능하면 enum 형태로 명시 (모호함 차단)
- 상세설계에 박힐 결정값을 본문에 흡수하지 않는다 (그 결정은 프로젝트 상세설계에 박힘)

### 컨벤션이 아닌 것 (제외 기준)

다음 종류는 컨벤션 카탈로그에 두지 않는다.

| 종류 | 위치 |
|------|------|
| 비즈니스 사실/규칙 | `domain/{도메인}/rules.md` |
| 수치/임계값 (성능 등) | `system.md` / `service/{서비스}.md` 비기능 요구사항 |
| 가이드라인 (단정 불가, 추천만) | 문서 외 영역 (코드 리뷰 등) |
| 프로젝트별 디자인 결정 | 프로젝트 디자인 시스템/토큰 |

## Future Work

- **카탈로그 인덱스 메커니즘**: 카탈로그가 커지면 `system-service-writer` 가 모든 파일을 매번 읽어야 하는 부담이 있음. 적용 조건만 모은 인덱스 파일을 두고, 인덱스 보고 해당 파일만 정독하는 방식으로 전환 검토.
