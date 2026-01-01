# 使用官方 Python 3.9 轻量版作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 1. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- [国内加速] 1. 替换 Debian 系统源为阿里云镜像源 (加速 apt install nmap) ---
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 2. 安装系统基础依赖
#    - nmap: 端口扫描核心
#    - wget, curl, unzip: 用于下载和解压工具
RUN apt-get update && apt-get install -y \
    nmap \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 3. 极速安装 ProjectDiscovery 工具 (使用 GitHub 代理加速下载)
#    自动检测架构 (amd64 或 arm64) 并下载对应版本
#    使用了 https://mirror.ghproxy.com/ 进行加速
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then pd_arch="amd64"; else pd_arch="arm64"; fi && \
    echo "Detected architecture: $pd_arch" && \
    \
    # --- Subfinder ---
    echo "Installing Subfinder..." && \
    wget -q https://mirror.ghproxy.com/https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_${pd_arch}.zip && \
    unzip -q subfinder_2.6.6_linux_${pd_arch}.zip && \
    mv subfinder /usr/local/bin/ && \
    rm subfinder_2.6.6_linux_${pd_arch}.zip && \
    \
    # --- httpx ---
    echo "Installing httpx..." && \
    wget -q https://mirror.ghproxy.com/https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_linux_${pd_arch}.zip && \
    unzip -q httpx_1.6.0_linux_${pd_arch}.zip && \
    mv httpx /usr/local/bin/ && \
    rm httpx_1.6.0_linux_${pd_arch}.zip && \
    \
    # --- Nuclei ---
    echo "Installing Nuclei..." && \
    wget -q https://mirror.ghproxy.com/https://github.com/projectdiscovery/nuclei/releases/download/v3.2.0/nuclei_3.2.0_linux_${pd_arch}.zip && \
    unzip -q nuclei_3.2.0_linux_${pd_arch}.zip && \
    mv nuclei /usr/local/bin/ && \
    rm nuclei_3.2.0_linux_${pd_arch}.zip

# 4. 安装 Python 依赖 (使用清华源加速)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 复制项目代码
COPY . .

# 6. 默认启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]