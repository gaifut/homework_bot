import logging
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram

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

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))
logger.addHandler(handler)


def check_tokens():
    """Проверяет наличие и формат переменных окружения."""
    if (
        isinstance(PRACTICUM_TOKEN, str)
        and isinstance(TELEGRAM_TOKEN, str)
        and isinstance(TELEGRAM_CHAT_ID, str)
    ):
        logging.debug('Проверка check_tokens успешно пройдена')
        return True
    logging.critical('Отустствуют обязательные переменные окружения.')
    return exit()


def send_message(bot, message):
    """Отправляет сообщение в Телеграм чат."""
    logging.debug('Сообщение успешно отправлено в Телеграм.')
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту, используя временную метку."""
    payload = {'from_date': str(timestamp)}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        response.raise_for_status()
        if response.status_code == 204:
            logging.error('Содержимого нет (204)', exc_info=True)
            raise requests.exceptions.HTTPError('Содержимого нет (204)')
        logging.debug(f'Ответ от API успешно получен. {response.json()}')
        return response.json()
    except requests.exceptions.HTTPError as error:
        logging.error(f'Возникла ошибка {error}', exc_info=True)
        raise error
    except requests.RequestException:
        ...


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    Документация из урока API сервиса Практикум.Домашка.
    """
    if (isinstance(response, dict)):
        if isinstance(response.get('homeworks'), list):
            return response
    logging.error('Тип данных ответа не соответствует ожидаемому')
    raise TypeError('Тип данных ответа не соответствует ожидаемому')


def parse_status(homework):
    """Принимает конкретный элемент из списка домашних работ.
    Извлекает из него статус этой работы.
    """
    status = homework.get('status')
    if status not in list(HOMEWORK_VERDICTS.keys()):
        logging.error(
            'Статус домашней работы отличается от ожидаемого',
            exc_info=True
        )
        raise ValueError('Статус домашней работы отличается от ожидаемого')
    homework_name = homework.get('homework_name')
    if 'homework_name' not in list(homework.keys()):
        logging.error(
            'Домашняя работа не найдена',
            exc_info=True
        )
        raise ValueError('Домашняя работа не найдена')
    verdict = HOMEWORK_VERDICTS.get(f'{status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    default_status = ''

    check_tokens()

    while True:
        try:
            homework = check_response(
                get_api_answer(timestamp)).get('homeworks')[0]
            homework_status = homework.get('status')
            if homework_status != default_status:
                default_status = homework_status
                send_message(bot, parse_status(homework))
        except IndexError:
            message = 'Новых домашек не найдено'
            logging.exception(message)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
