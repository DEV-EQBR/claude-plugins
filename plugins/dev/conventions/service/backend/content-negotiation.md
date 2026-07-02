# 콘텐츠 협상

> 버전: v1.0.0
> 최종 수정: 2026-06-12
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 백엔드가 HTTP endpoint를 제공하는 경우
> - webview·모바일·외부 시스템 등 복수 클라이언트 플랫폼이 동일 API를 소비하는 경우
>
> socket·gRPC 등 비 HTTP 통신은 범위 밖이다.

---

## 메타-규칙

요청·응답의 **미디어 타입과 문자 인코딩은 전역 단일 기본값**을 따른다. 어느 클라이언트 플랫폼(webview / 네이티브 / 외부 시스템)이든 같은 규칙으로 요청을 구성하고 응답을 파싱할 수 있어야 한다. JSON이 아닌 예외 endpoint(파일 업로드·다운로드 등)는 개별적으로 식별하여 명시한다.

> **검증 경로**: 미디어 타입·인코딩 정책이 명세에 박혔는지는 Stage 2 LLM judge가, `415`/`406` 등 협상 실패 동작은 필요 시 fragment "검증 항목"으로 런타임 `verifier`가 확인한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 명세서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 기본 미디어 타입 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | `application/json` 단일 기본값 강제. JSON이 아닌 endpoint(`multipart/form-data` 업로드, `application/octet-stream` 다운로드 등)는 예외 목록으로 명시 |
| 문자 인코딩 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | `UTF-8` 강제. 응답 `Content-Type`에 `; charset=utf-8` 명시 여부 결정 |
| 요청 Content-Type 검증 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | 본문 있는 요청의 `Content-Type` 불일치 처리: `415 Unsupported Media Type` vs 관대 수용. 강제 시 적용 메서드(POST/PUT/PATCH) 명시 |
| Accept 헤더 처리 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | 셋 중 택일: ① 무시하고 항상 JSON ② 존중하되 미지원이면 `406 Not Acceptable` ③ 존중하되 기본값 폴백. 플랫폼 호환성 고려 |
| 본문 없는 메서드의 헤더 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | `GET`/`DELETE` 등 본문 없는 요청에 `Content-Type` 요구 여부(보통 불요) |
| 응답 압축 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | `Accept-Encoding` 기반 gzip/br 협상 사용 여부. webview·저대역 클라이언트 영향 고려. 미사용 시 명시 |
| 버전 협상 위치 | `service/{백엔드 서비스}.md` / 콘텐츠 협상 섹션 | API 버전을 `Accept` 헤더(미디어 타입 파라미터)로 협상할지 여부. URL 버저닝을 쓰면 "헤더 미사용"으로 명시 (`api-versioning.md`와 정합) |

---

## spec 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 콘텐츠 협상

| 항목 | 정책 |
|------|------|
| 기본 미디어 타입 | `application/json` 강제 |
| 문자 인코딩 | `UTF-8`. 응답 `Content-Type: application/json; charset=utf-8` |
| 요청 Content-Type | POST/PUT/PATCH는 `application/json` 아니면 `415` |
| Accept 헤더 | 무시하고 항상 JSON 반환 (단순화) |
| 응답 압축 | gzip 지원 (`Accept-Encoding` 존중) — webview 호환 확인됨 |
| 버전 협상 | Accept 헤더 미사용 — URL prefix 버저닝 (`api-versioning.md`) |

### 예외 endpoint (비 JSON)

| endpoint | 미디어 타입 | 용도 |
|----------|-----------|------|
| `POST /files` | `multipart/form-data` | 파일 업로드 |
| `GET /files/:id/content` | `application/octet-stream` | 파일 다운로드 |
```
