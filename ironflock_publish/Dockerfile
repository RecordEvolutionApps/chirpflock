# Slim base keeps the image small; these deps ship as pure-Python/wheel builds.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the service runs (avoids pulling unrelated files into the image).
COPY ironflock_publisher.py .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["python", "-u", "ironflock_publisher.py"]
