FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY cortexstate ./cortexstate
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home cortexstate && mkdir /data && chown cortexstate /data
USER cortexstate
EXPOSE 8787
CMD ["cortexstate", "--db", "/data/cortexstate.db", "serve", "--host", "0.0.0.0"]
