from http import HTTPStatus
import logging
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram

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
    if len(variables_missing) > 0:
        logger.critical(
            'Отустствуют обязательные переменные окружения:'
            f'{", ".join(variables_missing)}'
        )
        exit(1)
    try:
        logger.debug('Проверка check_tokens успешно пройдена.')
    except telegram.TelegramError as error:
        logger.error(f'Сообщение не отправлено: {error}', exc_info=True)
        raise error


def send_message(bot, message):
    """Отправляет сообщение в Телеграм чат."""
    logger.debug('Сообщение успешно отправлено в Телеграм.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logger.error(f'Сообщение не отправлено: {error}', exc_info=True)
        raise error


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
    logger.debug(
        f'Ответ на запрос от API успешно получен. {response.json()}'
    )
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    Документация из урока API сервиса Практикум.Домашка.
    """
    logger.debug('Начало проверки ответа от API сервера (check_response).')
    current_date = 'current_date'  # Дата ответа API.
    if not isinstance(response, dict):
        raise TypeError(f'Тип данных ответа ({type(response)})'
                        ' не соответствует ожидаемому (list).')
    if current_date not in response:
        raise KeyError(f'Ответ API не содержит ключ {current_date}.')
    homeworks = 'homeworks'  # Все домашние работы ученика в виде списка.
    if not isinstance(response.get(homeworks), list):
        raise TypeError(f'Тип данных ответа ({type(response.get(homeworks))})'
                        ' не соответствует ожидаемому (list).')
    if homeworks not in response:
        raise KeyError(f'Ответ API не содержит ключ {homeworks}.')
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
    if status not in list(HOMEWORK_VERDICTS.keys()):
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
            timestamp = int(time.time())
            if len(homework) == 0:
                logger.debug('В ответе остутствуют новые статусы домашки')
            else:
                last_sent_message = send_message(
                    bot, parse_status(homework[0])
                )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)
            if message != last_sent_message:
                last_sent_message = send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
