# HTTP 캐싱 정책

> 버전: v1.0.0
> 최종 수정: 2026-06-12
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - 조회(`GET`) HTTP endpoint를 제공하는 경우
> - webview·모바일·CDN 등 중간/클라이언트 캐시를 경유하는 통신이 있는 경우
>
> socket·gRPC 등 비 HTTP 통신은 범위 밖이다.

---

## 메타-규칙

HTTP 캐싱은 **단일 강제값이 아니라 "endpoint 성격별 등급"으로 정한다** — 같은 API라도 공개/정적이냐, 개인화냐, 실시간·민감이냐에 따라 캐싱 가능성이 다르기 때문이다. 본 컨벤션은 그 *성격 등급의 분류 기준과 등급별 기본 동작*을 정하고, 각 endpoint를 어느 등급에 넣을지는 도메인 `api.md`가 표기한다. 또한 **소비 플랫폼의 캐시 동작이 정책 선택에 영향**을 준다(예: Android WebView ↔ 서버 통신에서 캐시가 의도와 다르게 동작하는 케이스) — 등급 정의 시 대상 플랫폼을 고려해야 한다. 조건부 응답의 상태 코드(`304`)는 `status-codes.md`와 정합한다.

> **검증 경로**: 등급/헤더가 상세설계에 박혔는지는 Stage 2 LLM judge가, 실제 응답 헤더·`304` 동작은 fragment "검증 항목"으로 런타임 `verifier`가 확인한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 상세설계서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 캐싱 등급 분류 | `service/{백엔드 서비스}.md` / 캐싱 섹션 | 성격별 등급 정의 + 판정 기준. 예: ① 공개·정적(캐시 가능) ② 개인화(private) ③ 비캐시(no-store, 실시간·민감). 각 등급에 들어가는 신호 명시 |
| 등급별 `Cache-Control` | `service/{백엔드 서비스}.md` / 캐싱 섹션 | 등급마다의 디렉티브 매핑: `public`/`private`/`no-store`/`no-cache`/`must-revalidate` + `max-age`(초). 단일 표로 |
| 조건부 캐싱 (validation) | `service/{백엔드 서비스}.md` / 캐싱 섹션 | `ETag` / `Last-Modified` 사용 여부. 사용 시 `If-None-Match`/`If-Modified-Since` → `304` 반환 정책. ETag 약/강 구분 |
| 기본값 (미지정 endpoint) | `service/{백엔드 서비스}.md` / 캐싱 섹션 | 등급이 명시되지 않은 endpoint의 안전한 기본 동작: `no-store` vs `no-cache` |
| 플랫폼 영향 / 예외 | `service/{백엔드 서비스}.md` / 캐싱 섹션 | 특정 클라이언트 플랫폼(예: Android WebView)의 캐시 동작 특이점과 그에 따른 등급 조정·예외 헤더 정책. 대상 플랫폼 목록 |
| 캐시 무효화 | `service/{백엔드 서비스}.md` / 캐싱 섹션 | 쓰기 후 관련 캐시 무효화 책임: 서버 헤더(짧은 max-age·`must-revalidate`) vs 클라이언트 책임. 정책 수준 명시 |

---

## 상세설계 작성 예

`service/{백엔드 서비스}.md` 에 다음 섹션을 추가한다.

```markdown
## 캐싱

### 등급 분류 → `Cache-Control`

| 등급 | 판정 기준 | `Cache-Control` | 조건부 |
|------|----------|-----------------|--------|
| 공개·정적 | 인증 무관, 변경 드묾 (코드 테이블·공지) | `public, max-age=300` | `ETag` |
| 개인화 | 인증 주체별로 다른 응답 | `private, max-age=0, must-revalidate` | `ETag` |
| 비캐시 | 실시간·민감 (잔액·결제 상태) | `no-store` | — |

- 등급 미지정 endpoint 기본값: `no-store` (안전 우선)
- 각 endpoint의 등급은 `domain/{도메인}/api.md`에 표기

### 플랫폼 고려

- Android WebView는 일부 버전에서 `no-store`를 무시하고 디스크 캐시를 사용 → 민감 응답에는 `no-store` + `Pragma: no-cache` 병행
- 조건부 캐싱은 `If-None-Match` → 변경 없으면 `304 Not Modified` (본문 없음)
```
