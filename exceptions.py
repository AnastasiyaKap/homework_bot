class NotForSending(Exception):
    """Не для пересылки в телеграм."""

    pass


class InvalidResponseCode(Exception):
    """Неверный код ответа."""

    pass


class ConnectinError(Exception):
    """Неверный код ответа."""

    pass


class EmptyResponseFromAPI(NotForSending):
    """Пустой ответ от API."""

    pass


class TelegramError(NotForSending):
    """Ошибка телеграма."""

    pass


class JsonError(Exception):
    """Неверный формат JSON."""

    pass
