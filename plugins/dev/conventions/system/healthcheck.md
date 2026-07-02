# 헬스체크

> 버전: v1.0.0
> 최종 수정: 2026-05-22
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - `system.md` 의 "서비스 구성" 에 프로세스로 기동되는 서비스가 1개 이상 정의된 경우 (백엔드/프론트엔드 무관)
> - `system.md` 의 "배포 구조" 가 컨테이너·오케스트레이터·로드밸런서·프로세스 매니저 등 외부에서 프로세스 상태를 폴링하는 환경을 전제하는 경우

---

## 메타-규칙

프로세스로 기동되는 **모든 서비스**는 외부에서 정상 여부를 확인할 수 있는 헬스체크 엔드포인트를 노출한다. 경로는 시스템 전역에서 단일 형식으로 통일하고, 응답 형식(상태 enum + HTTP 코드 매핑)도 서비스마다 갈리지 않도록 단일 형식으로 통일한다. 의존성 상태 검사 항목은 각 서비스가 자신의 의존성에 맞게 결정한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 명세서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 헬스체크 경로 | `system.md` / 헬스체크 컨벤션 섹션 | 기본 `/health`. API prefix(`/api/v1` 등) 적용 여부 결정 (적용 시 `/api/v1/health`). 전 서비스 공통 |
| HTTP 메서드 | `system.md` / 헬스체크 컨벤션 섹션 | `GET` 강제. 부수효과 없음 |
| liveness / readiness 분리 | `system.md` / 헬스체크 컨벤션 섹션 | 둘 중 택일: ① 단일 엔드포인트 (`/health`) ② 분리 (`/health/live` = 프로세스 살아있음, `/health/ready` = 의존성 포함 트래픽 수신 가능) |
| 응답 상태 enum | `system.md` / 헬스체크 컨벤션 섹션 | 단일 enum 정의 (예: `ok` / `degraded` / `down`). 전 서비스 공통 |
| 상태별 HTTP 코드 매핑 | `system.md` / 헬스체크 컨벤션 섹션 | 각 상태값별 응답 코드 결정 (예: `ok=200`, `degraded=200` 또는 `503`, `down=503`). 외부 폴러(LB/오케스트레이터)의 판정 기준과 정렬 |
| 응답 본문 형식 | `system.md` / 헬스체크 컨벤션 섹션 | JSON 본문 키 정의 (예: `{ "status": "ok", "checks": [...] }`). 의존성 검사 결과 포함 형식 (각 항목의 `name` / `status` / `latencyMs` 등) |
| 인증 정책 | `system.md` / 헬스체크 컨벤션 섹션 | 셋 중 택일: ① 인증 면제 (공개) ② 내부망 한정 (네트워크 경계로 차단) ③ 토큰/시크릿 필요. 응답에 노출되는 정보 민감도(의존성명·내부 hostname 등)와 함께 결정 |
| 의존성 검사 항목 | `service/{서비스}.md` / 헬스체크 의존성 섹션 | 해당 서비스가 정상 동작을 위해 도달 가능해야 하는 의존성 목록 (DB·캐시·메시지 큐·외부 API·파일시스템 등). 각 항목별 검사 방식(예: `SELECT 1`, `PING`)과 timeout 명시 |

---

## spec 작성 예

### system.md

```markdown
## 헬스체크 컨벤션

| 항목 | 정책 |
|------|------|
| 경로 | `/health` (API prefix 미적용. 전 서비스 공통) |
| HTTP 메서드 | `GET` |
| liveness / readiness | 분리 — `/health/live` (프로세스 가동), `/health/ready` (의존성 포함 트래픽 수신 가능) |
| 응답 상태 enum | `ok` / `degraded` / `down` |
| 상태별 HTTP 코드 | `ok` = 200, `degraded` = 200 (의존성 일부 장애지만 서비스는 계속 처리), `down` = 503 |
| 응답 본문 형식 | `{ "status": "ok\|degraded\|down", "version": "<service version>", "checks": [{ "name": "<dep>", "status": "ok\|down", "latencyMs": <int> }] }` |
| 인증 정책 | 인증 면제. 내부 의존성 hostname 등 식별 정보는 응답에서 마스킹 |
```

### service/{서비스}.md

```markdown
## 헬스체크 의존성

| 의존성 | 검사 방식 | timeout | 실패 시 status |
|--------|----------|---------|---------------|
| PostgreSQL (`primary`) | `SELECT 1` | 500ms | `down` |
| Redis (`session-cache`) | `PING` | 200ms | `degraded` (캐시 미스로 fallback 가능) |
| Payment Gateway (`stripe`) | `GET /v1/balance` (캐시된 토큰) | 1000ms | `degraded` (결제 외 기능은 정상) |
```
