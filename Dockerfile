FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=3847

EXPOSE 3847

CMD ["gunicorn", "--bind", "0.0.0.0:3847", "--workers", "2", "--timeout", "30", "app:app"]
