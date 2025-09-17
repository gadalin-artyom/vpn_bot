import aiohttp
import config  # type: ignore
import constants  # type: ignore
from datetime import datetime, timezone
import uuid
import string
import random
from typing import Optional, Dict, Any

def generate_secure_string(length=16, allowed_chars=string.ascii_letters + string.digits + "_"):
    """Генерирует безопасную строку заданной длины из допустимых символов"""
    return ''.join(random.choice(allowed_chars) for _ in range(length))

def generate_trojan_password():
    """Генерирует пароль для Trojan длиной до 32 символов"""
    return generate_secure_string(length=32, allowed_chars=string.ascii_letters + string.digits)

def generate_ss_password():
    """Генерирует пароль для Shadowsocks длиной до 32 символов"""
    return generate_secure_string(length=32, allowed_chars=string.ascii_letters + string.digits)

def generate_tag():
    """Генерирует тег длиной до 16 символов, содержащий только заглавные буквы, цифры и подчеркивания"""
    return generate_secure_string(length=16, allowed_chars=string.ascii_uppercase + string.digits + "_")

class RemnawaveAPI:
    """
    Класс для работы с API Remnawave.

    Атрибуты:
        base_url (str): Базовый URL API Remnawave.
        api_token (str): Токен авторизации для API.
        frontend_url (str): URL фронтенда Remnawave.
        session (aiohttp.ClientSession, optional): Асинхронная сессия HTTP.
    """

    def __init__(self):
        """Инициализирует клиент API Remnawave."""
        self.base_url = constants.REMNAWAVE_API_BASE_URL
        self.api_token = config.REMNAWAVE_API_TOKEN
        self.frontend_url = config.REMNAWAVE_FRONTEND_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """
        Асинхронный контекстный менеджер для инициализации сессии.

        Returns:
            RemnawaveAPI: Экземпляр класса с открытой сессией.
        """
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Асинхронный контекстный менеджер для закрытия сессии.
        """
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """
        Формирует заголовки для HTTP-запросов с токеном авторизации.

        Returns:
            Dict[str, str]: Словарь заголовков.
        """
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по telegram_id.

        Args:
            telegram_id (int): ID пользователя в Telegram.

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если не найден.
        """
        url = f"{self.base_url}{constants.REMNAWAVE_USERS_ENDPOINT}?telegramId={telegram_id}"
        headers = self._get_headers()

        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data and len(data) > 0:
                    return data[0]
                return None
            elif resp.status == 404:
                return None
            else:
                text = await resp.text()
                raise Exception(
                    f"Ошибка получения пользователя по telegram_id в Remnawave API: {resp.status} - {text}"
                )

    async def create_user(self, username: Optional[str] = None, tg_user_id: Optional[int] = None, expire_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Создает нового пользователя в системе Remnawave.

        Args:
            username (str, optional): Имя пользователя. По умолчанию формируется как 'tg_{tg_user_id}'.
            tg_user_id (int, optional): ID пользователя в Telegram.
            expire_at (datetime, optional): Дата окончания подписки (UTC).

        Returns:
            Dict[str, Any]: JSON-ответ от API с данными созданного пользователя.

        Raises:
            Exception: Если запрос не успешен или не удалось распарсить ответ.
        """
        url = f"{self.base_url}{constants.REMNAWAVE_USERS_ENDPOINT}"
        headers = self._get_headers()

        if username is None and tg_user_id is not None:
            username = f"tg_{tg_user_id}"

        payload = {
            "username": username,
            "status": "ACTIVE",
            "shortUuid": str(uuid.uuid4()),
            "trojanPassword": generate_trojan_password(),
            "vlessUuid": str(uuid.uuid4()),
            "ssPassword": generate_ss_password(),
            "trafficLimitBytes": 0,
            "trafficLimitStrategy": "NO_RESET",
            "expireAt": expire_at.strftime(constants.ISO_DATE_FORMAT) if expire_at else None,
            "createdAt": datetime.now(timezone.utc).strftime(constants.ISO_DATE_FORMAT),
            "lastTrafficResetAt": datetime.now(timezone.utc).strftime(constants.ISO_DATE_FORMAT),
            "description": "Created by Telegram bot",
            "tag": generate_tag(),
            "telegramId": tg_user_id,
            "email": f"bot_{tg_user_id}@example.com",
            "hwidDeviceLimit": 0,
            "activeInternalSquads": []
        }

        if not self.session:
            raise Exception("Сессия aiohttp не инициализирована")

        async with self.session.post(url, json=payload, headers=headers) as resp:
            if resp.status in (200, 201):
                try:
                    data = await resp.json()
                    return data
                except aiohttp.ClientError as e:
                    text = await resp.text()
                    raise Exception(
                        f"Ошибка парсинга JSON ответа при создании пользователя: {e}. "
                        f"Текст ответа: {text}"
                    )
            else:
                text = await resp.text()
                raise Exception(
                    f"Ошибка создания пользователя в Remnawave API: {resp.status} - {text}"
                )

    async def create_subscription(self, user_uuid: str, expiry_date: datetime) -> Dict[str, Any]:
        """
        Создает новую подписку для пользователя в системе Remnawave.

        Args:
            user_uuid (str): UUID пользователя в Remnawave.
            expiry_date (datetime): Дата окончания подписки (UTC).

        Returns:
            Dict[str, Any]: JSON-ответ от API с данными созданной подписки.

        Raises:
            Exception: Если запрос не успешен или не удалось распарсить ответ.
        """
        url = f"{self.base_url}{constants.REMNAWAVE_SUBSCRIPTIONS_ENDPOINT}"
        headers = self._get_headers()

        expiry_str = expiry_date.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

        payload = {
            "userUuid": user_uuid,
            "expiry": expiry_str,
            "trafficLimitBytes": 0,
            "trafficLimitStrategy": "NO_RESET",
            "description": "Created by Telegram bot",
            "tag": generate_tag(),
            "hwidDeviceLimit": 0,
            "activeInternalSquads": []
        }

        if not self.session:
            raise Exception("Сессия aiohttp не инициализирована")

        async with self.session.post(url, json=payload, headers=headers) as resp:
            if resp.status in (200, 201):
                try:
                    data = await resp.json()
                    return data
                except aiohttp.ClientError as e:
                    text = await resp.text()
                    raise Exception(
                        f"Ошибка парсинга JSON ответа при создании подписки: {e}. "
                        f"Текст ответа: {text}"
                    )
            else:
                text = await resp.text()
                raise Exception(
                    f"Ошибка создания подписки в Remnawave API: {resp.status} - {text}"
                )

    async def renew_subscription(self, subscription_uuid: str, new_expiry_date: datetime) -> Dict[str, Any]:
        """
        Продлевает существующую подписку в системе Remnawave.

        Args:
            subscription_uuid (str): UUID подписки в Remnawave.
            new_expiry_date (datetime): Новая дата окончания подписки (ожидается в UTC).

        Returns:
            Dict[str, Any]: JSON-ответ от API с обновленными данными подписки.

        Raises:
            Exception: Если запрос не успешен или не удалось распарсить ответ.
        """
        url = f"{self.base_url}{constants.REMNAWAVE_SUBSCRIPTIONS_ENDPOINT}/{subscription_uuid}"
        headers = self._get_headers()

        new_expiry_str = new_expiry_date.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

        payload = {"expiry": new_expiry_str}

        if not self.session:
            raise Exception("Сессия aiohttp не инициализирована")

        async with self.session.patch(url, json=payload, headers=headers) as resp:
            if resp.status in (200, 204):
                try:
                    if resp.status == 204:
                        return {"uuid": subscription_uuid, "expiry": new_expiry_str}
                    data = await resp.json()
                    return data
                except aiohttp.ClientError as e:
                    text = await resp.text()
                    raise Exception(
                        f"Ошибка парсинга JSON ответа при продлении подписки: {e}. "
                        f"Текст ответа: {text}"
                    )
            else:
                text = await resp.text()
                raise Exception(
                    f"Ошибка продления подписки в Remnawave API: {resp.status} - {text}"
                )