#!/usr/bin/env bash
# 전체 환경 셋업 및 실행 스크립트
# 사용법: ./scripts/setup.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Vital Risk API 셋업 ==="

# 1. .env 파일 생성 (.env.example 기반)
if [ ! -f .env ]; then
    echo "[1/5] .env.example → .env 복사"
    cp .env.example .env
    # Docker 내부에서는 docker-compose.yml의 environment가 DATABASE_URL을 덮어쓰므로
    # .env의 DATABASE_URL은 로컬 개발용 기본값 유지
    echo "  ✓ .env 생성 완료 (필요시 수정하세요)"
else
    echo "[1/5] .env 이미 존재 — 건너뜀"
fi

# 2. 기존 컨테이너 정리
echo "[2/5] 기존 컨테이너 정리"
docker compose down --remove-orphans 2>/dev/null || true

# 3. Docker 이미지 빌드
echo "[3/5] Docker 이미지 빌드"
docker compose build --no-cache
echo "  ✓ 이미지 빌드 완료"

# 4. 컨테이너 실행 (alembic upgrade head → uvicorn 순서)
echo "[4/5] 컨테이너 실행"
docker compose up -d

# 5. 앱 컨테이너 헬스 체크 (alembic + uvicorn 기동 대기)
echo "[5/5] API 서버 기동 대기 중..."
MAX_WAIT=60
ELAPSED=0
until curl -sf http://localhost:8000/docs > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "  ✗ ${MAX_WAIT}초 내 서버 미응답 — 로그 확인:"
        docker compose logs app --tail 30
        exit 1
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    printf "  대기 중... (%ds)\r" "$ELAPSED"
done
echo ""
echo "  ✓ API 서버 정상 기동 (${ELAPSED}s)"

# 결과 출력
echo ""
echo "=== 셋업 완료 ==="
echo "  API:     http://localhost:8000"
echo "  Swagger: http://localhost:8000/docs"
echo "  DB:      postgresql://postgres:postgres@localhost:5432/vitalrisk"
echo ""
echo "=== 빠른 테스트 ==="
echo "  curl -H 'Authorization: Bearer \$(grep API_TOKEN .env | cut -d= -f2)' http://localhost:8000/docs"
echo ""
echo "=== 컨테이너 로그 확인 ==="
echo "  docker compose logs -f app"
echo ""
echo "=== 종료 ==="
echo "  docker compose down"
