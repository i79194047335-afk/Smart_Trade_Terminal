# Frontend container (DEV mode) — runs the Vite dev server with hot reload.

# Start from a small official Node 22 image.
FROM node:22-alpine

WORKDIR /app

# Enable pnpm (it ships with Node via corepack but needs to be activated).
RUN corepack enable

# Same caching trick: copy manifests first so the install layer is cached.
COPY package.json pnpm-lock.yaml ./

# Install the exact locked dependency set.
RUN pnpm install --frozen-lockfile

# Copy the rest of the source.
COPY . .

# Vite dev-server port.
EXPOSE 5173

# `--host` makes Vite bind to all interfaces so the port is reachable
# from outside the container (otherwise it only listens on localhost INSIDE).
CMD ["pnpm", "dev", "--host"]
