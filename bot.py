import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
import config  # type: ignore
import constants  # type: ignore
from app.database import AsyncSessionLocal, Base, engine
from app.services.user_service import UserService  # type: ignore
from app.utils.logger import get_logger  # type: ignore

logger = get_logger(__name__)

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обработчик команды /start.

    Args:
        message (Message): Входящее сообщение от пользователя.
    """
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await send_main_menu(message)

async def send_main_menu(message: Message):
    """
    Отправляет главное меню с кнопками пользователю.

    Args:
        message (Message): Сообщение, в ответ на которое отправляется меню.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=constants.BUTTON_CREATE_USER, callback_data="create_user")],
        [InlineKeyboardButton(text=constants.BUTTON_GET_KEY, callback_data="get_key")],
        [InlineKeyboardButton(text=constants.BUTTON_RENEW_KEY, callback_data="renew_key")],
    ])
    await message.answer(constants.WELCOME_MESSAGE, reply_markup=keyboard)

@router.callback_query(F.data == "create_user")
async def create_user_callback(callback_query: CallbackQuery) -> None:
    """
    Обработчик нажатия кнопки 'Создать пользователя'.

    Args:
        callback_query (CallbackQuery): Callback-запрос от пользователя.
    """
    logger.info(f"Пользователь {callback_query.from_user.id} выбрал 'Создать пользователя'")
    await callback_query.answer()

    async with AsyncSessionLocal() as db_session:
        user_service = UserService(db_session)
        try:
            user, subscription, subscription_link = await user_service.create_user_and_subscription(
                tg_user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name
            )
            expiry_str = subscription.subscription_date.strftime("%Y-%m-%d %H:%M:%S UTC")
            response_text = (
                f"{constants.USER_CREATED_MESSAGE}\n\n"
                f"Ссылка: `{subscription_link}`\n\n"
                f"Окончание подписки: {expiry_str}"
            )
            await callback_query.message.answer(response_text, parse_mode='Markdown')
            logger.info(f"Ключ успешно создан и отправлен пользователю {callback_query.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя/подписки для {callback_query.from_user.id}: {e}")
            await callback_query.message.answer(constants.ERROR_MESSAGE)

@router.callback_query(F.data == "get_key")
async def get_key_callback(callback_query: CallbackQuery) -> None:
    """
    Обработчик нажатия кнопки 'Получить ключ'.

    Args:
        callback_query (CallbackQuery): Callback-запрос от пользователя.
    """
    logger.info(f"Пользователь {callback_query.from_user.id} выбрал 'Получить ключ'")
    await callback_query.answer()

    async with AsyncSessionLocal() as db_session:
        user_service = UserService(db_session)
        try:
            result = await user_service.get_user_subscription(callback_query.from_user.id)
            if result:
                subscription, subscription_link = result
                expiry_str = subscription.subscription_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                response_text = (
                    f"{constants.KEY_RETRIEVED_MESSAGE}\n\n"
                    f"Ссылка: `{subscription_link}`\n\n"
                    f"Окончание подписки: {expiry_str}"
                )
                await callback_query.message.answer(response_text, parse_mode='Markdown')
                logger.info(f"Ключ успешно отправлен пользователю {callback_query.from_user.id}")
            else:
                await callback_query.message.answer(constants.NO_SUBSCRIPTION_MESSAGE)
                logger.info(f"У пользователя {callback_query.from_user.id} нет подписки")
        except Exception as e:
            logger.error(f"Ошибка при получении ключа для {callback_query.from_user.id}: {e}")
            await callback_query.message.answer(constants.ERROR_MESSAGE)

@router.callback_query(F.data == "renew_key")
async def renew_key_callback(callback_query: CallbackQuery) -> None:
    """
    Обработчик нажатия кнопки 'Продлить ключ'.

    Args:
        callback_query (CallbackQuery): Callback-запрос от пользователя.
    """
    logger.info(f"Пользователь {callback_query.from_user.id} выбрал 'Продлить ключ'")
    await callback_query.answer()

    async with AsyncSessionLocal() as db_session:
        user_service = UserService(db_session)
        try:
            subscription, subscription_link = await user_service.renew_user_subscription(callback_query.from_user.id)
            new_expiry_str = subscription.subscription_date.strftime("%Y-%m-%d %H:%M:%S UTC")
            response_text = (
                f"{constants.KEY_RENEWED_MESSAGE} {new_expiry_str}\n\n"
                f"Ссылка: `{subscription_link}`"
            )
            await callback_query.message.answer(response_text, parse_mode='Markdown')
            logger.info(f"Ключ успешно продлен для пользователя {callback_query.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при продлении ключа для {callback_query.from_user.id}: {e}")
            if "нет активной подписки" in str(e).lower():
                await callback_query.message.answer(constants.NO_SUBSCRIPTION_MESSAGE)
            else:
                await callback_query.message.answer(constants.ERROR_MESSAGE)

async def main() -> None:
    """Главная асинхронная функция для запуска бота."""
    logger.info("Запуск бота...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы БД проверены/созданы")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Бот запущен и ожидает сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())