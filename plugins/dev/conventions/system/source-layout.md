# 서비스 소스 구조 (source layout)

> 버전: v1.0.0
> 최종 수정: 2026-06-25
> 적용 조건: 다음에 해당하면 적용
> - `system.md` 의 "서비스 구성" 에 배포 단위 서비스가 1개 이상 정의되는 경우 (= 코드 산출물이 생기는 모든 구현 프로젝트)

---

## 메타-규칙

**서비스 = 배포 단위 = 폴더 1개.** 모든 소스는 모노레포의 `services/{backend|frontend}/{서비스}/` 아래 둔다. `backend`/`frontend` 2단계 구분은 **배포 성격**으로 가른다 — 장기 실행 서버 프로세스 = `backend`, 정적 SPA/CDN 자산 = `frontend`. **UI 유무가 기준이 아니다**(예: SSR 웹 콘솔은 화면을 그리지만 서버 배포 단위이므로 `backend`). 각 구분 안에서는 서비스를 **평평하게 나열**한다(추가 중첩 디렉토리 없음).

각 서비스 폴더는 **자기완결 배포 단위**로 자기 빌드·설정·`.env`·포트·실행 산출물을 소유한다. **스택은 강제하지 않는다** — 언어/런타임/패키지 매니저는 서비스마다 자유롭게 고른다. DB는 **db-per-service** — 서비스가 실행하는 스키마·시드·마이그레이션은 그 서비스 폴더의 `db/` 가 소유한다(다른 서비스의 DB를 참조하지 않는다).

표준 골격(스택이 달라도 이 배치 의도는 유지):

```
services/
├─ backend/{서비스}/
│   ├─ src/{domains, core, config, providers}   # (+ 필요 시 utils) 모든 백엔드 공통 골격
│   ├─ db/{schema.sql, seed.sql, migrations/}    # db-per-service. 이 서비스가 실행하는 소스
│   ├─ assets/  test/                            # 선택
│   ├─ .env.example                              # 접속 좌표(키만). 실제 .env 값은 gitignore
│   └─ package.json  tsconfig.json …             # 빌드/설정. dist/ logs/ 는 gitignore
└─ frontend/{서비스}/
    ├─ src/{…}  public/                          # 화면/자산. DB 없음 → db/ 없음
    └─ package.json  vite.config.ts …            # 빌드/설정. dist/ 는 gitignore
```

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 명세서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 서비스 목록 (배포 단위 경계) | `system.md` / 서비스 구성 | 표의 각 행 = 배포 단위 1개. 분리/통합 결정은 아키텍처 의사결정(L3) |
| 각 서비스의 레이어 구분 | `system.md` / 서비스 구성 (서비스 식별자 = 폴더 경로) | `services/backend/{서비스}` 또는 `services/frontend/{서비스}`. 기준 = 배포 성격(서버 프로세스 vs 정적 SPA), UI 유무 아님 |
| 각 서비스 폴더명 | `system.md` / 서비스 구성 | 케밥-케이스 권장. 폴더명 = 배포 단위명 (pm2 name·패키지명과 일치 권장) |
| 각 서비스 기술 스택 | `system.md` / 서비스 구성 의 각 서비스 섹션 | 언어/런타임/패키지 매니저 (스택 비강제이므로 서비스마다 명시) |

> 서비스 식별자를 폴더 경로(`services/{layer}/{서비스}`)로 쓰는 이유: 명세서의 서비스 식별자와 코드 위치가 1:1로 고정되어, coder/deployer/verifier가 경로를 추론하지 않고 그대로 사용한다.

---

## spec 작성 예

결정의 결과가 명세서에 어떻게 박히는지 샘플.

```markdown
## 서비스 구성

### 서비스 목록

| 서비스 (폴더) | 담당 도메인 | 비고 |
|---|---|---|
| `services/backend/gateway` | 게이트웨이·라우팅·인증 위임 | NestJS |
| `services/backend/core`    | USR·AUT·PERM·… | NestJS, db-per-service |
| `services/frontend/payer-web` | 결제 페이지 | Vite SPA, CDN 배포 |

### core
- 역할: …
- 기술 스택: NestJS (TypeScript)
- 소스 위치: `services/backend/core/` — 표준 백엔드 골격(`src/{domains,core,config,providers}` + `db/`)
```
