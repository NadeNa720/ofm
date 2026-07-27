@echo off
chcp 65001 >nul
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Установка зависимостей...
venv\Scripts\pip install -r requirements.txt

echo Запуск приложения...
venv\Scripts\python app.py
