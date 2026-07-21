# API 경로 구성

> 버전: v1.0.0
> 최종 수정: 2026-05-19
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 도메인이 외부에 노출하는 HTTP endpoint가 있는 경우 (`domain/{도메인}/api.md` 작성 대상)
> - 백엔드 서비스가 REST/RPC 스타일 API를 제공하는 경우

---

## 메타-규칙

API 경로는 프로젝트 전역에서 **단일 prefix 정책**과 **단일 케이싱 정책**을 따른다. 리소스 명명, 경로 변수 표기, 액션 표현 방식도 도메인마다 갈리지 않도록 단일 형식으로 통일한다. 도메인 api.md는 자체적으로 경로 규칙을 결정하지 않고 본 컨벤션이 박힌 `service/{백엔드 서비스}.md`의 결정을 따른다. 경로에 쓰는 HTTP 메서드의 선택 기준은 `http-methods.md`, 버전 prefix를 어떻게 운용·폐기하는지는 `api-versioning.md`에서 결정한다 — 본 컨벤션은 prefix 문자열과 경로 형태만 정한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 상세설계서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| API prefix | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 셋 중 택일: ① `/api` ② `/api/v{N}` (버전 포함) ③ prefix 없음. 외부 공개 API와 내부 전용 API의 prefix가 다르면 각각 명시 |
| 경로 케이싱 | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 단일 케이싱 강제 (보통 kebab-case). 복합어 분리 규칙(예: `git-repositories` vs `gitrepositories`)도 함께 명시 |
| 리소스 명명 (단수/복수) | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 둘 중 택일: ① 복수형 강제 (`/users`) ② 단수형 강제 (`/user`). 컬렉션·아이템 구분 없이 동일 정책 |
| 경로 변수 표기 | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 둘 중 택일: ① `:id` (Express/NestJS 스타일) ② `{id}` (OpenAPI 스타일). 변수명은 `id` 강제 또는 `{도메인}Id` 허용 중 택일 |
| 중첩 리소스 표현 | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 적용 깊이 결정 (예: 1단계까지만 허용, 2단계 이상은 평탄화). 평탄화 시 별도 컨트롤러로 분리할지 여부 |
| 액션 endpoint 표현 | `service/{백엔드 서비스}.md` / API 경로 컨벤션 섹션 | 셋 중 택일: ① RPC 스타일 (`POST /:id/{action}`, 예: `/approvals/:id/approve`) ② PATCH 상태 변경 (`PATCH /:id`, body에 상태) ③ 혼합 (상태 전이는 PATCH, 부수효과 있는 액션은 RPC) |

---

## 상세설계 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## API 경로 컨벤션

| 항목 | 정책 |
|------|------|
| API prefix | `/api/v1` (외부·내부 동일) |
| 경로 케이싱 | kebab-case 강제. 복합어는 하이픈 분리 (`git-repositories`) |
| 리소스 명명 | 복수형 강제 (`/users`, `/projects`) |
| 경로 변수 | `:id` 표기. 변수명은 `id` 강제 (도메인 prefix 금지) |
| 중첩 리소스 | 1단계까지 허용 (`/projects/:id/members`). 2단계 이상은 평탄화 |
| 액션 endpoint | 부수효과 있는 액션은 RPC 스타일 (`POST /approvals/:id/approve`). 단순 상태 전이는 PATCH (`PATCH /todos/:id/status`) |
```
