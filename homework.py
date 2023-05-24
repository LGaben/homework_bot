"""Модуль обработки состояние домашних заданий.

Telegram-бот, который обращается к API сервиса Практикум.Домашка
и узнает статус домашней работы.
"""

import sys
import logging
import os
from http import HTTPStatus
import time

import requests
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

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def check_tokens() -> None:
    """Проветка присутствия токенов."""
    tokens = {
        'Практикум токен': PRACTICUM_TOKEN,
        'Телеграмм токен': TELEGRAM_TOKEN,
        'Телеграмм чат ID': TELEGRAM_CHAT_ID
    }
    for name_token, token in tokens.items():
        if token is None:
            logger.critical(f'Отсутствует {name_token}')
            sys.exit(f'Отсутствует {name_token}')


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение успешно отправленно: {message}')
    except TelegramError as error:
        raise error(f'Сообщение не отправленно: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload: dict = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
    except requests.exceptions.RequestException as e:
        raise e(
            f'Ошибка при запросе к основному API: {e}'
            f'Url: {ENDPOINT}'
            f'Headers: {HEADERS}'
        )
    if response.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            f'Ошибка {response.status_code}'
            f'Url: {ENDPOINT}'
            f'Headers: {HEADERS}'
        )
    return response.json()


def check_response(response: dict) -> dict:
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(
            'В функцию "check_response" поступил не словарь,'
            f'а {type(response)}'
        )
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks отсутствует')
    if not isinstance(response['homeworks'], list):
        hw = response['homeworks']
        raise TypeError(
            'Объект homeworks не является списком'
            f'Тип объекта {type(hw)}'
        )
    if 'current_date' not in response:
        raise KeyError('Отсутствует текущая дата в ответе')
    return response.get('homeworks')


def parse_status(homework: dict) -> str:
    """Извлекает из информации о домашней работе статусэтой работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует название работы')
    homework_name: str = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Отсутствует статус работы')
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Ключ статуса не отвечает стандарту')
    verdict: str = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    check_tokens()
    bot: Bot = Bot(token=TELEGRAM_TOKEN)
    timestamp: int = 0
    while True:
        try:
            response: dict = get_api_answer(timestamp)
            timestamp: int = response['current_date']
            homework: dict = check_response(response)
            if homework:
                message: str = parse_status(homework[0])
                send_message(bot, message)
            else:
                logger.info('homework пуст')
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}', exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
