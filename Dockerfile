# Образ python:3.12-slim — минимальный, ~120 МБ.
FROM python:3.12-slim

# Все команды выполняются в /app внутри контейнера
WORKDIR /app

# Переменные окружения:
#   PYTHONDONTWRITEBYTECODE — не создавать .pyc-файлы внутри контейнера
#   PYTHONUNBUFFERED        — сразу выводить print() в stdout (важно для docker logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Сначала копируем только requirements.txt — так Docker кэширует слой с pip install.
# При изменении кода не придётся переустанавливать пакеты.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем код и конфиги
COPY lab2/ ./lab2/
COPY tests/ ./tests/
COPY main_cli.py .
COPY conftest.py .

# Команда по умолчанию — запуск консольного приложения
CMD ["python", "main_cli.py"]