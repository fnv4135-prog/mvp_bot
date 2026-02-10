from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from datetime import datetime
import logging

from core.database import db

router = Router()
logger = logging.getLogger(__name__)


# Вспомогательные функции для клавиатур
def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(text="🎁 Попробовать бесплатно", callback_data="get_trial")],
        [InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="📊 Мой доступ", callback_data="my_access")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu() -> InlineKeyboardMarkup:
    """Кнопка назад в меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 500₽", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])


# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Создаем пользователя если его нет
    if not db.get_user(user_id):
        db.create_user(user_id, message.from_user.username)
        await message.answer(
            "👋 Добро пожаловать!\n"
            "Я бот для управления подписками на сетевой сервис.\n\n"
            "Что я умею:\n"
            "• Выдать пробный период на 3 дня\n"
            "• Продать подписку на 1 месяц\n"
            "• Показать статус вашего доступа\n"
            "• Ответить на вопросы\n\n"
            "Выберите действие в меню ниже:",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "С возвращением! Что вы хотите сделать?",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "get_trial")
async def trial_handler(callback: CallbackQuery):
    """Выдача trial периода"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)

    if not user:
        db.create_user(user_id, callback.from_user.username)
        user = db.get_user(user_id)

    if user["trial_used"]:
        await callback.message.edit_text(
            "❌ Вы уже использовали пробный период.\n"
            "Приобретите платную подписку, чтобы продолжить пользоваться сервисом.",
            reply_markup=get_back_to_menu()
        )
    else:
        db.set_trial_used(user_id, days=3)
        await callback.message.edit_text(
            "✅ Вам выдан пробный период на 3 дня!\n\n"
            "Теперь у вас есть доступ ко всем функциям сервиса.\n"
            "По окончании пробного периода вы сможете приобрести платную подписку.",
            reply_markup=get_back_to_menu()
        )


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription_handler(callback: CallbackQuery):
    """Покупка подписки"""
    await callback.message.edit_text(
        "💳 **Покупка подписки**\n\n"
        "Подписка на 1 месяц дает вам:\n"
        "• Полный доступ к сервису\n"
        "• Приоритетную поддержку\n"
        "• Все будущие обновления\n\n"
        "Стоимость: **500₽**\n\n"
        "После оплаты вы мгновенно получите доступ.",
        reply_markup=get_payment_keyboard()
    )


@router.callback_query(F.data == "confirm_payment")
async def confirm_payment_handler(callback: CallbackQuery):
    """Подтверждение оплаты (заглушка)"""
    user_id = callback.from_user.id

    # В реальном боте здесь будет интеграция с платежной системой
    # Для демо просто активируем подписку
    db.set_paid_subscription(user_id, days=30)
    db.add_payment(user_id, 500, "Подписка на 1 месяц")

    await callback.message.edit_text(
        "✅ **Оплата прошла успешно!**\n\n"
        "Ваша подписка активирована на 30 дней.\n"
        "Теперь у вас есть полный доступ ко всем функциям сервиса.\n\n"
        "Спасибо за покупку! 🎉",
        reply_markup=get_back_to_menu()
    )


@router.callback_query(F.data == "my_access")
async def my_access_handler(callback: CallbackQuery):
    """Проверка статуса доступа"""
    user_id = callback.from_user.id
    status = db.get_user_status(user_id)

    if status["active"]:
        if status["type"] == "trial":
            message_text = (
                "🎁 **Пробный период активен**\n\n"
                f"Осталось дней: **{status['days_left']}**\n"
                "Рекомендуем приобрести подписку до окончания trial."
            )
        else:  # paid
            message_text = (
                "✅ **Подписка активна**\n\n"
                f"Осталось дней: **{status['days_left']}**\n"
                "У вас полный доступ ко всем функциям."
            )
    else:
        message_text = (
            "❌ **Нет активного доступа**\n\n"
            "У вас нет активной подписки или пробного периода.\n"
            "Используйте меню для получения доступа."
        )

    # Добавляем кнопку "Получить конфиг" если доступ есть
    keyboard_buttons = []
    if status["active"]:
        keyboard_buttons.append(
            [InlineKeyboardButton(text="📄 Получить конфигурацию", callback_data="get_config")]
        )
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )


@router.callback_query(F.data == "get_config")
async def get_config_handler(callback: CallbackQuery):
    """Получение конфигурации"""
    # В реальном боте здесь запрос к backend API
    # Для демо генерируем тестовую конфигурацию
    fake_config = """# Конфигурация для подключения
server: vpn.example.com
port: 1194
protocol: udp
cipher: AES-256-CBC
auth: SHA512
key-direction: 1
remote-cert-tls: server

<ca>
-----BEGIN CERTIFICATE-----
FAKE_CERTIFICATE_FOR_DEMO_ONLY
-----END CERTIFICATE-----
</ca>"""

    await callback.message.answer(
        f"📄 **Ваша конфигурация:**\n\n"
        f"```\n{fake_config}\n```\n\n"
        "Скопируйте этот текст в файл config.ovpn",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к статусу", callback_data="my_access")]
        ])
    )

    await callback.answer("Конфигурация отправлена в чат")


@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    """Поддержка"""
    await callback.message.edit_text(
        "🆘 **Поддержка**\n\n"
        "Если у вас возникли проблемы:\n\n"
        "1. Опишите проблему в этом чате\n"
        "2. Администратор ответит в течение 24 часов\n"
        "3. Для срочных вопросов: @NicholasBiz\n\n"
        "Напишите ваш вопрос ниже:",
        reply_markup=get_back_to_menu()
    )


def get_back_to_menu() -> InlineKeyboardMarkup:
    """Кнопка назад в меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]
    ])


@router.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):
    """О боте"""
    await callback.message.edit_text(
        "ℹ️ **О боте**\n\n"
        "Это демо-версия бота для управления подписками.\n\n"
        "**Реализованные функции:**\n"
        "• Регистрация пользователей\n"
        "• Пробный период (3 дня)\n"
        "• Покупка подписки (демо-оплата)\n"
        "• Проверка статуса доступа\n"
        "• Выдача конфигурации\n"
        "• Поддержка\n\n"
        "**Технологии:** Python, aiogram, SQLite",
        reply_markup=get_back_to_menu()
    )


def setup_subscription_bot(dp):
    """Настройка бота подписок"""
    dp.include_router(router)
    print("✅ Subscription bot setup complete")