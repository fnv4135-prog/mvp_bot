import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Выбор демо-режима (subscription | info | content)
DEMO_MODE = "subscription"  # Измени эту переменную для переключения ботов

# Загрузка выбранного бота
if DEMO_MODE == "subscription":
    from bots.subscription_bot import setup_subscription_bot

    setup_subscription_bot(dp)
    bot_name = "Бот подписок"

elif DEMO_MODE == "info":
    # Будет добавлено позже
    bot_name = "Инфо-бот с партнёрками"
    from bots.info_bot import setup_info_bot

    setup_info_bot(dp)

elif DEMO_MODE == "content":
    # Будет добавлено позже
    bot_name = "Контент-завод"
    from bots.content_bot import setup_content_bot

    setup_content_bot(dp)

else:
    bot_name = "Неизвестный режим"


# Общая команда для всех режимов
@dp.message(Command("mode"))
async def show_mode(message: Message):
    """Показать текущий режим бота"""
    await message.answer(f"🔧 Текущий режим: {bot_name}\n\n"
                         f"Для смены режима измените переменную DEMO_MODE в main.py")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    await message.answer(
        f"🤖 **{bot_name}**\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Эта справка\n"
        "/mode - Показать текущий режим\n\n"
        "Используйте кнопки меню для навигации."
    )


async def main():
    """Главная функция"""
    logger.info(f"Бот запущен в режиме: {bot_name}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())