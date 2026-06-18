# Use a Python base image (adjust version as needed)
FROM python:3.12

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY * .

CMD ["python", "-u", "ironflock_publisher.py"]