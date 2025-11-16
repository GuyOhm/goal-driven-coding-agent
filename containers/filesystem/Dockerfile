FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini git bash && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install .

ENV SANDBOX_ROOT=/sandbox \
    TRANSPORT=streamable-http \
    HOST=0.0.0.0 \
    PORT=7101 \
    LOG_LEVEL=INFO

VOLUME ["/sandbox"]
EXPOSE 7101

ENTRYPOINT ["tini", "--", "python", "-m", "goal_driven_coding_agent.mcp.servers.filesystem_server"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "7101"]

