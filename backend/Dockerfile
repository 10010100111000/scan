# 使用官方 Python 3.9 轻量版作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 1. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # 将 Go 的 bin 目录加入 PATH，确保能直接运行 subfinder 等命令
    PATH="/root/go/bin:${PATH}"

# 2. 安装系统依赖和安全工具
#    - nmap: 端口扫描
#    - wget, git, gcc: 用于安装 Go 和编译依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    nmap \
    wget \
    git \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. 安装 Go 语言环境 (用于安装 ProjectDiscovery 工具)
RUN wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz && \
    rm go1.21.6.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

# 4. 安装 ProjectDiscovery 工具 (Subfinder, httpx, Nuclei)
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# 5. 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 复制项目代码
COPY . .

# 默认启动命令 (会被 docker-compose 覆盖)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]