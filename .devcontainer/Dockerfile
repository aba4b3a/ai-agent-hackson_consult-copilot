FROM mcr.microsoft.com/devcontainers/typescript-node:4-24-bookworm

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    make \
    curl \
    jq \
    unzip \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

USER node

ENV PATH="/home/node/.local/bin:${PATH}"
