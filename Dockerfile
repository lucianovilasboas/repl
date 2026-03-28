# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

ENV RPN_DATABASE_URL="sqlite+aiosqlite:///./data/rpn_api.db"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
