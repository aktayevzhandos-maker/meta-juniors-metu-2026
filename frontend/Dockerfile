# Build frontend assets with npm ci && npm run build before building this image.
# Reuses the existing Python image; no extra runtime dependency or network download.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY dist/ /app/dist/
COPY serve.py /app/serve.py
USER 10001:10001
EXPOSE 8080
CMD ["python", "serve.py"]
