from datetime import datetime, timedelta
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import config
from app.models.subscription import Subscription
from app.models.user import User
from app.services.remnawave_api import RemnawaveAPI
from constants import (
    API_EXPIRE_AT_KEY,
    API_RESPONSE_KEY,
    API_SHORT_UUID_KEY,
    API_TRAFFIC_LIMIT_KEY,
    API_UUID_KEY,
    DEFAULT_TRAFFIC_USED,
    ISO_TIMEZONE_REPLACEMENT,
    SUBSCRIPTION_BASE_URL,
    TELEGRAM_USERNAME_PREFIX,
)


class UserService:
    """Сервис для работы с пользователями и подписками."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Инициализация сервиса.

        Args:
            db_session: Сессия базы данных
        """
        self.db = db_session
        self.remnawave_api = RemnawaveAPI()

    async def get_or_create_user(
        self,
        tg_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Получить существующего пользователя или создать нового.

        Args:
            tg_user_id: ID пользователя в Telegram
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия

        Returns:
            Объект пользователя
        """
        result = await self.db.execute(
            select(User).where(User.tg_user_id == tg_user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(
            tg_user_id=tg_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created=datetime.utcnow(),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info(f"Создан новый пользователь: {tg_user_id}")

        return user

    async def create_user_and_subscription(
        self,
        tg_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[User, Subscription, str]:
        """
        Создать пользователя и подписку.

        Args:
            tg_user_id: ID пользователя в Telegram
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия

        Returns:
            Кортеж (пользователь, подписка, ссылка на подписку)
        """
        user = await self.get_or_create_user(
            tg_user_id, username, first_name, last_name
        )

        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        existing_subscription = result.scalar_one_or_none()

        remnawave_user = await self.remnawave_api.get_user_by_telegram_id(
            tg_user_id
        )

        if remnawave_user:
            subscription_link = (
                await self.remnawave_api.generate_subscription_link(
                    remnawave_user
                )
            )
            logger.info(
                f"Найден существующий пользователь в Remnawave: {tg_user_id}"
            )

            if not existing_subscription:
                try:
                    response_data = remnawave_user.get(
                        API_RESPONSE_KEY, remnawave_user
                    )

                    if (
                        isinstance(response_data, list)
                        and len(response_data) > 0
                    ):
                        response_data = response_data[0]
                        logger.info(
                            f"Извлечен первый элемент из response: "
                            f"{type(response_data)}"
                        )

                    expire_at = response_data.get(API_EXPIRE_AT_KEY, "")
                    subscription_date = None

                    if expire_at:
                        try:
                            subscription_date = datetime.fromisoformat(
                                expire_at.replace(
                                    "Z", ISO_TIMEZONE_REPLACEMENT
                                )
                            )
                            subscription_date = subscription_date.replace(
                                tzinfo=None
                            )
                        except ValueError:
                            subscription_date = datetime.utcnow() + timedelta(
                                days=config.SUBSCRIPTION_DAYS
                            )
                    else:
                        subscription_date = datetime.utcnow() + timedelta(
                            days=config.SUBSCRIPTION_DAYS
                        )

                    uuid = response_data.get(API_UUID_KEY, "")
                    short_uuid = response_data.get(API_SHORT_UUID_KEY, "")

                    if not short_uuid:
                        logger.error(
                            f"shortUuid отсутствует в ответе API для "
                            f"пользователя {tg_user_id}"
                        )
                        raise Exception("shortUuid отсутствует в ответе API")

                    if not uuid:
                        logger.error(
                            f"uuid отсутствует в ответе API для "
                            f"пользователя {tg_user_id}"
                        )
                        raise Exception("uuid отсутствует в ответе API")

                    vpn_key = f"{SUBSCRIPTION_BASE_URL}/{short_uuid}"

                    subscription = Subscription(
                        user_id=user.id,
                        vpn_key=vpn_key,
                        vpn_id=uuid,
                        subscription_date=subscription_date,
                        traffic_limit=response_data.get(
                            API_TRAFFIC_LIMIT_KEY, DEFAULT_TRAFFIC_USED
                        ),
                        creation_time=datetime.utcnow(),
                        traffic_used=DEFAULT_TRAFFIC_USED,
                    )

                    self.db.add(subscription)
                    await self.db.commit()
                    await self.db.refresh(subscription)

                    logger.info(
                        f"Создана локальная запись подписки для существующего "
                        f"пользователя {tg_user_id}"
                    )
                    return user, subscription, subscription_link
                except Exception as e:
                    logger.error(
                        f"Ошибка создания локальной записи подписки: {e}"
                    )
                    raise

            if existing_subscription:
                logger.info(
                    f"Использована существующая подписка для {tg_user_id}"
                )
                return user, existing_subscription, subscription_link

        try:
            telegram_username = (
                username
                if username
                else f"{TELEGRAM_USERNAME_PREFIX}{tg_user_id}"
            )

            remnawave_user = await self.remnawave_api.create_user(
                tg_user_id, telegram_username
            )

            subscription_link = (
                await self.remnawave_api.generate_subscription_link(
                    remnawave_user
                )
            )

            response_data = remnawave_user.get(
                API_RESPONSE_KEY, remnawave_user
            )

            if isinstance(response_data, list) and len(response_data) > 0:
                response_data = response_data[0]
                logger.info(
                    f"Извлечен первый элемент из response: "
                    f"{type(response_data)}"
                )

            expire_at = response_data.get(API_EXPIRE_AT_KEY, "")
            subscription_date = None

            if expire_at:
                try:
                    subscription_date = datetime.fromisoformat(
                        expire_at.replace("Z", ISO_TIMEZONE_REPLACEMENT)
                    )
                    subscription_date = subscription_date.replace(tzinfo=None)
                except ValueError:
                    logger.warning(
                        f"Некорректный формат даты из API: {expire_at}"
                    )
                    subscription_date = datetime.utcnow() + timedelta(
                        days=config.SUBSCRIPTION_DAYS
                    )
            else:
                logger.warning(
                    "Дата окончания подписки отсутствует в ответе API"
                )
                subscription_date = datetime.utcnow() + timedelta(
                    days=config.SUBSCRIPTION_DAYS
                )

            uuid = response_data.get(API_UUID_KEY, "")
            short_uuid = response_data.get(API_SHORT_UUID_KEY, "")

            if not short_uuid:
                logger.error(
                    f"shortUuid отсутствует в ответе API для пользователя "
                    f"{tg_user_id}"
                )
                raise Exception("shortUuid отсутствует в ответе API")

            if not uuid:
                logger.error(
                    f"uuid отсутствует в ответе API для пользователя "
                    f"{tg_user_id}"
                )
                raise Exception("uuid отсутствует в ответе API")

            vpn_key = f"{SUBSCRIPTION_BASE_URL}/{short_uuid}"

            subscription = Subscription(
                user_id=user.id,
                vpn_key=vpn_key,
                vpn_id=uuid,
                subscription_date=subscription_date,
                traffic_limit=response_data.get(
                    API_TRAFFIC_LIMIT_KEY, DEFAULT_TRAFFIC_USED
                ),
                creation_time=datetime.utcnow(),
                traffic_used=DEFAULT_TRAFFIC_USED,
            )

            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Создана подписка для пользователя {tg_user_id}")
            return user, subscription, subscription_link

        except Exception as e:
            logger.error(f"Ошибка создания подписки для {tg_user_id}: {e}")
            raise

    async def get_user_subscription(
        self, tg_user_id: int
    ) -> Optional[Tuple[Subscription, str]]:
        """
        Получить подписку пользователя.

        Args:
            tg_user_id: ID пользователя в Telegram

        Returns:
            Кортеж (подписка, ссылка на подписку) или None
        """
        result = await self.db.execute(
            select(User).where(User.tg_user_id == tg_user_id)
        )
        users = result.scalars().all()

        if not users:
            logger.warning(f"Пользователь не найден: {tg_user_id}")
            return None

        if len(users) > 1:
            logger.warning(
                f"Найдено несколько пользователей с ID {tg_user_id}. "
                f"Используем первого."
            )

        user = users[0]

        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.warning(
                f"Подписка не найдена для пользователя: {tg_user_id}"
            )
            return None

        if len(subscriptions) > 1:
            logger.warning(
                f"Найдено несколько подписок для пользователя {tg_user_id}. "
                f"Используем первую."
            )

        subscription = subscriptions[0]

        remnawave_user = await self.remnawave_api.get_user_by_telegram_id(
            tg_user_id
        )
        if remnawave_user:
            logger.info(
                f"Тип данных от API: {type(remnawave_user)}, "
                f"данные: {remnawave_user}"
            )

            if isinstance(remnawave_user, list):
                if len(remnawave_user) > 0:
                    remnawave_user = remnawave_user[0]
                    logger.info(
                        f"Извлечен первый элемент из списка: {remnawave_user}"
                    )
                else:
                    logger.warning(
                        f"Получен пустой список от API для пользователя "
                        f"{tg_user_id}"
                    )
                    return subscription, subscription.vpn_key

            response_data = remnawave_user.get(
                API_RESPONSE_KEY, remnawave_user
            )

            if isinstance(response_data, list) and len(response_data) > 0:
                response_data = response_data[0]
                logger.info(
                    f"Извлечен первый элемент из response: "
                    f"{type(response_data)}"
                )

            short_uuid = response_data.get(API_SHORT_UUID_KEY, "")
            uuid = response_data.get(API_UUID_KEY, "")

            if short_uuid:
                subscription_link = f"{SUBSCRIPTION_BASE_URL}/{short_uuid}"

                if (
                    subscription.vpn_key != subscription_link
                    or subscription.vpn_id != uuid
                ):
                    subscription.vpn_key = subscription_link
                    subscription.vpn_id = uuid
                    await self.db.commit()

                return subscription, subscription_link

        return subscription, subscription.vpn_key
