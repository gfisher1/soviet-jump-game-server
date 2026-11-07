# Runs the local Soviet Jump Game backend.
#
# NOTE: the game *server* itself is the retail game binary running headless (see
# gameserver/README.md). This image only runs the mock backend service.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV SJG_PUBLIC_HOST=127.0.0.1 \
    SJG_GAME_PORT=42010 \
    SJG_ACCOUNT_GROUP=Administrator

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
