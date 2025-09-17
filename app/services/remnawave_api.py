from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import aiohttp
from loguru import logger

import config
from constants import (
    API_EXPIRE_AT_KEY,
    API_RESPONSE_KEY,
    API_SHORT_UUID_KEY,
    API_STATUS_KEY,
    API_TELEGRAM_ID_KEY,
    API_TRAFFIC_LIMIT_KEY,
    API_TRAFFIC_LIMIT_STRATEGY_KEY,
    API_USERNAME_KEY,
    API_USERS_BY_TELEGRAM_ID_PATH,
    API_USERS_BY_USERNAME_PATH,
    API_USERS_PATH,
    AUTHORIZATION_BEARER_PREFIX,
    AUTHORIZATION_HEADER,
    CONTENT_TYPE_HEADER,
    CONTENT_TYPE_JSON,
    DEFAULT_TRAFFIC_LIMIT,
    HTTP_CREATED,
    HTTP_NOT_FOUND,
    HTTP_OK,
    ISO_DATETIME_SUFFIX,
    SUBSCRIPTION_BASE_URL,
    TRAFFIC_LIMIT_STRATEGY_NO_RESET,
    USER_STATUS_ACTIVE,
)


class RemnawaveAPI:
    """Клиент для работы с Remnawave API."""

    def __init__(self) -> None:
        """Инициализация клиента API."""
        self.base_url = config.REMNAWAVE_API_BASE_URL
        self.token = config.REMNAWAVE_API_TOKEN
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT)

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для HTTP-запросов.

        Returns:
            Словарь с заголовками для авторизации
        """
        return {
            AUTHORIZATION_HEADER: f"{AUTHORIZATION_BEARER_PREFIX}{self.token}",
            CONTENT_TYPE_HEADER: CONTENT_TYPE_JSON,
        }

    async def create_user(
        self, telegram_id: int, username: str
    ) -> Dict[str, Any]:
        """Создать нового пользователя в Remnawave.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя

        Returns:
            Данные созданного пользователя

        Raises:
            Exception: При ошибке создания пользователя
        """
        url = f"{self.base_url}{API_USERS_PATH}"

        expire_date = datetime.now() + timedelta(days=config.SUBSCRIPTION_DAYS)

        payload = {
            API_USERNAME_KEY: username,
            API_TELEGRAM_ID_KEY: telegram_id,
            API_EXPIRE_AT_KEY: expire_date.isoformat() + ISO_DATETIME_SUFFIX,
            API_TRAFFIC_LIMIT_KEY: DEFAULT_TRAFFIC_LIMIT,
            API_TRAFFIC_LIMIT_STRATEGY_KEY: TRAFFIC_LIMIT_STRATEGY_NO_RESET,
            API_STATUS_KEY: USER_STATUS_ACTIVE,
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                url, json=payload, headers=self._get_headers()
            ) as response:
                if response.status in (HTTP_OK, HTTP_CREATED):
                    data = await response.json()
                    logger.info(
                        f"Пользователь создан в Remnawave: {telegram_id}"
                    )
                    return data
                else:
                    text = await response.text()
                    logger.error(
                        f"Ошибка создания пользователя: {response.status} - "
                        f"{text}"
                    )
                    raise Exception(f"API error {response.status}: {text}")

    async def get_user_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            Данные пользователя или None, если не найден
        """
        url = f"{self.base_url}{API_USERS_BY_TELEGRAM_ID_PATH}/{telegram_id}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url, headers=self._get_headers()
                ) as response:
                    if response.status == HTTP_OK:
                        data = await response.json()
                        logger.info(
                            f"Пользователь найден в Remnawave: {telegram_id}, "
                            f"тип данных: {type(data)}"
                        )

                        if isinstance(data, list):
                            logger.info(
                                f"API вернул список из {len(data)} элементов"
                            )
                            if len(data) > 0:
                                logger.info(
                                    f"Возвращаем первый элемент: "
                                    f"{type(data[0])}"
                                )
                                return data[
                                    0
                                ]
                            else:
                                logger.info(
                                    f"Список пользователей пуст для "
                                    f"telegram_id: {telegram_id}"
                                )
                                return None
                        else:
                            logger.info(
                                f"API вернул объект напрямую: {type(data)}"
                            )
                            return data
                    elif response.status == HTTP_NOT_FOUND:
                        logger.info(
                            f"Пользователь не найден в Remnawave: "
                            f"{telegram_id}"
                        )
                        return None
                    else:
                        text = await response.text()
                        logger.error(
                            f"Ошибка получения пользователя: "
                            f"{response.status} - {text}"
                        )
                        return None
        except Exception as e:
            logger.error(f"Исключение при получении пользователя по ID: {e}")
            return None

    async def get_user_by_username(
        self, username: str
    ) -> Optional[Dict[str, Any]]:
        """Получить пользователя по имени пользователя.

        Args:
            username: Имя пользователя

        Returns:
            Данные пользователя или None, если не найден
        """
        url = f"{self.base_url}{API_USERS_BY_USERNAME_PATH}/{username}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url, headers=self._get_headers()
                ) as response:
                    if response.status == HTTP_OK:
                        data = await response.json()
                        logger.info(
                            f"Пользователь найден по username: {username}"
                        )

                        if isinstance(data, list):
                            if len(data) > 0:
                                return data[
                                    0
                                ]
                            else:
                                logger.info(
                                    f"Список пользователей пуст для "
                                    f"username: {username}"
                                )
                                return None
                        else:
                            return data
                    else:
                        text = await response.text()
                        logger.error(
                            f"Ошибка получения пользователя по username: "
                            f"{response.status} - {text}"
                        )
                        return None
        except Exception as e:
            logger.error(
                f"Исключение при получении пользователя по username: {e}"
            )
            return None

    async def generate_subscription_link(
        self, user_data: Union[Dict[str, Any], str]
    ) -> str:
        """Сгенерировать ссылку на подписку.

        Args:
            user_data: Данные пользователя или строка

        Returns:
            Ссылка на подписку
        """
        if isinstance(user_data, dict):
            response_data = user_data.get(API_RESPONSE_KEY, user_data)

            if isinstance(response_data, list) and len(response_data) > 0:
                response_data = response_data[0]
                logger.info(
                    f"В generate_subscription_link извлечен первый элемент "
                    f"из response: {type(response_data)}"
                )

            username = response_data.get(API_USERNAME_KEY, "")
            short_uuid = response_data.get(API_SHORT_UUID_KEY)

            if short_uuid:
                return f"{SUBSCRIPTION_BASE_URL}/{short_uuid}"

            if username:
                user_details = await self.get_user_by_username(username)
                if user_details:
                    details_response = user_details.get(
                        API_RESPONSE_KEY, user_details
                    )
                    if API_SHORT_UUID_KEY in details_response:
                        return (
                            f"{SUBSCRIPTION_BASE_URL}/"
                            f"{details_response[API_SHORT_UUID_KEY]}"
                        )

            logger.warning(
                "Не удалось сформировать ссылку на подписку - "
                "shortUuid отсутствует"
            )
            return ""

        elif isinstance(user_data, str):
            if user_data.startswith(SUBSCRIPTION_BASE_URL.split("/sub")[0]):
                return user_data

            if "/" not in user_data:
                return f"{SUBSCRIPTION_BASE_URL}/{user_data}"

            return user_data

        else:
            logger.warning(
                f"Некорректный тип данных для ссылки: {type(user_data)}"
            )
            return ""
