# HTTP 응답 상태 코드

> 버전: v1.0.0
> 최종 수정: 2026-06-12
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 백엔드가 HTTP endpoint를 제공하는 경우
> - `domain/{도메인}/api.md`에 endpoint의 응답을 명시하는 경우
>
> socket·gRPC 등 비 HTTP 통신은 범위 밖이다.

---

## 메타-규칙

성공 응답의 HTTP 상태 코드는 **작업 성격에 따라 일관되게 매핑**한다. 같은 성격의 결과(생성 / 동기 완료 / 비동기 수락 / 무내용)에 도메인마다 다른 코드를 반환하지 않는다. 본 컨벤션은 *상태 코드의 선택 기준*만 정한다 — 실패(4xx/5xx) 코드 카탈로그와 HTTP↔공통 코드 매핑은 `error-catalog.md`, 응답 본문 래퍼 구조는 `response-envelope.md`, 비동기 수락(`202`) 이후 흐름은 `async-operations.md`, 조건부 응답(`304`)은 `caching.md`에서 결정한다.

> **검증 경로**: 상태 코드 매핑이 상세설계에 박혔고 도메인 `api.md`와 일관된지는 Stage 2 LLM judge가 본다. deterministic 룰은 추가하지 않는다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 상세설계서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 생성 성공 코드 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | 둘 중 택일: ① `201 Created` + `Location` 헤더(생성 리소스 URI) ② `200 OK`. 단일 정책으로 통일 |
| 동기 성공 코드 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | 조회·수정 성공은 `200 OK`로 단일화 |
| 무내용 응답 코드 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | 반환 데이터 없는 성공(삭제 등): `204 No Content`(본문 없음) vs `200`+`{ success: true }`. `response-envelope.md`의 빈 응답 결정과 일치해야 함 |
| 비동기 수락 코드 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | 즉시 완료하지 않는 작업에 `202 Accepted` 사용 여부. 사용 시 상태 추적 방법은 `async-operations.md`에서 결정 |
| 본문 `success` ↔ HTTP 상태 관계 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | `response-envelope.md`가 본문 `success` 필드를 쓰는 경우 HTTP 상태와의 정합 규칙 명시(2xx ↔ `success:true`). 상태 코드만 쓰면 본 행 불요 |
| 배치 / 멀티 상태 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | 한 요청에 항목별 부분 성공이 가능한 endpoint가 있으면: 멀티 상태(`207`류) vs `200`+본문 항목별 결과 중 택일. 없으면 "배치 없음" 명시 |
| 리다이렉트 사용 정책 | `service/{백엔드 서비스}.md` / 상태 코드 컨벤션 섹션 | API 응답에 3xx(`301`/`302`/`307`) 사용 여부. 보통 미사용(본문으로 처리), 사용 시 대상 endpoint 명시 |

---

## 상세설계 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 상태 코드 컨벤션

| 결과 | 상태 코드 | 본문 |
|------|----------|------|
| 조회·수정 성공 | `200 OK` | `{ success: true, data }` |
| 생성 성공 | `201 Created` | `{ success: true, data }` + `Location: /api/v1/{resource}/{id}` |
| 무내용 성공 (삭제 등) | `204 No Content` | 본문 없음 |
| 비동기 수락 | `202 Accepted` | `{ success: true, data: { jobId, statusUrl } }` — 추적은 `async-operations.md` |

- 모든 2xx 응답은 본문 `success: true`와 정합 (4xx/5xx는 `error-catalog.md`)
- 배치 요청 없음 — 멀티 상태(`207`) 미사용
- API 응답에 3xx 리다이렉트 미사용
```
