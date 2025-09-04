# Strataregula Dockerfile
# 権限問題を解決した開発環境

FROM python:3.11-slim

# ビルド引数でホストのUID/GIDを受け取る
ARG UID=1000
ARG GID=1000

# システムパッケージのインストール
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

# ホストと同じUID/GIDでユーザーを作成
RUN groupadd -g $GID uraka && \
    useradd -m -u $UID -g $GID -s /bin/bash uraka && \
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
# Cursor Agent最適化
ENV HTTP_PROXY=
ENV HTTPS_PROXY=
ENV NO_PROXY=localhost,127.0.0.1
ENV CURL_TIMEOUT=30
ENV PYTHONIOENCODING=utf-8

# ポートの公開
EXPOSE 8000 3000 5000 8080

# 依存関係のインストール
COPY --chown=uraka:uraka pyproject.toml requirements.txt ./
COPY --chown=uraka:uraka strataregula/ ./strataregula/
RUN pip install --upgrade pip && \
    pip install -e ".[dev,test,docs,performance,plugins,api]"

# Git設定の事前設定
USER root
RUN git config --global --add safe.directory /workspace && \
    git config --global init.defaultBranch main && \
    git config --global pull.rebase false

# SSH権限の修正（起動時に実行）
USER root
RUN echo '#!/bin/bash\n\
    # SSH権限の修正\n\
    if [ -d /home/uraka/.ssh ]; then\n\
    chmod 700 /home/uraka/.ssh\n\
    chmod 600 /home/uraka/.ssh/* 2>/dev/null || true\n\
    chown -R uraka:uraka /home/uraka/.ssh\n\
    fi\n\
    # Cursor Agent最適化\n\
    export PAGER=cat\n\
    export PS1="$ "\n\
    export TERM=xterm\n\
    export PYTHONUNBUFFERED=1\n\
    export PYTHONDONTWRITEBYTECODE=1\n\
    export PYTHONIOENCODING=utf-8\n\
    # ネットワーク最適化\n\
    export HTTP_PROXY=\n\
    export HTTPS_PROXY=\n\
    export NO_PROXY=localhost,127.0.0.1\n\
    # bashrcに永続化\n\
    echo "export PS1=\"$ \"" >> /home/uraka/.bashrc\n\
    echo "export PAGER=cat" >> /home/uraka/.bashrc\n\
    echo "export TERM=xterm" >> /home/uraka/.bashrc\n\
    # Git設定の永続化\n\
    git config --global --add safe.directory /workspace\n\
    exec "$@"' > /usr/local/bin/fix-ssh-perms.sh && \
    chmod +x /usr/local/bin/fix-ssh-perms.sh

# 非rootユーザーに戻す
USER uraka

# デフォルトコマンド
CMD ["/usr/local/bin/fix-ssh-perms.sh", "/bin/bash"]