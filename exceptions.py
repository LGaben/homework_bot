class SendMessageError(Exception):
    """Исключение об ошибке отправки сообщенгия в телеграмм."""

    pass


class ResponseStatusCode(Exception):
    """Статус кода не равен ОК."""

    pass


class ApiAnswerError(Exception):
    """Ошибка в response API."""

    pass


class SendMessageErrorException(Exception):
    """Сбой отправки сообщения об ошибке."""

    pass
