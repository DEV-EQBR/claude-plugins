# API 채널 시나리오 템플릿 (Hurl)
# 검증 항목 한 줄 → 선언적 요청 + 응답 assert. 외부 호출 timeout 내장.
# 실행 예: hurl --variable base=http://127.0.0.1:PORT --connect-timeout 5 --max-time 10 --test this.hurl
#
# 변수: {{base}} 서비스 주소, {{maker}}/{{pw}} 자격, {{transferId}} 전제 데이터
#
# --- 전제: 로그인하여 토큰 확보 ---
POST {{base}}/api/v1/auth/sign-in
Content-Type: application/json
{ "email": "{{maker}}", "password": "{{pw}}" }
HTTP 200
[Captures]
token: jsonpath "$.data.accessToken"

# --- 검증 항목: SC-005 송금 실행 → execution_status=IN_PROGRESS ---
POST {{base}}/api/v1/transfers/{{transferId}}/execute
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.data.executionStatus" == "IN_PROGRESS"

# --- 에러 케이스 예: 권한 없는 사용자 차단 ---
# POST {{base}}/api/v1/transfers/{{transferId}}/execute
# Authorization: Bearer {{viewerToken}}
# HTTP 403
