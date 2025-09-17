"""Константы приложения."""

from http import HTTPStatus
from typing import Final

# HTTP статусы
HTTP_OK: Final[int] = HTTPStatus.OK.value  # 200
HTTP_CREATED: Final[int] = HTTPStatus.CREATED.value  # 201
HTTP_NOT_FOUND: Final[int] = HTTPStatus.NOT_FOUND.value  # 404

# URL и ссылки
REMNAWAVE_API_BASE_URL: Final[str] = "https://remnawave.tgvpnbot.com/api"
SUBSCRIPTION_BASE_URL: Final[str] = (
    "https://sub.officialbot.org/officialvpn/sub"
)

# Значения по умолчанию
DEFAULT_DATABASE_URL: Final[str] = (
    "postgresql+asyncpg://user:password@db:5432/remnawave_db"
)
DEFAULT_FRONTEND_URL: Final[str] = "https://remnawave.tgvpnbot.com"

# Временные интервалы (в днях)
DEFAULT_SUBSCRIPTION_DAYS: Final[int] = 7

# Таймауты (в секундах)
DEFAULT_API_TIMEOUT: Final[int] = 30

# Форматы даты
DATE_FORMAT: Final[str] = "%d.%m.%Y %H:%M"
ISO_DATETIME_SUFFIX: Final[str] = "Z"
ISO_TIMEZONE_REPLACEMENT: Final[str] = "+00:00"

# Статусы пользователей и стратегии
USER_STATUS_ACTIVE: Final[str] = "ACTIVE"
TRAFFIC_LIMIT_STRATEGY_NO_RESET: Final[str] = "NO_RESET"

# Значения по умолчанию для трафика
DEFAULT_TRAFFIC_LIMIT: Final[int] = 0
DEFAULT_TRAFFIC_USED: Final[int] = 0

# Префиксы и суффиксы
TELEGRAM_USERNAME_PREFIX: Final[str] = "tg_"
AUTHORIZATION_BEARER_PREFIX: Final[str] = "Bearer "

# HTTP заголовки
CONTENT_TYPE_JSON: Final[str] = "application/json"
AUTHORIZATION_HEADER: Final[str] = "Authorization"
CONTENT_TYPE_HEADER: Final[str] = "Content-Type"

# Сообщения для пользователей
MSG_USER_CREATED: Final[str] = "✅ <b>Пользователь успешно создан!</b> ✅"
MSG_USER_CREATION_ERROR: Final[str] = (
    "Произошла ошибка при создании пользователя. Пожалуйста, попробуйте позже."
)
MSG_KEY_ERROR: Final[str] = (
    "Произошла ошибка при получении ключа. Пожалуйста, попробуйте позже."
)
MSG_RENEW_ERROR: Final[str] = (
    "Произошла ошибка при продлении ключа. Пожалуйста, попробуйте позже."
)
MSG_NO_SUBSCRIPTION: Final[str] = (
    "❌ <b>У вас нет активной подписки</b> ❌\n\n"
    "Нажмите кнопку 'Создать пользователя' для создания новой "
    "подписки."
)
MSG_SUBSCRIPTION_RENEWED: Final[str] = (
    "✅ <b>Подписка успешно продлена!</b> ✅"
)
MSG_BOT_WELCOME: Final[str] = (
    "Привет! Я бот для работы с VPN. Выберите действие:"
)

# Кнопки интерфейса
BUTTON_CREATE_USER: Final[str] = "Создать пользователя"
BUTTON_GET_KEY: Final[str] = "Получить ключ"
BUTTON_RENEW_KEY: Final[str] = "Продлить ключ"

# Callback данные
CALLBACK_CREATE_USER: Final[str] = "create_user"
CALLBACK_GET_KEY: Final[str] = "get_key"
CALLBACK_RENEW_KEY: Final[str] = "renew_key"

# Шаблоны сообщений
SUBSCRIPTION_INFO_TEMPLATE: Final[str] = (
    "💫 <b>Ваша VPN подписка</b> 💫\n\n"
    "🔗 <b>Ссылка на подписку:</b>\n{subscription_link}\n\n"
    "📅 <b>Дата окончания:</b> {end_date}\n\n"
    "Для продления подписки нажмите кнопку 'Продлить ключ'"
)

SUBSCRIPTION_RENEWED_TEMPLATE: Final[str] = (
    "✅ <b>Подписка успешно продлена!</b> ✅\n\n"
    "🔗 <b>Ссылка на подписку:</b>\n{subscription_link}\n\n"
    "📅 <b>Новая дата окончания:</b> {end_date}"
)

# Значения для неопределенных состояний
UNKNOWN_VALUE: Final[str] = "Неизвестно"

# Пути API
API_USERS_PATH: Final[str] = "/users"
API_USERS_BY_TELEGRAM_ID_PATH: Final[str] = "/users/by-telegram-id"
API_USERS_BY_USERNAME_PATH: Final[str] = "/users/by-username"

# Ключи для работы с API ответами
API_RESPONSE_KEY: Final[str] = "response"
API_USERNAME_KEY: Final[str] = "username"
API_SHORT_UUID_KEY: Final[str] = "shortUuid"
API_UUID_KEY: Final[str] = "uuid"
API_EXPIRE_AT_KEY: Final[str] = "expireAt"
API_TRAFFIC_LIMIT_KEY: Final[str] = "trafficLimitBytes"
API_TELEGRAM_ID_KEY: Final[str] = "telegramId"
API_STATUS_KEY: Final[str] = "status"
API_TRAFFIC_LIMIT_STRATEGY_KEY: Final[str] = "trafficLimitStrategy"

# Режимы парсинга сообщений
PARSE_MODE_HTML: Final[str] = "HTML"
