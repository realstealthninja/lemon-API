FROM python:3.11.5-slim-bookworm

RUN pip install poetry==1.8.2

ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /lemonapi

COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

EXPOSE 5001

COPY . .
RUN poetry install --without dev

ENTRYPOINT ["poetry"]

CMD ["run", "python", "-m", "uvicorn", "lemonapi.main:app", "--host=0.0.0.0", "--port=5001", "--log-level=info"]
