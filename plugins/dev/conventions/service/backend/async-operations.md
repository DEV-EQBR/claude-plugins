# 장기 실행 / 비동기 작업

> 버전: v1.0.0
> 최종 수정: 2026-06-12
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 동기 응답 시간 안에 끝나지 않는 작업(배치·대용량 처리·느린 외부 연동)을 HTTP로 트리거하는 경우
>
> socket·gRPC 등 비 HTTP 통신은 범위 밖이다.

---

## 메타-규칙

즉시 완료하지 못하는 작업은 **`202 Accepted`로 수락하고, 별도 상태 리소스로 진행을 추적하는 단일 패턴**을 따른다. 도메인마다 다른 비동기 표현(롱폴링·임의 콜백 등)을 즉석에서 만들지 않는다. 수락 응답의 상태 코드(`202`)는 `status-codes.md`, 본문 래퍼는 `response-envelope.md`, 상태 enum 명명은 `field-naming.md`, 중복 제출 방지는 `idempotency.md`, 실패 시 에러 코드는 `error-catalog.md`와 정합한다.

> **검증 경로**: 제출 → `202` → 상태 폴링 → 완료의 *흐름*은 fragment "검증 항목"으로 런타임 `verifier`가 확인한다. 본문 키·상태 enum의 정합은 Stage 2 LLM judge가 본다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 명세서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 비동기 전환 기준 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 어떤 작업을 비동기로 둘지: 예상 처리시간 임계 / 외부 의존 / 대용량. 동기·비동기 분기 기준 명시 |
| 수락 응답 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | `202` 본문에 담을 작업 식별자(`jobId`)와 상태 조회 위치(`statusUrl` 또는 `Location`). 키 명명은 `field-naming.md` |
| 상태 리소스 구조 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 상태 enum(예: `PENDING`/`RUNNING`/`SUCCEEDED`/`FAILED`), 진행률 포함 여부, 완료 시 결과 위치, 실패 시 에러 표현 |
| 상태 조회 방식 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 폴링(`GET statusUrl`) vs push(webhook/SSE). 폴링이면 권장 주기(`Retry-After`) 제공 여부 |
| 완료 결과 전달 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 상태 리소스에 결과 임베드 vs 별도 결과 endpoint(`303 See Other` 등)로 분리 중 택일 |
| 작업 보존 기간 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 완료된 작업 상태를 얼마나 조회 가능하게 유지할지 |
| 취소 지원 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 진행 중 작업 취소 endpoint 제공 여부와 방식 |
| 중복 제출 방지 | `service/{백엔드 서비스}.md` / 비동기 작업 섹션 | 같은 작업의 중복 제출을 `idempotency.md` 키로 막을지 여부 |

---

## spec 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 비동기 작업

| 항목 | 정책 |
|------|------|
| 전환 기준 | 예상 처리 5초 초과 또는 외부 배치 의존 작업 |
| 수락 응답 | `202` + `{ success: true, data: { jobId, statusUrl } }` |
| 상태 enum | `PENDING` / `RUNNING` / `SUCCEEDED` / `FAILED` (UPPER_SNAKE) |
| 상태 조회 | 폴링 `GET /api/v1/jobs/:jobId`. `Retry-After` 권장 주기 제공 |
| 결과 전달 | 완료 시 상태 리소스의 `resultUrl`로 분리 |
| 보존 기간 | 완료 후 7일간 상태 조회 가능 |
| 취소 | `POST /api/v1/jobs/:jobId/cancel` 지원 (`PENDING`/`RUNNING`만) |
| 중복 제출 | `Idempotency-Key`로 동일 작업 중복 제출 차단 (`idempotency.md`) |

### 상태 리소스 예

\`\`\`
GET /api/v1/jobs/job_123
{ "success": true, "data": {
  "jobId": "job_123", "status": "SUCCEEDED",
  "progress": 100, "resultUrl": "/api/v1/reports/r_456",
  "createdAt": "2026-06-12T00:00:00Z", "completedAt": "2026-06-12T00:01:30Z"
} }
\`\`\`
```
