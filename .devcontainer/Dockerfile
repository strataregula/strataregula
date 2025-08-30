ARG VARIANT=3.11
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

# 基本的な開発ツールのインストール
RUN apt-get update && apt-get install -y \
    git \
    bash-completion \
    less \
    jq \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python開発環境のセットアップ
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir uv ruff black isort pytest pytest-cov