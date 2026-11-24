# Soviet Jump Game - server, ONE image with two roles:
#
#   * sjg-api         the FastAPI backend ("mock SovietAPI" + live server registry)
#   * sjg-gameserver  the retail game itself run headless under Wine (the gameplay server)
#
# The role is chosen at run time (see docker/docker-compose.yml):
#
#   backend:     uvicorn app.main:app --host 0.0.0.0 --port 8080
#   gameserver:  /usr/local/bin/sjg-gameserver
#
# NO GAME CODE IS SHIPPED. The gameserver role needs your own legally-purchased
# copy of the game mounted at /game (see the wiki -> Deployment).
#
# The base already provides wine, xvfb-run and winetricks (Ubuntu 24.04).
FROM scottyhardy/docker-wine:latest

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WINEPREFIX=/wine \
    WINEDEBUG=-all \
    WINEDLLOVERRIDES=winhttp=n,b \
    SJG_GAME_DIR=/game \
    SJG_GAME_PORT=42010

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3-venv ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/venv

ENV PATH=/opt/venv/bin:${PATH}

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app /app/app

# The headless launcher (and the repo's own helper, kept for parity).
COPY docker/sjg-gameserver /usr/local/bin/sjg-gameserver
COPY gameserver/run-headless.sh /usr/local/bin/sjg-run-headless
RUN chmod +x /usr/local/bin/sjg-gameserver /usr/local/bin/sjg-run-headless

EXPOSE 8080/tcp
EXPOSE 42010/udp

# Default role: the backend.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
