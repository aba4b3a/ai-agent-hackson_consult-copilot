# Multi-stage: build the Next.js static export in stage 1, then bake the
# static output into a small nginx image. Build context must be the repo
# root (see docs/deploy.md and .github/workflows/deploy.yml).

# ---------- Stage 1: build front ----------
FROM node:24-bookworm AS front-build

WORKDIR /app/front
# Copy manifests first for better layer caching.
COPY front/package.json front/package-lock.json ./
RUN npm ci

# Copy the rest of the front source.
COPY front/ ./

# Ensure the API base URL points to the same origin the browser is already on
# (the ALB). Empty string keeps requests relative — e.g. `/api/v1/...`.
ENV NEXT_PUBLIC_API_BASE_URL=""

RUN npm run build

# ---------- Stage 2: nginx ----------
FROM nginx:1.27-alpine

# Config.
COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf

# Static front assets from Next.js `output: "export"`.
COPY --from=front-build /app/front/out /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
