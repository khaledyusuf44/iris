#!/usr/bin/env bash
# Hugging Face Space entrypoint: start the local llama.cpp model server, wait
# for it to become healthy, wire the IRIS_* env vars to it, then launch Gradio.
set -euo pipefail

MODEL_PATH="${IRIS_MODEL_PATH:-/models/minicpm3-4b-q4_k_m.gguf}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LLAMA_CTX="${LLAMA_CTX:-8192}"
LLAMA_THREADS="${LLAMA_THREADS:-$(nproc)}"

echo "[iris] starting llama-server with ${MODEL_PATH} on :${LLAMA_PORT}"
llama-server \
    --model "${MODEL_PATH}" \
    --host 127.0.0.1 \
    --port "${LLAMA_PORT}" \
    --ctx-size "${LLAMA_CTX}" \
    --threads "${LLAMA_THREADS}" \
    --jinja \
    --no-warmup &
LLAMA_PID=$!

# Stop the model server if the container is asked to shut down.
trap 'kill "${LLAMA_PID}" 2>/dev/null || true' EXIT INT TERM

echo "[iris] waiting for model server health..."
for _ in $(seq 1 150); do
    if curl -sf "http://127.0.0.1:${LLAMA_PORT}/health" >/dev/null 2>&1; then
        echo "[iris] model server is healthy"
        break
    fi
    if ! kill -0 "${LLAMA_PID}" 2>/dev/null; then
        echo "[iris] llama-server exited before becoming healthy" >&2
        exit 1
    fi
    sleep 2
done

# Point the Iris engine at the local server. llama-server ignores the OpenAI
# "model" field and serves the loaded GGUF regardless, so IRIS_MODEL is nominal.
export IRIS_API_BASE_URL="http://127.0.0.1:${LLAMA_PORT}/v1"
export IRIS_MODEL="${IRIS_MODEL:-local-minicpm}"
export IRIS_API_KEY="${IRIS_API_KEY:-not-needed}"
# MiniCPM3-4B is not a /think model; keep thinking off unless overridden.
export IRIS_ENABLE_THINKING="${IRIS_ENABLE_THINKING:-0}"

# Gradio reads these to bind the public Space port.
export GRADIO_SERVER_NAME="${GRADIO_SERVER_NAME:-0.0.0.0}"
export GRADIO_SERVER_PORT="${GRADIO_SERVER_PORT:-7860}"

echo "[iris] launching Gradio app"
exec python3 app.py
