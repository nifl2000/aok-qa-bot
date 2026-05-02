FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY qa_bot/ qa_bot/
COPY backend/ backend/
COPY input/ input/
COPY .env.example .env

EXPOSE 8000

CMD ["python", "backend/main.py"]
