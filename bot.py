import asyncio
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

import config
from app.database import async_session_maker, init_database
from app.services.user_service import UserService
from constants import (
    BUTTON_CREATE_USER,
    BUTTON_GET_KEY,
    BUTTON_RENEW_KEY,
    CALLBACK_CREATE_USER,
    CALLBACK_GET_KEY,
    CALLBACK_RENEW_KEY,
    DATE_FORMAT,
    MSG_BOT_WELCOME,
    MSG_KEY_ERROR,
    MSG_NO_SUBSCRIPTION,
    MSG_RENEW_ERROR,
    MSG_USER_CREATED,
    MSG_USER_CREATION_ERROR,
    PARSE_MODE_HTML,
    SUBSCRIPTION_INFO_TEMPLATE,
    SUBSCRIPTION_RENEWED_TEMPLATE,
    UNKNOWN_VALUE,
)


def validate_config():
    if not config.BOT_TOKEN:
        logger.warning(
            "TELEGRAM_BOT_TOKEN не установлен! Установите его в .env файле"
        )
        logger.info("Пример: TELEGRAM_BOT_TOKEN=your_token_here")

    if not config.REMNAWAVE_API_TOKEN:
        logger.warning(
            "REMNAWAVE_API_TOKEN не установлен! Установите его в .env файле"
        )
        logger.info("Пример: REMNAWAVE_API_TOKEN=your_token_here")

    logger.info("Запуск приложения...")


validate_config()

if config.BOT_TOKEN:
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
else:
    logger.error("Невозможно запустить бота без BOT_TOKEN")
    sys.exit(1)


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=BUTTON_CREATE_USER, callback_data=CALLBACK_CREATE_USER
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTON_GET_KEY, callback_data=CALLBACK_GET_KEY
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTON_RENEW_KEY, callback_data=CALLBACK_RENEW_KEY
                )
            ],
        ]
    )
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

    await message.answer(
        MSG_BOT_WELCOME,
        reply_markup=get_main_keyboard(),
    )


@dp.callback_query(lambda c: c.data == CALLBACK_CREATE_USER)
async def process_create_user(callback_query: types.CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    logger.info(f"Пользователь {user_id} нажал кнопку 'Создать пользователя'")

    await callback_query.message.answer("Создаю нового пользователя...")

    try:
        async with async_session_maker() as session:
            user_service = UserService(session)
            await user_service.create_user_and_subscription(
                tg_user_id=user_id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
            )

            await callback_query.message.answer(
                MSG_USER_CREATED, parse_mode=PARSE_MODE_HTML
            )
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        await callback_query.message.answer(MSG_USER_CREATION_ERROR)

    await callback_query.answer()


@dp.callback_query(lambda c: c.data == CALLBACK_GET_KEY)
async def process_get_key(callback_query: types.CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    logger.info(f"Пользователь {user_id} нажал кнопку 'Получить ключ'")

    try:
        async with async_session_maker() as session:
            user_service = UserService(session)

            result = await user_service.get_user_subscription(user_id)

            if result:
                subscription, subscription_link = result
                end_date_str = UNKNOWN_VALUE
                if subscription.subscription_date:
                    end_date_str = subscription.subscription_date.strftime(
                        DATE_FORMAT
                    )

                await callback_query.message.answer(
                    SUBSCRIPTION_INFO_TEMPLATE.format(
                        subscription_link=subscription_link,
                        end_date=end_date_str,
                    ),
                    parse_mode=PARSE_MODE_HTML,
                )
            else:
                await callback_query.message.answer(
                    MSG_NO_SUBSCRIPTION,
                    parse_mode=PARSE_MODE_HTML,
                )
    except Exception as e:
        logger.error(f"Ошибка при получении ключа: {e}")
        await callback_query.message.answer(MSG_KEY_ERROR)

    await callback_query.answer()


@dp.callback_query(lambda c: c.data == CALLBACK_RENEW_KEY)
async def process_renew_key(callback_query: types.CallbackQuery) -> None:
    user_id = callback_query.from_user.id
    logger.info(f"Пользователь {user_id} нажал кнопку 'Продлить ключ'")

    try:
        async with async_session_maker() as session:
            user_service = UserService(session)

            (
                _,
                subscription,
                subscription_link,
            ) = await user_service.create_user_and_subscription(
                tg_user_id=user_id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
            )

            end_date_str = UNKNOWN_VALUE
            if subscription.subscription_date:
                end_date_str = subscription.subscription_date.strftime(
                    DATE_FORMAT
                )

            await callback_query.message.answer(
                SUBSCRIPTION_RENEWED_TEMPLATE.format(
                    subscription_link=subscription_link, end_date=end_date_str
                ),
                parse_mode=PARSE_MODE_HTML,
            )
    except Exception as e:
        logger.error(f"Ошибка при продлении ключа: {e}")
        await callback_query.message.answer(MSG_RENEW_ERROR)

    await callback_query.answer()


async def main() -> None:
    logger.info("Запуск бота...")

    await init_database()

    logger.info("Бот запущен и готов к работе")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
