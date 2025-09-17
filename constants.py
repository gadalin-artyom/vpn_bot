from datetime import timedelta

REMNAWAVE_API_BASE_URL = "https://remnawave.tgvpnbot.com/api"
REMNAWAVE_USERS_ENDPOINT = "/users"
REMNAWAVE_SUBSCRIPTIONS_ENDPOINT = "/subscriptions"
SUBSCRIPTION_DAYS = 7
SUBSCRIPTION_DELTA = timedelta(days=SUBSCRIPTION_DAYS)
RENEWAL_YEARS = 1
RENEWAL_DELTA = timedelta(days=365 * RENEWAL_YEARS)
ISO_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
USERS_TABLE = "users"
SUBSCRIPTIONS_TABLE = "subscriptions"
BUTTON_CREATE_USER = "Создать пользователя"
BUTTON_GET_KEY = "Получить ключ"
BUTTON_RENEW_KEY = "Продлить ключ"
WELCOME_MESSAGE = "Добро пожаловать! Выберите действие:"
USER_CREATED_MESSAGE = "Пользователь создан. Ваш ключ/ссылка:"
KEY_RETRIEVED_MESSAGE = "Ваш ключ/ссылка:"
KEY_RENEWED_MESSAGE = "Ключ продлен до:"
ERROR_MESSAGE = "Произошла ошибка. Попробуйте позже."
NO_SUBSCRIPTION_MESSAGE = "У вас пока нет активной подписки."
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)