import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# === ВЫБОР РЕЖИМА БОТА (МЕНЯТЬ ЗДЕСЬ!) ===
DEMO_MODE = "subscription"  # "subscription" | "info" | "content"

# Загрузка выбранного бота
if DEMO_MODE == "subscription":
    from bots.subscription_bot import setup_subscription_bot

    setup_subscription_bot(dp)
    bot_name = "Бот подписок"

elif DEMO_MODE == "info":
    from bots.info_bot import setup_info_bot

    setup_info_bot(dp)
    bot_name = "Инфо-бот с партнёрками"

elif DEMO_MODE == "content":
    from bots.content_bot import setup_content_bot

    setup_content_bot(dp)
    bot_name = "Контент-завод"

else:
    bot_name = "Неизвестный режим"

logger.info(f"🚀 Загружен режим: {bot_name}")


# === ВЕБХУКИ И HEALTH CHECK ===
async def health_check(request):
    """Простой health check для Uptime Robot"""
    return web.Response(text=f"OK - {bot_name}")


async def on_startup(app):
    """Действия при запуске бота"""
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")


async def on_shutdown(app):
    """Действия при остановке бота"""
    await bot.delete_webhook()
    logger.info("Бот остановлен")


def main():
    """Основная функция запуска"""
    app = web.Application()

    # Регистрируем health check
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    # Регистрируем вебхук для бота
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path="/webhook")

    # События запуска/остановки
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Запускаем сервер
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Запуск сервера на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()