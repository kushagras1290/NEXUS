FROM node:22.19.0-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --ignore-scripts

FROM node:22.19.0-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_NEXUS_API_URL
ENV NEXT_PUBLIC_NEXUS_API_URL=${NEXT_PUBLIC_NEXUS_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22.19.0-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S nexus && adduser -S nexus -G nexus
COPY --from=builder --chown=nexus:nexus /app/.next ./.next
COPY --from=builder --chown=nexus:nexus /app/public ./public
COPY --from=builder --chown=nexus:nexus /app/package.json ./package.json
COPY --from=builder --chown=nexus:nexus /app/node_modules ./node_modules
USER nexus
EXPOSE 3000
CMD ["npm", "start"]
