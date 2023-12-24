from http import HTTPStatus


class HTTPStatusNotOkError(Exception):
    """Вылавливает все HTTP статусы кроме OK."""

    pass


def check_status_not_OK(status):
    """Сравнивает статус параметра со статусом OK.
    Выбрасывает ошибку при неравенстве.
    """
    if status != HTTPStatus.OK:
        raise HTTPStatusNotOkError(
            f'Получен статус: {status}'
            f' вместо ожидаемого {HTTPStatus.OK}.'
        )
