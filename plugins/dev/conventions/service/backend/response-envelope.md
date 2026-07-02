# 응답 공통 래퍼

> 버전: v1.0.0
> 최종 수정: 2026-05-19
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 백엔드가 JSON 응답을 반환하는 HTTP endpoint를 제공하는 경우
> - 클라이언트(프론트엔드 / 외부 시스템)가 성공·실패 응답을 단일 형식으로 파싱하기를 기대하는 경우

---

## 메타-규칙

성공·실패 응답은 **단일 공통 래퍼 구조**로 통일한다. 응답을 받은 측이 도메인·엔드포인트에 무관하게 동일 규칙으로 성공 여부를 판정하고 데이터를 추출할 수 있어야 한다. 도메인 api.md는 래퍼 구조를 다시 결정하지 않고 본 컨벤션이 박힌 결정을 그대로 따른다. 목록 응답(`items` + `pagination`)의 내부 구조는 본 컨벤션이 아닌 `list-response.md`에서 별도 결정. `data` 안에 담기는 리소스 본문의 관계 표현(임베드 vs 참조 ID)·부분 응답은 `resource-representation.md`, 응답에 실리는 HTTP 상태 코드는 `status-codes.md`에서 결정한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 명세서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 성공 여부 판정 방식 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | 둘 중 택일: ① 본문 최상위 `success: boolean` 필드 ② HTTP 상태 코드만 사용 (본문 래퍼 없음, body가 곧 data) |
| 성공 응답 구조 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | `success` 방식 선택 시: `{ success: true, data: ..., message?: string }` 등 정확한 키 명세. `data` 필드 사용 여부와 옵셔널 키도 결정 |
| 실패 응답 구조 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | `{ success: false, error: { code, message }, details?: ... }` 형태로 키 명세. `error` 객체의 내부 키와 추가 필드(`details`, `traceId` 등) 사용 조건 명시 |
| `message` 필드 사용 조건 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | 셋 중 택일: ① 항상 사용 ② 사용자 안내가 필요한 경우만 ③ 사용 안 함. 도메인별 자율 결정 금지 |
| 단일 객체 응답의 `data` 키 강제 여부 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | 둘 중 택일: ① `data` 키로 항상 래핑 (`{ success, data: { id, name } }`) ② 객체 필드를 최상위에 풀어 표기 (`{ success, id, name }`). 도메인 간 혼재 금지 |
| 빈 응답 표현 | `service/{백엔드 서비스}.md` / 응답 래퍼 섹션 | 삭제·승인 등 반환할 데이터가 없는 경우의 응답 형태 결정: `{ success: true }` 단독 / `{ success: true, data: null }` / HTTP 204 No Content |

---

## spec 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 응답 래퍼

모든 응답은 아래 단일 구조를 따른다.

**성공:**
\`\`\`json
{
  "success": true,
  "data": { ... },
  "message": "선택적, 사용자 안내가 필요한 경우만"
}
\`\`\`

**실패:**
\`\`\`json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자에게 노출 가능한 메시지"
  },
  "details": [ ... ]
}
\`\`\`

| 항목 | 정책 |
|------|------|
| 성공 여부 판정 | 본문 `success: boolean` 필드 (HTTP 상태 코드와 병행) |
| `data` 키 | 단일 객체·배열 무관 항상 래핑 |
| `message` (성공) | 사용자 안내가 필요한 경우만 (생성·갱신 완료 메시지 등) |
| `error` 구조 | `{ code, message }` 필수. `code` 카탈로그는 `error-catalog.md` 결정 따름 |
| `details` (실패) | 입력 검증 실패 시 필드별 오류 배열로 포함 |
| 빈 응답 | `{ success: true }` 단독 (HTTP 200) |
```
