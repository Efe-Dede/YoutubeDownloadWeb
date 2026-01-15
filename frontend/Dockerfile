# Frontend Dockerfile - Nginx Alpine
FROM nginx:alpine

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy static files
COPY index.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY entrypoint.sh /entrypoint.sh

# Create directories for nginx and set permissions
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R appuser:appgroup /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    # Make nginx.pid writable
    touch /var/run/nginx.pid && \
    # Fix potentially Windows line endings
    sed -i 's/\r$//' /entrypoint.sh && \
    chown appuser:appgroup /var/run/nginx.pid /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Environment
ENV PORT=8080

# Expose port
EXPOSE ${PORT}

# Health check - updated to use the correct port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

# Switch to non-root user
USER appuser

# Run entrypoint script then nginx
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
