# Contexto de construcción: la raíz del repositorio. Las versiones de Python y de
# uv son argumentos sin valor por defecto; salen de mise.toml (`mise current`) y
# las pasan runner/local.py y runner/worker/cloudflare.config.ts.
#   docker build -f runner/Dockerfile -t qg-runner \
#     --build-arg PYTHON_VERSION=$(mise current python) \
#     --build-arg UV_VERSION=$(mise current uv) .
ARG PYTHON_VERSION
ARG UV_VERSION

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

# Las versiones salen de uv.lock, grupo `runner` de pyproject.toml. El sistema de
# archivos es de solo lectura en ejecución, así que el bytecode se compila aquí.
COPY pyproject.toml uv.lock /tmp/lock/
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    uv export --project /tmp/lock --frozen --no-emit-project --no-default-groups \
        --only-group runner -o /tmp/requirements.txt \
 && uv pip install --system --no-cache --compile-bytecode --require-hashes -r /tmp/requirements.txt \
 && rm -r /tmp/lock /tmp/requirements.txt

COPY runner/ /app/
COPY qgcheck/ /app/qgcheck/
COPY exercises/ /app/exercises/
RUN python -m compileall -q /app/qgcheck /app/grader

# Nada es escribible por el alumno salvo su directorio de trabajo en /scratch.
RUN mkdir /scratch && chmod 755 /scratch /tmp /var/tmp /app

WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "/app/server.py"]
