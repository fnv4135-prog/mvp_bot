import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# === ХРАНЕНИЕ ТЕКУЩЕГО РЕЖИМА ДЛЯ КАЖДОГО ПОЛЬЗОВАТЕЛЯ ===
user_modes = {}  # {user_id: "subscription"/"info"/"content"}


# === КЛАВИАТУРА ДЛЯ ВЫБОРА РЕЖИМА ===
def get_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора режима бота"""
    buttons = [
        [InlineKeyboardButton(text="🤖 Бот подписок", callback_data="mode_subscription")],
        [InlineKeyboardButton(text="🛒 Инфо-бот с партнёрками", callback_data="mode_info")],
        [InlineKeyboardButton(text="📝 Контент-завод", callback_data="mode_content")],
        [InlineKeyboardButton(text="ℹ️ О портфолио", callback_data="mode_about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# === ГЛАВНЫЕ КОМАНДЫ ===
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Главное меню с выбором режима"""
    user_id = message.from_user.id

    # По умолчанию - бот подписок
    if user_id not in user_modes:
        user_modes[user_id] = "subscription"

    await message.answer(
        "🚀 **Портфолио Telegram-ботов**\n\n"
        "Выберите демо-бот для тестирования:\n\n"
        "• **🤖 Бот подписок** - полный цикл продажи подписок\n"
        "• **🛒 Инфо-бот** - подбор товаров с партнёрскими ссылками\n"
        "• **📝 Контент-завод** - генерация постов через AI\n\n"
        "Вы можете переключаться между ботами в любой момент!",
        reply_markup=get_mode_keyboard()
    )


@dp.message(Command("mode"))
async def cmd_mode(message: Message):
    """Смена режима бота"""
    await message.answer(
        "🔄 **Смена режима бота**\n\n"
        "Выберите, какой бот вы хотите использовать:",
        reply_markup=get_mode_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    user_id = message.from_user.id
    current_mode = user_modes.get(user_id, "subscription")

    mode_names = {
        "subscription": "Бот подписок",
        "info": "Инфо-бот с партнёрками",
        "content": "Контент-завод"
    }

    await message.answer(
        f"ℹ️ **Справка**\n\n"
        f"**Текущий режим:** {mode_names.get(current_mode)}\n"
        f"**Ваш ID:** {user_id}\n\n"
        "**Команды:**\n"
        "/start - Главное меню\n"
        "/mode - Сменить режим бота\n"
        "/help - Эта справка\n\n"
        "**Как использовать:**\n"
        "1. Выберите режим бота из меню\n"
        "2. Начните работу с выбранным функционалом\n"
        "3. В любой момент можете сменить режим командой /mode"
    )


# === ОБРАБОТЧИКИ ВЫБОРА РЕЖИМА ===
@dp.callback_query(F.data.startswith("mode_"))
async def mode_handler(callback: CallbackQuery):
    """Обработчик выбора режима"""
    user_id = callback.from_user.id
    mode = callback.data.replace("mode_", "")

    mode_names = {
        "subscription": "🤖 Бот подписок",
        "info": "🛒 Инфо-бот с партнёрками",
        "content": "📝 Контент-завод",
        "about": "ℹ️ О портфолио"
    }

    if mode == "about":
        await callback.message.edit_text(
            "🎯 **Портфолио Telegram-ботов**\n\n"
            "Это демонстрационный проект, показывающий различные типы Telegram-ботов:\n\n"
            "• **Бот подписок** - полный цикл продаж (trial, оплата, выдача доступа)\n"
            "• **Инфо-бот** - рекомендательная система с партнёрскими ссылками\n"
            "• **Контент-завод** - генерация контента с помощью AI\n\n"
            "**Технологии:** Python, aiogram, aiohttp, вебхуки\n"
            "**Хостинг:** Render + Uptime Robot\n\n"
            "Все боты полностью рабочие и готовы к интеграции в реальные проекты.",
            reply_markup=get_mode_keyboard()
        )
        return

    # Сохраняем выбранный режим
    user_modes[user_id] = mode

    # 🔔 Отправляем всплывающее уведомление
    await callback.answer(
        f"✅ Переключено на {mode_names[mode]}",
        show_alert=True
    )

    # Загружаем соответствующий бот
    await load_bot_mode(callback, mode, mode_names[mode])


async def load_bot_mode(callback: CallbackQuery, mode: str, mode_name: str):
    """Динамическая загрузка выбранного бота"""

    if mode == "subscription":
        # Очищаем предыдущие хэндлеры
        from bots.subscription_bot import router as subscription_router
        # Удаляем старые хэндлеры (упрощенный способ - перезагружаем диспетчер)
        # Вместо этого просто вызываем команду /start для выбранного бота

        # 🔥 Прямой запуск бота подписок
        from bots.subscription_bot import show_main_menu
        await show_main_menu(callback.message)
        await callback.message.delete()  # Удаляем старое сообщение с выбором режима

    elif mode == "info":
        from bots.info_bot import router as info_router
        dp.include_router(info_router)

        # 🔥 Прямой запуск инфо-бота
        from bots.info_bot import show_start_menu
        await show_start_menu(callback.message)
        await callback.message.delete()

    elif mode == "content":
        from bots.content_bot import router as content_router
        dp.include_router(content_router)

        # 🔥 Прямой запуск контент-бота
        from bots.content_bot import show_start_menu as show_content_menu
        await show_content_menu(callback.message)
        await callback.message.delete()


# === ВЕБХУКИ И HEALTH CHECK ===
async def health_check(request):
    """Health check для мониторинга"""
    return web.Response(text="✅ Портфолио ботов работает")


async def on_startup(app):
    """Действия при запуске"""
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

    # По умолчанию загружаем бота подписок
    from bots.subscription_bot import router as subscription_router
    dp.include_router(subscription_router)
    logger.info("✅ Загружен бот подписок по умолчанию")


async def on_shutdown(app):
    """Действия при остановке"""
    await bot.delete_webhook()
    logger.info("Бот остановлен")


def main():
    """Запуск сервера"""
    app = web.Application()

    # Health check
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    # Вебхук для бота
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")

    # События
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Запуск
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Сервер запущен на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()