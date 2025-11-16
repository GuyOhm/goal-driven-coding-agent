FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini git bash build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install . \
    && pip install "pytest>=8.3.3"

ENV SANDBOX_ROOT=/sandbox \
    TRANSPORT=streamable-http \
    HOST=0.0.0.0 \
    PORT=7102 \
    LOG_LEVEL=INFO \
    PYTHON_BINARY=python \
    TIMEOUT_SECONDS=300

VOLUME ["/sandbox"]
EXPOSE 7102

ENTRYPOINT ["tini", "--", "python", "-m", "goal_driven_coding_agent.mcp.servers.executor_server"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "7102", "--timeout-seconds", "300"]
