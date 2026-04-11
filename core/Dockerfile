FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/root \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1

# Base system packages — no VNC, no desktop, no browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    wget \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    locales \
    gnupg \
    lsb-release \
    && locale-gen en_US.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# HashiCorp Vault CLI (for org overlay vault.env support)
RUN wget -O- https://apt.releases.hashicorp.com/gpg \
      | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
      https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
      | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y --no-install-recommends vault && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Python dependencies — install before copying app code for layer caching
COPY api/requirements.txt /tmp/api-requirements.txt
COPY mcp/requirements.txt /tmp/mcp-requirements.txt
RUN pip3 install --no-cache-dir \
    -r /tmp/api-requirements.txt \
    -r /tmp/mcp-requirements.txt

# Directory structure
RUN mkdir -p \
    /etc/supervisor/conf.d \
    /var/log/supervisor \
    /sandbox/modules/enabled \
    /opt/sandbox/api \
    /opt/sandbox/mcp

# supervisord
COPY supervisord/supervisord.conf /etc/supervisor/supervisord.conf
COPY supervisord/conf.d/           /etc/supervisor/conf.d/

# nginx
COPY nginx/nginx.conf              /etc/nginx/nginx.conf
COPY nginx/conf.d/default.conf     /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Application code
COPY api/ /opt/sandbox/api/
COPY mcp/ /opt/sandbox/mcp/

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# REST API + MCP direct ports, nginx on 8080
EXPOSE 8080 8079 8091

ENTRYPOINT ["/entrypoint.sh"]
