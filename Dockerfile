# Stage 1: Build dependencies and compile C++ extensions
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python compilation tools
RUN python -m pip install --upgrade pip setuptools wheel

# Copy requirements list
COPY requirements.txt .

# Pre-compile llama-cpp-python and other requirements into wheels
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final lightweight image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (e.g. system dependencies for PyQt/tests if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libegl1 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled wheels from stage 1
COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache-dir /app/wheels/* && rm -rf /app/wheels

# Copy application files (excluding virtual envs and DBs via .dockerignore)
COPY . .

# Set default env configs
ENV MODEL_DIR=models
ENV CHROMA_DB_DIR=chroma_db
ENV EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
ENV LLM_TEMPERATURE=0.1
ENV LLM_MAX_TOKENS=1000
ENV LLM_N_CTX=4096

# Run test suites by default
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
