FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Build-time env var — Next.js bakes NEXT_PUBLIC_* into the JS bundle at build time.
# Pass via --build-arg NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1 in CI/CD.
# Falls back to empty string so local `npm run build` still works unchanged.
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN adduser --disabled-password --no-create-home appuser

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER appuser

EXPOSE 3000
CMD ["node", "server.js"]
