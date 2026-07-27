#!/usr/bin/env bash
set -e

if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

echo "Установка зависимостей..."
venv/bin/pip install -r requirements.txt

echo "Запуск приложения..."
venv/bin/python app.py
