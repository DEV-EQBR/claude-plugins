# 요청·응답 본문 필드 명명

> 버전: v1.0.0
> 최종 수정: 2026-05-19
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 도메인이 요청·응답 본문(JSON)을 주고받는 HTTP endpoint를 제공하는 경우
> - `domain/{도메인}/api.md`에 request body / response body 스키마를 명시하는 경우

---

## 메타-규칙

요청·응답 본문 필드는 프로젝트 전역에서 **단일 케이싱 정책**을 따른다. timestamp, actor, ID, boolean 등 도메인이 반복적으로 사용하는 필드는 표준 명명 규칙을 두어 도메인마다 다른 이름을 짓지 않게 한다. 도메인 api.md의 필드명은 entities.md의 속성 명명과 일치해야 한다 — 둘이 어긋나면 tactical-verifier가 위반으로 검출한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 상세설계서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 본문 필드 케이싱 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 둘 중 택일: ① camelCase 강제 (`createdAt`, `accountId`) ② snake_case 강제 (`created_at`, `account_id`). 도메인·필드 무관하게 단일 정책 |
| Timestamp 필드 명명 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 표준 접미사 결정: `-At` (`createdAt`) vs `-Time` vs `-Date`. 표준 필드 목록 명시: 생성/수정/삭제/공개 등 |
| Actor 필드 명명 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 표준 접미사: `-By` (`createdBy`, `updatedBy`). 값 타입(사용자 ID vs 사용자 객체)도 결정 |
| ID 필드 명명 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 두 가지 결정: ① 자기 자신의 PK는 `id` 강제 ② 외래 키는 `{도메인}Id` 형태 강제 (예: `userId`, `projectId`). 도메인 prefix 생략 금지 |
| Boolean 필드 명명 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 접두사 강제 여부 결정: `is-`/`has-` 강제 vs 자유. 강제 시 적용 범위(상태 vs 권한 등)도 명시 |
| Enum 값 표기 | `service/{백엔드 서비스}.md` / 필드 명명 컨벤션 섹션 | 둘 중 택일: ① UPPER_SNAKE (`PENDING`, `IN_PROGRESS`) ② lower_snake (`pending`) ③ camelCase (`inProgress`). 도메인별 enum 값에 동일 적용 |

---

## 상세설계 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 필드 명명 컨벤션

| 항목 | 정책 |
|------|------|
| 본문 필드 케이싱 | camelCase 강제 (요청·응답 동일) |
| Timestamp | `-At` 접미사 강제 (`createdAt`, `updatedAt`, `deletedAt`, `publishedAt`) |
| Actor | `-By` 접미사. 값 타입은 사용자 ID(string) (`createdBy`, `updatedBy`) |
| 자기 PK | `id` 강제 |
| 외래 키 | `{도메인}Id` 강제 (`userId`, `projectId`). 단일 어휘 ID(예: `assignee`) 금지 |
| Boolean | `is-`/`has-` 접두사 강제 (`isActive`, `hasPermission`) |
| Enum 값 | UPPER_SNAKE 강제 (`PENDING`, `APPROVED`, `IN_PROGRESS`) |

> entities.md의 속성 명명은 본 컨벤션과 일치해야 한다. DB 컬럼이 snake_case여도 API 본문은 위 정책을 따른다.
```
