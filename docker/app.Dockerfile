FROM python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=/opt/venv/bin:${PATH} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN python -m pip install --no-cache-dir "uv==0.11.17"

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY config ./config
COPY migrations ./migrations
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable \
    && groupadd --gid 10001 wikiepwing \
    && useradd --uid 10001 --gid 10001 --create-home \
        --home-dir /home/wikiepwing --shell /usr/sbin/nologin wikiepwing \
    && mkdir --parents \
        /data/sources /data/reference /data/work /data/cache \
        /data/output /data/reports /data/logs \
    && chown --recursive wikiepwing:wikiepwing \
        /data/sources /data/work /data/cache /data/output /data/reports /data/logs \
    && chmod 0555 /data/reference \
    && rm --recursive --force /root/.cache

ENV HOME=/home/wikiepwing

USER 10001:10001

CMD ["wikiepwing", "--help"]
