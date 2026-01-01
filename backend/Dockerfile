# 使用明确发行版的 slim（非常关键）
FROM python:3.10-slim-bookworm

WORKDIR /app

# Python 运行环境
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 强制 apt 使用 IPv4，避免国内网络卡死
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

# === 使用国内 Debian 源（slim 正确方式）===
RUN rm -f /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list

# === 安装系统依赖（nmap 国内源）===
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    wget \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# === 安装 ProjectDiscovery 官方预编译二进制（不编译 Go）===
RUN set -eux; \
    ARCH="$(dpkg --print-architecture)"; \
    if [ "$ARCH" = "amd64" ]; then PD_ARCH="amd64"; else PD_ARCH="arm64"; fi; \
    echo "Using arch: $PD_ARCH"; \
    \
    wget https://gh-proxy.org/https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_${PD_ARCH}.zip; \
    unzip -jq subfinder_2.6.6_linux_${PD_ARCH}.zip subfinder; \
    mv subfinder /usr/local/bin/; \
    \
    wget https://gh-proxy.org/https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_linux_${PD_ARCH}.zip; \
    unzip -jq httpx_1.6.0_linux_${PD_ARCH}.zip httpx; \
    mv httpx /usr/local/bin/; \
    \
    wget https://gh-proxy.org/https://github.com/projectdiscovery/nuclei/releases/download/v3.2.0/nuclei_3.2.0_linux_${PD_ARCH}.zip; \
    unzip -jq nuclei_3.2.0_linux_${PD_ARCH}.zip nuclei; \
    mv nuclei /usr/local/bin/; \
    \
    chmod +x /usr/local/bin/*; \
    rm -f *.zip




# === Python 依赖（清华源）===
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# === 复制代码（最后一步，方便调试）===
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
