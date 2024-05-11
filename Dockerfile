FROM python:3.11.5-slim-bookworm
WORKDIR /lemonapi
COPY pyproject.toml
RUN poetry install
EXPOSE 5001
COPY . .
CMD uvicorn lemonapi.main:app --host=0.0.0.0 --port=5001 --log-level=info
