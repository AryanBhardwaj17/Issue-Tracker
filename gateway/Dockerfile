FROM nginx:1.27-alpine

# Remove default site
RUN rm /etc/nginx/conf.d/default.conf

# Production config (overridden via volume mount in dev)
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY cors.conf /etc/nginx/cors.conf

EXPOSE 80
