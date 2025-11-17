FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

COPY . .

CMD ["/wait-for-db.sh", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]