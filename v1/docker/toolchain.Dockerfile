FROM python:3.12.11-slim-bookworm

ARG FREEPWING_VERSION=1.5
ARG FREEPWING_URL=https://deb.debian.org/debian/pool/main/f/freepwing/freepwing_1.5.orig.tar.gz
ARG FREEPWING_SHA256=51e3acf62c9c634c049116e99f02185143a81e4da0971896d48ea84fcffa5dd8
ARG EB_VERSION=4.4.3
ARG EB_URL=https://github.com/mistydemeo/eb/releases/download/v4.4.3/eb-4.4.3.tar.bz2
ARG EB_SHA256=abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential ca-certificates curl perl bzip2 zip zlib1g-dev fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/toolchain
COPY patches /tmp/patches
RUN curl --fail --location --silent --show-error --output freepwing.tar.gz "$FREEPWING_URL" \
    && echo "$FREEPWING_SHA256  freepwing.tar.gz" | sha256sum --check --strict \
    && tar --extract --gzip --file freepwing.tar.gz \
    && cd "freepwing-${FREEPWING_VERSION}.orig" \
    && ./configure --prefix=/opt/freepwing --libexecdir=/opt/freepwing/libexec \
    && make \
    && make install \
    && rm -rf /tmp/toolchain

WORKDIR /tmp/toolchain
RUN curl --fail --location --silent --show-error --output eb.tar.bz2 "$EB_URL" \
    && echo "$EB_SHA256  eb.tar.bz2" | sha256sum --check --strict \
    && tar --extract --bzip2 --file eb.tar.bz2 \
    && cd "eb-${EB_VERSION}" \
    && patch --strip=1 < /tmp/patches/eb-4.4.3-aarch64-config.patch \
    && ./configure --build="$(gcc -dumpmachine)" --prefix=/opt/eb \
    && make \
    && make install \
    && rm -rf /tmp/toolchain

ENV PATH=/opt/freepwing/bin:/opt/eb/bin:$PATH

RUN groupadd --gid 10001 wikiepwing \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin wikiepwing \
    && mkdir --parents /data /output /reports /workspace \
    && chown --recursive wikiepwing:wikiepwing /data /output /reports /workspace
