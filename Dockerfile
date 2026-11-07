FROM python:3.12-slim
WORKDIR /srv
RUN useradd -m appuser
COPY pyproject.toml .python-version ./
RUN pip install --no-cache-dir "fastapi>=0.115,<1" "uvicorn>=0.30,<1" "pydantic>=2,<3" "httpx>=0.27,<1"
COPY app ./app
RUN mkdir /srv/data && chown -R appuser:appuser /srv/data
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
