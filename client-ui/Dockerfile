FROM python:3.11-slim

WORKDIR /app

# Copy static files
COPY static /app/static

# Expose port
EXPOSE 8080

# Run simple HTTP server
CMD ["python", "-m", "http.server", "8080", "--directory", "static"]

