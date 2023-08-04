FROM python:3.10
WORKDIR /lemonapi
COPY requirements.txt requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt
EXPOSE 5001
COPY . .
CMD ["uvicorn", "lemonapi.main:app", "--host=0.0.0.0", "--port=5001", "--log-level=info"]