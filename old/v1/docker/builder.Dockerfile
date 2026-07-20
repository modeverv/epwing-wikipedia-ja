# Build this image through `make build-image`, which first builds the pinned
# legacy toolchain image declared in docker/toolchain.Dockerfile.
FROM wikiepwing-toolchain:1.0.0

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy VIRTUAL_ENV=/opt/venv PATH=/opt/venv/bin:$PATH

RUN mkdir --parents /opt/venv \
    && chown --recursive wikiepwing:wikiepwing /opt/venv

WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN pip install --no-cache-dir uv==0.7.13 \
    && uv sync --frozen --active \
    && chown --recursive wikiepwing:wikiepwing /opt/venv

USER wikiepwing
CMD ["wikiepwing", "doctor"]
