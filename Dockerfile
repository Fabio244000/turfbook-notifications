FROM python:3.12-slim

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/local.txt

COPY . .

CMD ["uvicorn", "app.user_notification.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
