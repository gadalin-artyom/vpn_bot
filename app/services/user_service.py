from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.subscription import Subscription
from datetime import datetime, timezone, timedelta
import constants  # type: ignore
from app.utils.logger import get_logger  # type: ignore
from app.services.remnawave_api import RemnawaveAPI  # type: ignore

logger = get_logger(__name__)

class UserService:
    """
    Сервис для управления пользователями и их подписками.

    Атрибуты:
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Инициализирует сервис с сессией БД.

        Args:
            db_session (AsyncSession): Сессия SQLAlchemy.
        """
        self.db = db_session

    async def get_or_create_user(self, tg_user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """
        Получает пользователя из БД по tg_user_id или создает нового, если не найден.

        Args:
            tg_user_id (int): ID пользователя в Telegram.
            username (str, optional): Имя пользователя в Telegram.
            first_name (str, optional): Имя пользователя в Telegram.
            last_name (str, optional): Фамилия пользователя в Telegram.

        Returns:
            User: Экземпляр модели User.
        """
        result = await self.db.execute(select(User).where(User.tg_user_id == tg_user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.info(f"Создание нового пользователя TG ID: {tg_user_id}")
            user = User(
                tg_user_id=tg_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Пользователь TG ID: {tg_user_id} успешно создан с ID: {user.id}")
        else:
            logger.debug(f"Пользователь TG ID: {tg_user_id} уже существует")

        return user

    async def create_user_and_subscription(self, tg_user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> tuple[User, Subscription, str]:
        """
        Создает пользователя в Remnawave, БД и соответствующую подписку.

        Args:
            tg_user_id (int): ID пользователя в Telegram.
            username (str, optional): Имя пользователя в Telegram.
            first_name (str, optional): Имя пользователя в Telegram.
            last_name (str, optional): Фамилия пользователя в Telegram.

        Returns:
            tuple[User, Subscription, str]: Кортеж из модели пользователя, модели подписки и ссылки на подписку.

        Raises:
            Exception: Если возникают ошибки при взаимодействии с API или БД.
        """
        async with RemnawaveAPI() as remnawave:
            rem_user_data = await remnawave.get_user_by_telegram_id(tg_user_id)

            if rem_user_data:
                logger.info(f"Пользователь TG ID: {tg_user_id} уже существует в Remnawave. Используем существующего пользователя.")
                rem_user_uuid = rem_user_data.get('uuid') or rem_user_data.get('id')
                if not rem_user_uuid:
                    logger.error(f"Не найдено поле UUID в ответе от API. Доступные поля: {list(rem_user_data.keys())}")
                    raise Exception("Не удалось получить UUID пользователя из ответа Remnawave API")

                result = await self.db.execute(
                    select(Subscription)
                    .where(Subscription.user_id == tg_user_id)
                    .order_by(Subscription.subscription_date.desc())
                )
                subscription = result.scalar_one_or_none()

                if subscription:
                    logger.info(f"Подписка для TG ID: {tg_user_id} уже существует в БД.")
                    return None, subscription, subscription.vpn_key
                else:
                    logger.info(f"Подписка для TG ID: {tg_user_id} не найдена в БД. Создаем новую подписку.")
                    expiry_date = datetime.now(timezone.utc) + constants.SUBSCRIPTION_DELTA
                    rem_sub_data = await remnawave.create_subscription(user_uuid=rem_user_uuid, expiry_date=expiry_date)
                    rem_sub_uuid = rem_sub_data.get('uuid') or rem_sub_data.get('id')
                    if not rem_sub_uuid:
                        logger.error(f"Не найдено поле UUID подписки в ответе от API. Доступные поля: {list(rem_sub_data.keys())}")
                        raise Exception("Не удалось получить UUID подписки из ответа Remnawave API")

                    subscription_link = f"{remnawave.frontend_url}/api/sub/{rem_user_data['shortUuid']}"

                    subscription = Subscription(
                        user_id=tg_user_id,
                        vpn_key=subscription_link,
                        vpn_id=rem_sub_uuid,
                        subscription_date=expiry_date,
                    )
                    self.db.add(subscription)
                    await self.db.commit()
                    await self.db.refresh(subscription)
                    logger.info(f"Подписка для TG ID: {tg_user_id} успешно создана с ID: {subscription.id}")

                    user = await self.get_or_create_user(tg_user_id, username, first_name, last_name)
                    return user, subscription, subscription_link

            user = await self.get_or_create_user(tg_user_id, username, first_name, last_name)
            expiry_date = datetime.now(timezone.utc) + constants.SUBSCRIPTION_DELTA

            rem_user_data = await remnawave.create_user(
                username=f"tg_{tg_user_id}",
                tg_user_id=tg_user_id,
                expire_at=expiry_date
            )

            rem_user_uuid = rem_user_data.get('uuid') or rem_user_data.get('id')
            if not rem_user_uuid:
                logger.error(f"Не найдено поле UUID в ответе от API. Доступные поля: {list(rem_user_data.keys())}")
                raise Exception("Не удалось получить UUID пользователя из ответа Remnawave API")

            rem_sub_data = await remnawave.create_subscription(user_uuid=rem_user_uuid, expiry_date=expiry_date)
            rem_sub_uuid = rem_sub_data.get('uuid') or rem_sub_data.get('id')
            if not rem_sub_uuid:
                logger.error(f"Не найдено поле UUID подписки в ответе от API. Доступные поля: {list(rem_sub_data.keys())}")
                raise Exception("Не удалось получить UUID подписки из ответа Remnawave API")

            subscription_link = f"{remnawave.frontend_url}/api/sub/{rem_user_data['shortUuid']}"

            subscription = Subscription(
                user_id=tg_user_id,
                vpn_key=subscription_link,
                vpn_id=rem_sub_uuid,
                subscription_date=expiry_date,
            )
            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)
            logger.info(f"Подписка для TG ID: {tg_user_id} успешно создана с ID: {subscription.id}")

        return user, subscription, subscription_link

    async def get_user_subscription(self, tg_user_id: int) -> tuple[Subscription, str] | None:
        """
        Получает последнюю подписку пользователя из БД.

        Args:
            tg_user_id (int): ID пользователя в Telegram.

        Returns:
            tuple[Subscription, str] | None: Кортеж из модели подписки и ссылки,
                                             или None, если подписка не найдена.
        """
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == tg_user_id)
            .order_by(Subscription.subscription_date.desc())
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription_link = subscription.vpn_key
            return subscription, subscription_link
        return None

    async def renew_user_subscription(self, tg_user_id: int) -> tuple[Subscription, str]:
        """
        Продлевает подписку пользователя на 1 год.

        Args:
            tg_user_id (int): ID пользователя в Telegram.

        Returns:
            tuple[Subscription, str]: Кортеж из обновленной/новой модели подписки и ссылки на подписку.

        Raises:
            Exception: Если у пользователя нет активной подписки или возникли ошибки API/БД.
        """
        logger.info(f"Попытка продления подписки для TG ID: {tg_user_id}")

        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == tg_user_id)
            .order_by(Subscription.subscription_date.desc())
        )
        current_subscription = result.scalar_one_or_none()

        if not current_subscription:
            logger.info(f"У пользователя TG ID: {tg_user_id} нет подписки для продления.")
            raise Exception("У вас нет активной подписки для продления.")

        rem_sub_uuid = current_subscription.vpn_id
        if not rem_sub_uuid:
            logger.error(f"UUID подписки Remnawave не найден для TG ID: {tg_user_id}")
            raise Exception("Ошибка: UUID подписки не найден в локальной БД.")

        now = datetime.now(timezone.utc)
        current_expiry = current_subscription.subscription_date
        base_date_for_renewal = max(now, current_expiry)
        new_expiry_date = base_date_for_renewal + constants.RENEWAL_DELTA

        logger.info(f"Новая дата окончания подписки для TG ID: {tg_user_id} будет {new_expiry_date}")

        async with RemnawaveAPI() as remnawave:
            try:
                await remnawave.renew_subscription(
                    subscription_uuid=rem_sub_uuid,
                    new_expiry_date=new_expiry_date,
                )
                logger.info(f"Подписка для TG ID: {tg_user_id} успешно продлена в Remnawave API.")
            except Exception as e:
                logger.error(f"Ошибка при продлении подписки в Remnawave API для TG ID: {tg_user_id}: {e}")
                raise Exception(f"Ошибка продления в Remnawave: {e}")

            current_subscription.subscription_date = new_expiry_date
            self.db.add(current_subscription)
            await self.db.commit()
            await self.db.refresh(current_subscription)
            logger.info(f"Подписка для TG ID: {tg_user_id} успешно обновлена в локальной БД.")

        subscription_link = current_subscription.vpn_key
        return current_subscription, subscription_link
