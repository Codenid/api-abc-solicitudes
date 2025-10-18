FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --no-deps -r requirements.txt

COPY ./src ./src

EXPOSE 8101

CMD ["uvicorn", "src.api_abc_solicitudes.main:app", "--host", "0.0.0.0", "--port", "8101"]