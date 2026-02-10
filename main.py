import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer('✅ Бот работает! MVP готов к разработке.')

@dp.message(Command('menu'))
async def menu(message: types.Message):
    await message.answer('Главное меню:\n1. Функция 1\n2. Функция 2')

async def main():
    logger.info('Бот запущен!')
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())