FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HOME=/root

# System packages only — Python already in base image
# Vault is NOT here: org overlay installs it via org/scripts/install-vault.sh
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    wget \
    git \
    ca-certificates \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python dependencies — layer-cached before app code
COPY api/requirements.txt /tmp/api-requirements.txt
COPY mcp/requirements.txt /tmp/mcp-requirements.txt
RUN pip install --no-cache-dir \
    -r /tmp/api-requirements.txt \
    -r /tmp/mcp-requirements.txt

# Directory structure
RUN mkdir -p \
    /etc/supervisor/conf.d \
    /var/log/supervisor \
    /sandbox/modules/enabled \
    /opt/sandbox/api \
    /opt/sandbox/mcp \
    /root/.local/bin

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

EXPOSE 8080 8079 8091

ENTRYPOINT ["/entrypoint.sh"]
