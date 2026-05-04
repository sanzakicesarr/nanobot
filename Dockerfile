FROM python:3.12-slim
WORKDIR /app
COPY config.py bot.py ./
RUN chmod 644 config.py && useradd -m -u 1001 nanobot
USER nanobot
CMD ["python3", "bot.py"]
