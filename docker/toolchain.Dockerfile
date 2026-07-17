FROM debian:bookworm-slim@sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df AS eb-builder

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC

# A dated signed Debian snapshot keeps build dependencies from drifting while
# the image digest fixes the initial filesystem and architecture selection.
RUN printf '%s\n' \
        'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20260701T000000Z bookworm main' \
        'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20260701T000000Z bookworm-security main' \
        > /etc/apt/sources.list \
    && rm --force /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install --yes --no-install-recommends \
        build-essential=12.9 \
        bzip2=1.0.8-5+b1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        patch=2.7.6-7 \
        perl=5.36.0-7+deb12u3 \
        zlib1g-dev=1:1.2.13.dfsg-1 \
    && rm --recursive --force /var/lib/apt/lists/*

COPY docker/toolchain /tmp/toolchain
COPY patches/eb /tmp/patches/eb
COPY patches/freepwing /tmp/patches/freepwing

RUN /tmp/toolchain/build-eb.sh
RUN /tmp/toolchain/build-freepwing.sh

FROM python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b AS eb-runtime

LABEL org.opencontainers.image.title="wikiepwing EB toolchain" \
    org.opencontainers.image.version="4.4.3" \
    org.opencontainers.image.source="https://github.com/mistydemeo/eb" \
    io.wikiepwing.eb.source.sha256="abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f" \
    io.wikiepwing.freepwing.version="1.6.1" \
    io.wikiepwing.freepwing.source.sha256="274a8cf392e2c46662bcf3eedce331fe84e65f7e5e6044d0178b2150a0704fc2"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LD_LIBRARY_PATH=/opt/eb/lib \
    PATH=/opt/venv/bin:/opt/freepwing/bin:/opt/eb/bin:${PATH} \
    PERL5LIB=/opt/freepwing/lib/perl5 \
    TZ=UTC \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=eb-builder /opt/eb /opt/eb
COPY --from=eb-builder /opt/freepwing /opt/freepwing
COPY docker/toolchain/version.sh /usr/local/bin/toolchain-version

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY config ./config
COPY migrations ./migrations
COPY src ./src

RUN printf '%s\n' \
        'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20260701T000000Z bookworm main' \
        'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20260701T000000Z bookworm-security main' \
        > /etc/apt/sources.list \
    && rm --force /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install --yes --no-install-recommends \
        fonts-noto-cjk=1:20220127+repack1-1 \
        imagemagick=8:6.9.11.60+dfsg-1.6+deb12u9 \
        libjson-xs-perl=4.040-1~deb12u1 \
        librsvg2-bin=2.54.7+dfsg-1~deb12u1 \
        make=4.3-4.1 \
        perl=5.36.0-7+deb12u3 \
        zip=3.0-13 \
    && rm --recursive --force /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir "uv==0.11.17" \
    && uv sync --frozen --no-dev --no-editable \
    && groupadd --gid 10001 wikiepwing \
    && useradd --uid 10001 --gid 10001 --create-home \
        --home-dir /home/wikiepwing --shell /usr/sbin/nologin wikiepwing \
    && mkdir --parents /data/reference /data/work /data/reports \
    && chown --recursive wikiepwing:wikiepwing /data/work /data/reports \
    && chmod 0555 /data/reference /usr/local/bin/toolchain-version \
    && /usr/local/bin/toolchain-version

# Overwrites imagemagick's own default policy.xml (installed above) with a
# locked-down one -- must run after the apt-get install, or dpkg's unpack
# would just replace this file with its own default again.
COPY docker/toolchain/imagemagick-policy.xml /etc/ImageMagick-6/policy.xml

USER 10001:10001

CMD ["toolchain-version"]
