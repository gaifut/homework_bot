# homework_bot
python telegram bot

## Описание
Телеграм бот для проверки статуса домашнего задания на курсе Yandex.Practicum.
Работает на базе «API сервиса Практикум.Домашка»

## Установка
Для работы бота необходимы:
- Токен от API сервиса Практикум.Домашка
- Токен от бота для телеграм
- ID чата, куда бот будет отправлять сообщения.
Информацию выше необходимо будет сохранить в файл .env в папку с проектом как в примере ниже:
```
PRACTICUM_TOKEN=dsfsfsdf23423423sdsdf32sdf
TELEGRAM_TOKEN=dsfsfsdf2342:3423sdsdf32sdf
TELEGRAM_CHAT_ID=23423sdfsf
```

1. Склонируйте репозиторий ```git clone git@github.com:gaifut/homework_bot.git```
2. Установите виртуальное окружение и зависимости.
```
# Для Linux/MacOS
python3 -m venv venv

# Для Windows
python -m venv venv

# Активируйте виртуальное окружение:
source venv/bin/activate

# Обновите pip
python -m pip install --upgrade pip 

# Установите зависимости
pip install -r requirements.txt
```
3. Запустите проект. В папке с проектом в терминале наберите: ```python homework.py```
