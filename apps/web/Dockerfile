FROM node:22.19.0-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --ignore-scripts

FROM node:22.19.0-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_NEXUS_API_URL
ARG NEXT_PUBLIC_NEXUS_DEV_AUTH=true
ENV NEXT_PUBLIC_NEXUS_API_URL=${NEXT_PUBLIC_NEXUS_API_URL}
ENV NEXT_PUBLIC_NEXUS_DEV_AUTH=${NEXT_PUBLIC_NEXUS_DEV_AUTH}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22.19.0-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S nexus && adduser -S nexus -G nexus
COPY --from=builder --chown=nexus:nexus /app/public ./public
COPY --from=builder --chown=nexus:nexus /app/.next/standalone ./
COPY --from=builder --chown=nexus:nexus /app/.next/static ./.next/static
USER nexus
EXPOSE 3000
CMD ["node", "server.js"]
