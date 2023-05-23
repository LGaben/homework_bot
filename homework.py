"""Модуль обработки состояние домашних заданий.

Telegram-бот, который обращается к API сервиса Практикум.Домашка
и узнает статус домашней работы.
"""

import logging
import os
from http import HTTPStatus

import requests
import time

from telegram import Bot, TelegramError

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: str = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def check_tokens() -> None:
    """Проветка присутствия токенов."""
    tokens = {
        PRACTICUM_TOKEN: 'В файле не задан практикум токен',
        TELEGRAM_TOKEN: 'В файле не задан телеграмм токен',
        TELEGRAM_CHAT_ID: 'В файле не задан телеграмм ID'
    }
    for token, message in tokens.items():
        if token is None:
            logger.critical(message)
            raise Exception(message)


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение успешно отправленно: {message}')
    except TelegramError as error:
        logger.error(f'Сообщение не отправленно: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload: dict = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        if response.status_code != HTTPStatus.OK:
            logger.critical('Страница недоступна')
            raise Exception('Страница недоступна')
        return response.json()
    except Exception as error:
        logger.critical(f'Ошибка при запросе к основному API: {error}')
        raise Exception(f'Ошибка при запросе к основному API: {error}')


def check_response(response: dict) -> dict:
    """Проверка ответа API на корректность."""
    if type(response) is not dict:
        raise TypeError('В функцию "check_response" поступил не словарь')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks отсутствует')
    if type(response['homeworks']) is not list:
        raise TypeError('Объект homeworks не является списком')
    if response['homeworks'] == []:
        return None
    if response['homeworks'][0]['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Ключ статуса не отвечает стандарту')
    return response.get('homeworks')[0]


def parse_status(homework: dict) -> str:
    """Извлекает из информации о домашней работе статусэтой работы."""
    if 'homework_name' not in homework:
        logger.info('Отсутствует название работы')
        raise KeyError('отсутствует homework_name')
    homework_name: str = homework['homework_name']
    if (
        (homework['status'] is None)
        or (homework['status'] not in HOMEWORK_VERDICTS)
    ):
        logger.info('Ключ статуса не отвечает стандарту')
        raise KeyError('Ключ статуса не отвечает стандарту')
    verdict: str = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    check_tokens()
    bot: Bot = Bot(token=TELEGRAM_TOKEN)
    hw_status: str = None
    while True:
        try:
            timestamp: int = int(time.time())
            response: dict = get_api_answer(timestamp)
            homework: dict = check_response(response)
            if homework:
                if hw_status != homework.get('status'):
                    hw_status = homework.get('status')
                    message: str = parse_status(homework)
                    send_message(bot, message)
                else:
                    logger.info('Статус ответа не обновился')
            else:
                logger.info('homework пуст')
            timestamp: int = response['current_date']
        except Exception as error:
            message: str = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
