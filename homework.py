import exceptions
import logging
import os
import requests
import sys
import telegram
import time
from dotenv import load_dotenv
from http import HTTPStatus

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


def check_tokens():
    """Проверка доступности переменных окружения."""
    logging.info('Проверка наличия всех токенов')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.error(f'Начало отправки сообщения {message}')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except telegram.error.TelegramError as error:
        raise exceptions.TelegramError(
            f'Ошибка отправки статуса в telegram: {error}'
        )
    else:
        logging.debug(f'Сообщение доставлено {message}')


def get_api_answer(timestamp):
    """Получения статуса домашней работы."""
    timestamp = timestamp or int(time.time())
    parametrs_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        logging.info(
            'Начало запроса: url = {url},'
            'headers = {headers},'
            'params = {params}'.format(**parametrs_request))
        homework_statuses = requests.get(**parametrs_request)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise exceptions.InvalidResponseCode(
                'Не удалось получить ответ API, '
                f'ошибка: {homework_statuses.status_code}'
                f'причина: {homework_statuses.reason}'
                f'текст: {homework_statuses.text}'
            )
        try:
            return homework_statuses.json()
        except exceptions.JsonError as error:
            raise exceptions.JsonError(
                logging.error(f'Формат полученного ответа не JSON {error}')
            )
    except Exception:
        raise exceptions.ConnectionError(
            'Не верный код ответа параметры запроса: url = {url},'
            'headers = {headers},'
            'params = {params}'.format(**parametrs_request))


def check_response(response):
    """Проверка ответв API на соответствие документации."""
    logging.debug('Начало проверки')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является dict')
    if 'homeworks' not in response or 'current_date' not in response:
        raise exceptions.EmptyResponseFromAPI('Пустой ответ от API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks не является списком')
    return homeworks


def parse_status(homework):
    """Статус обработки домашнего задания."""
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы {homework_status}')
    return (
        'Изменился статус проверки работы "{homework_name}" {verdict}'
    ).format(
        homework_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework_status]
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует необходимое кол-во'
                         ' переменных окружения')
        sys.exit('Отсутсвуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    start_message = 'Бот начал работу'
    send_message(bot, start_message)
    logging.info(start_message)
    prev_msg = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get(
                'current_date', int(time.time())
            )
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет новых статусов'
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message
            else:
                logging.info(message)
        except exceptions.NotForSending as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s, %(levelname)s, Путь - %(pathname)s, '
            'Файл - %(filename)s, Функция - %(funcName)s, '
            'Номер строки - %(lineno)d, %(message)s'
        ),
        handlers=[logging.FileHandler('log.txt', encoding='UTF-8'),
                  logging.StreamHandler(sys.stdout)]
    )
    main()
