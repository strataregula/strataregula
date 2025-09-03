# Strataregula Dockerfile
# シンプルで実用的な開発・本番環境

FROM python:3.10-slim

# システムパッケージのインストール（sudo含む）
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    sudo \
    build-essential \
    # 基本的なLinuxコマンド
    tree \
    htop \
    nano \
    less \
    man \
    # ネットワークツール
    net-tools \
    iputils-ping \
    # ファイルシステムツール
    rsync \
    # その他便利ツール
    jq \
    && rm -rf /var/lib/apt/lists/*


    # ホストユーザーと同じ名前のユーザーを作成
RUN useradd -m -s /bin/bash uraka && \
    echo 'uraka ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# ワークスペースの設定
WORKDIR /workspace
RUN chown uraka:uraka /workspace

# 非rootユーザーに切り替え
USER uraka

# 環境変数の設定
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/home/uraka
ENV PAGER=cat
ENV PS1="$ "
ENV TERM=xterm
ENV PATH=/usr/local/bin:/usr/bin:/bin:$PATH
ENV DOCKER_HOST=unix:///run/user/1000/docker.sock

# ポートの公開
EXPOSE 8000 3000 5000 8080

# 依存関係のインストール
COPY --chown=uraka:uraka pyproject.toml requirements.txt ./
COPY --chown=uraka:uraka strataregula/ ./strataregula/
RUN pip install --upgrade pip && \
    pip install -e ".[dev,test,docs,performance,plugins,api]"

# デフォルトコマンド
CMD ["/bin/bash"]
