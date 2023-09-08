# Используем базовый образ Python с установленным Python 3.8
FROM python:3.8

# Установка зависимостей Flask и других библиотек
RUN pip install Flask pymongo flask_restful flask_jwt_extended pandas

# Создание каталога приложения в контейнере
WORKDIR /app

# Копирование всех файлов приложения в контейнер
COPY . /app

# Установка переменной окружения для Flask, чтобы указать, что мы находимся в production-режиме
ENV FLASK_ENV=production

# Определение порта, на котором будет работать приложение (по умолчанию Flask работает на порту 5000)
EXPOSE 5000

# Запуск Flask-приложения при запуске контейнера
CMD ["python", "app.py"]