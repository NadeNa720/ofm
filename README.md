# Редактор метаданных медиа

Веб-приложение для изменения метаданных изображений и видео без перекодирования и потери качества. Позволяет заменить информацию об устройстве (например, на iPhone 15/16/17) и записать IP-адрес в метаданные файла.

## Возможности

- Загрузка изображений (JPG, PNG, TIFF, HEIC, WEBP) и видео (MP4, MOV, AVI, MKV, WEBM, 3GP).
- Выбор устройства из пресетов: iPhone 11 / 11 Pro / 11 Pro Max, iPhone 12 / 12 mini / 12 Pro / 12 Pro Max, iPhone 13 / 13 mini / 13 Pro / 13 Pro Max, iPhone 14 / 14 Plus / 14 Pro / 14 Pro Max, iPhone 15 / 15 Plus / 15 Pro / 15 Pro Max, iPhone 16 / 16 Plus / 16 Pro / 16 Pro Max, iPhone 17 / 17 Air / 17 Pro / 17 Pro Max.
- Выбор геолокации из списка популярных городов (Нью-Йорк, Лондон, Париж, Токио и др.) или ручной ввод координат.
- Запись GPS-метаданных: `GPSLatitude`, `GPSLongitude`, `GPSAltitude`, `GPSPosition`, а также IPTC/XMP-полей города, штата и страны.
- Ручной ввод IP-адреса для записи в метаданные.
- Сохранение исходных дат съемки или их обновление.
- Lossless-редактирование: изображение и видеопоток не перекодируются, изменяются только метаданные.
- Предпросмотр загруженного файла и просмотр новых метаданных после обработки.

## Установка

### 1. Установите ExifTool

ExifTool необходим для lossless-редактирования метаданных.

**Windows (рекомендуется — через winget):**
```powershell
winget install OliverBetz.ExifTool
```

**Windows (вручную):**
1. Скачайте ZIP-архив с ExifTool для Windows: https://exiftool.org/
2. Извлеките файл `exiftool(-k).exe` и переименуйте в `exiftool.exe`.
3. Поместите `exiftool.exe` и папку `exiftool_files` в каталог, который добавлен в системную переменную `PATH`, или в корень проекта.

**macOS:**
```bash
brew install exiftool
```

**Linux:**
```bash
sudo apt-get install libimage-exiftool-perl
```

### 2. Установите Python-зависимости

```bash
python -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

**Windows:**
```powershell
.\run.bat
```

**Linux / macOS:**
```bash
chmod +x run.sh
./run.sh
```

Или вручную:

```bash
python -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Откройте в браузере: http://localhost:5000

## Деплой на Railway

Проект уже адаптирован для Railway:

1. Подключите репозиторий GitHub `NadeNa720/ofm` в Railway.
2. Railway автоматически установит Python, зависимости из `requirements.txt` и ExifTool через `nixpacks.toml`.
3. Запуск будет выполнен через `Procfile` (gunicorn).
4. Переменная окружения `PORT` задается Railway автоматически.

Или разверните вручную через CLI:

```bash
railway login
railway link
railway up
```

## Как это работает

- Для изображений приложение записывает EXIF-теги: `Make`, `Model`, `LensModel`, `Software`, `UserComment`, `GPSLatitude`, `GPSLongitude`, `GPSAltitude`, `ColorSpace`, `XResolution`, `YResolution`, `ResolutionUnit`.
- Для видео приложение записывает QuickTime-теги: `Make`, `Model`, `Software`, `Comment`, `UserComment`, `GPSLatitude`, `GPSLongitude`, `GPSAltitude`.
- ExifTool обновляет только метаданные контейнера, не трогая пиксели и видеопоток. Файл перезаписывается в папке `processed/`.

## Структура проекта

```
media-metadata-editor/
├── app.py              # Flask-приложение
├── devices.py          # Пресеты устройств
├── geolocations.py     # База городов и координат
├── requirements.txt    # Зависимости Python
├── Procfile            # Команда запуска для Railway
├── nixpacks.toml       # Системные зависимости (ExifTool) для Railway
├── runtime.txt         # Версия Python для Railway
├── run.bat             # Скрипт запуска для Windows
├── run.sh              # Скрипт запуска для Linux/macOS
├── templates/
│   └── index.html      # Главная страница
├── static/
│   ├── css/style.css   # Стили
│   ├── js/app.js       # Логика фронтенда
│   └── thumbnails/     # Миниатюры превью
├── uploads/            # Временные загруженные файлы
├── processed/          # Готовые файлы с измененными метаданными
└── README.md
```

## Безопасность

- Максимальный размер загружаемого файла: 500 МБ.
- Разрешены только популярные медиа-форматы.
- Имена файлов очищаются перед сохранением.

## Предупреждение

Приложение предназначено для легального редактирования метаданных собственных файлов. Не используйте его для подделки доказательств или обмана третьих лиц.
