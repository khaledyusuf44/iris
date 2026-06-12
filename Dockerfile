# Iris on Hugging Face Spaces (Docker): self-contained llama.cpp + Gradio.
# The small MiniCPM GGUF is baked into the image so the model runs entirely
# inside the Space at runtime (no external model API).
#
# Build args let you swap the model without code changes. Defaults target the
# Tiny Titan badge (<=4B params) with reliable upstream llama.cpp support.
ARG GGUF_REPO=openbmb/MiniCPM3-4B-GGUF
ARG GGUF_FILE=minicpm3-4b-q4_k_m.gguf

# ---------------------------------------------------------------------------
# Stage 1: build llama.cpp's llama-server (static-linked, generic CPU build).
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS llama-build

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential cmake libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp /src/llama.cpp
WORKDIR /src/llama.cpp

# GGML_NATIVE=OFF keeps the binary portable across HF build/runtime CPUs
# (native autovectorization can emit instructions the runtime CPU lacks).
RUN cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DLLAMA_CURL=ON \
        -DGGML_NATIVE=OFF \
        -DBUILD_SHARED_LIBS=OFF \
    && cmake --build build --config Release -j "$(nproc)" --target llama-server

# ---------------------------------------------------------------------------
# Stage 2: download the GGUF once, at build time, into the image.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS model-fetch
ARG GGUF_REPO
ARG GGUF_FILE

RUN pip install --no-cache-dir "huggingface_hub>=0.23"
RUN python3 -c "from huggingface_hub import hf_hub_download; \
hf_hub_download(repo_id='${GGUF_REPO}', filename='${GGUF_FILE}', local_dir='/models')"

# ---------------------------------------------------------------------------
# Stage 3: runtime image.
# ---------------------------------------------------------------------------
FROM python:3.11-slim
ARG GGUF_FILE

# libcurl4 / libgomp1 are needed by the llama-server binary at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcurl4 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces run the container as uid 1000.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    IRIS_MODEL_PATH=/models/${GGUF_FILE}

COPY --from=llama-build /src/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
COPY --from=model-fetch /models /models

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN python scripts/patch_gradio_templates.py \
    && chmod +x /app/scripts/space_entrypoint.sh \
    && chown -R user:user /app /models

USER user
EXPOSE 7860
ENTRYPOINT ["/app/scripts/space_entrypoint.sh"]
