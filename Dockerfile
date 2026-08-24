# A pinned toolchain for building and testing baffin.
#
# Derivative cache keys are hash(content_hash + spec) — they do NOT include the
# libvips version. Identical keys therefore promise identical *inputs*, not
# identical output bytes: upgrading libvips silently changes what a thumbnail
# looks like without invalidating anything. Pinning the toolchain is what makes
# "all cache hits" mean the same thing twice.
#
# This image is the toolchain only; the project is bind-mounted at /work, so
# editing code does not rebuild the image. Dependencies are baked in, so a
# change to uv.lock does.
#
# Debian 13 (trixie) ships libvips 8.16 and ffmpeg 7.1, the closest stable pair
# to a current Homebrew macOS box. The base is pinned by digest; apt versions
# float within the Debian release, so security point-updates land without
# breaking the build. Bumping the digest is the deliberate act of re-pinning.
FROM python@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a

# libvips-dev      the pyvips thumbnailer
# ffmpeg           video poster frames and clip copies (must be on PATH)
# plantuml         renders the architecture diagrams for `make docs`
# make/git         the entry point, and the version metadata hatch reads
# build-essential  pyvips compiles its cffi API module against libvips headers;
# pkg-config       there is no prebuilt wheel for every platform, so the
# libffi-dev       compiler stays in the image rather than in a build stage.
#                  This is a dev/CI toolchain, not a deployment artifact.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libvips-dev \
        ffmpeg \
        plantuml \
        make \
        git \
        build-essential \
        pkg-config \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Pinned uv, copied rather than pip-installed so it cannot drift with the
# interpreter's site-packages.
COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /usr/local/bin/

# The host's .venv is macOS-native and gets bind-mounted over the project, so
# point uv at an environment outside /work that the container owns.
# HOME and the uv cache live somewhere world-writable so the image also works
# under `--user $(id -u)`, which is what keeps container-written caches from
# landing in the repo as root on a Linux host.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    HOME=/tmp

WORKDIR /work

# Dependencies only: the project itself arrives as a bind mount at run time,
# and `uv run` installs it into the venv — hence the group-writable venv.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-install-project --group dev --group docs --group e2e \
    && chmod -R a+rwX /opt/venv \
    && uv cache clean

# Provenance: `docker run --rm IMAGE` prints the versions it pinned. Reported
# through pyvips because that is the binding baffin actually renders with (the
# `vips` CLI lives in a separate package this image has no use for).
CMD ["sh", "-c", "/opt/venv/bin/python -c \"import pyvips; print('libvips', '.'.join(str(pyvips.version(i)) for i in range(3)))\" && ffmpeg -version | head -1 && uv --version"]
