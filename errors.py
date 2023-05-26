class SendMessageError(Exception):
    """Исключение об ошибке отправки сообщенгия в телеграмм."""

    pass


class APIError(Exception):
    """Исключение об ошибки запроса к API."""

    pass


class ResponseStatusCode(Exception):
    """Статус кода не равен ОК."""

    pass