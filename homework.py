from http import HTTPStatus
import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPStatusNotOkError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s'
        '- %(lineno)d - %(funcName)s - %(message)s'
    ))
logger.addHandler(handler)


def check_tokens():
    """Проверяет наличие переменных окружения."""
    variables_to_check = (
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID'
    )
    variables_missing = [
        variable for variable in variables_to_check if not globals()[variable]
    ]
    if variables_missing:
        logger.critical(
            'Отустствуют обязательные переменные окружения:'
            f'{", ".join(variables_missing)}'
        )
        sys.exit(1)


def send_message(bot, message):
    """Отправляет сообщение в Телеграм чат."""
    logger.debug('Сообщение успешно отправлено в Телеграм.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logger.error(f'Сообщение не отправлено: {error}', exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту, используя временную метку."""
    payload = {'from_date': timestamp}
    logger.debug(
        f'Начало запроса к API по адресу: {ENDPOINT} с параметром: {payload}'
    )
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException:
        raise ConnectionError(
            f'Ошибка при запросе к API по адресу: {ENDPOINT}.'
        )
    if response.status_code != HTTPStatus.OK:
        raise HTTPStatusNotOkError(
            f'Получен статус: {response.status_code}'
            f' вместо ожидаемого {HTTPStatus.OK}.'
        )
    logger.debug('Ответ на запрос от API успешно получен.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    Документация из урока API сервиса Практикум.Домашка.
    """
    logger.debug('Начало проверки ответа от API сервера (check_response).')
    if not isinstance(response, dict):
        raise TypeError(f'Тип данных ответа ({type(response)})'
                        ' не соответствует ожидаемому (list).')
    if 'current_date' not in response:
        raise KeyError('Ответ API не содержит ключ current_date.')
    if 'homeworks' not in response:
        raise KeyError('Ответ API не содержит ключ homeworks.')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Тип данных ответа'
                        f' ({type(response.get("homeworks"))})'
                        'не соответствует ожидаемому (list).'
                        )
    logger.debug(
        'Успешное окончание проверки ответа от API сервера'
        ' (функция check_response).'
    )
    return response.get('homeworks')


def parse_status(homework):
    """Принимает конкретный элемент из списка домашних работ.
    Извлекает из него статус этой работы.
    """
    logger.debug('Начало работы функции parse_status')
    status = homework.get('status')
    if 'status' not in homework:
        raise KeyError(f'В словаре {homework} отсутствует ключ status.')
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(
            f'Статус домашней работы ({status}) отличается от возможных'
            f' ожидаемых статусов: {HOMEWORK_VERDICTS.values}.'
        )
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        raise KeyError(f'В словаре {homework} отсутствует ключ homework_name.')
    verdict = HOMEWORK_VERDICTS.get(f'{status}')
    logger.debug('Успешное окончание работы функции parse_status')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_sent_message = ''

    while True:
        try:
            homework = check_response(get_api_answer(timestamp))
            if not homework:
                logger.debug('В ответе остутствуют новые статусы домашки')
            else:
                send_message(bot, parse_status(homework[0]))
                last_sent_message = parse_status(homework[0])
            timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)
            if message != last_sent_message:
                send_message(bot, message)
                last_sent_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
