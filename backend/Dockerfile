# FastAPI 백엔드. uv.lock 그대로 설치한다(paddlepaddle 은 pyproject 의 paddle-cpu 인덱스에서 aarch64 휠).
FROM python:3.13-slim-bookworm

# paddle/opencv 런타임 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv UV_LINK_MODE=copy UV_PYTHON=/usr/local/bin/python3
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .

# 업로드·OCR 모델은 볼륨(compose 참고). PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK 는 ocr.py 가 설정한다.
ENV PYTHONUNBUFFERED=1 HOME=/root
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
