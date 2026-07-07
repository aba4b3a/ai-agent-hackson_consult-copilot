FROM node:24-bookworm

# Browser system dependencies for Playwright Chromium in compose-based E2E.
# The browser binary itself is installed into a named volume by `make test`.
RUN npx --yes playwright@1.60.0 install-deps chromium
