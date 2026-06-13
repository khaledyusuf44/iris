# Iris on Hugging Face Spaces (Docker): self-contained llama.cpp + Gradio.
# The small MiniCPM GGUF is baked into the image so the model runs entirely
# inside the Space at runtime (no external model API).
#
# Build args let you swap the model without code changes. Defaults target the
# Tiny Titan badge (<=4B params) with reliable upstream llama.cpp support.
ARG GGUF_REPO=openbmb/MiniCPM3-4B-GGUF
ARG GGUF_FILE=minicpm3-4b-q4_k_m.gguf
ARG LLAMA_CPP_TAG=b9616
ARG LLAMA_CPP_ARCHIVE=llama-b9616-bin-ubuntu-x64.tar.gz

# ---------------------------------------------------------------------------
# Stage 1: fetch llama.cpp's prebuilt Ubuntu CPU server binary.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS llama-bin
ARG LLAMA_CPP_TAG
ARG LLAMA_CPP_ARCHIVE

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl tar \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/llama.cpp \
    && curl -L --fail \
        "https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_CPP_TAG}/${LLAMA_CPP_ARCHIVE}" \
        | tar -xz --strip-components=1 -C /opt/llama.cpp \
    && test -x /opt/llama.cpp/llama-server

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
    PATH=/opt/llama.cpp:/home/user/.local/bin:$PATH \
    LD_LIBRARY_PATH=/opt/llama.cpp \
    PYTHONUNBUFFERED=1 \
    IRIS_MODEL_PATH=/models/${GGUF_FILE}

COPY --from=llama-bin /opt/llama.cpp /opt/llama.cpp
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
