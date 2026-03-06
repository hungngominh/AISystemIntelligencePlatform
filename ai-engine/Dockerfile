FROM python:3.12-slim

WORKDIR /app

# Install dependencies trước để cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Tạo thư mục data
RUN mkdir -p data

EXPOSE 8765

CMD ["python", "main.py"]
