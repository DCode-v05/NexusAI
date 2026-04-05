FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml ./
RUN uv sync
COPY src/ src/
EXPOSE 9004
CMD ["uv", "run", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "9004"]
