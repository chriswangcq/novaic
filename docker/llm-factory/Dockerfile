FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 19990

CMD ["python", "-m", "uvicorn", "factory.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "19990", "--log-level", "info"]
