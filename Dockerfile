FROM python:3.12-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости через pip
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
# Копируем остальные файлы проекта
COPY . .

# Запуск приложения
CMD ["python", "bot.py"]