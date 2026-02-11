from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
import logging

router = Router()
logger = logging.getLogger(__name__)

# База данных рекомендаций (товары + партнёрские ссылки)
RECOMMENDATIONS = {
    "gaming": {
        "budget_low": {
            "name": "Игровая мышь Redragon Griffin",
            "description": "Игровая мышь с RGB-подсветкой, 5 кнопок, 7200 DPI",
            "price": "1 890₽",
            "link": "https://www.wildberries.ru/catalog/12345678/detail.aspx"
        },
        "budget_medium": {
            "name": "Игровая клавиатура A4Tech Bloody",
            "description": "Механическая клавиатура с красными свичами, подсветка",
            "price": "4 590₽",
            "link": "https://www.ozon.ru/product/123456789/"
        },
        "budget_high": {
            "name": "Игровой ноутбук ASUS TUF Gaming",
            "description": "15.6\", RTX 4050, 16 ГБ ОЗУ, 512 ГБ SSD",
            "price": "89 990₽",
            "link": "https://www.dns-shop.ru/product/123456789/"
        }
    },
    "work": {
        "budget_low": {
            "name": "Наушники Sony MDR-ZX110",
            "description": "Проводные наушники для офиса, складная конструкция",
            "price": "990₽",
            "link": "https://www.wildberries.ru/catalog/87654321/detail.aspx"
        },
        "budget_medium": {
            "name": "Монитор Samsung 24\"",
            "description": "Монитор с IPS матрицей, 75 Гц, HDMI",
            "price": "12 990₽",
            "link": "https://www.ozon.ru/product/987654321/"
        },
        "budget_high": {
            "name": "Ноутбук Apple MacBook Air M1",
            "description": "13.3\", 8 ГБ ОЗУ, 256 ГБ SSD, macOS",
            "price": "89 990₽",
            "link": "https://www.dns-shop.ru/product/987654321/"
        }
    }
}


def get_start_keyboard():
    """Клавиатура для выбора цели"""
    buttons = [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="goal_gaming")],
        [InlineKeyboardButton(text="💼 Работа", callback_data="goal_work")],
        [InlineKeyboardButton(text="🎵 Медиа/Стриминг", callback_data="goal_media")],
        [InlineKeyboardButton(text="🖥️ Комплектующие", callback_data="goal_components")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_budget_keyboard(goal: str):
    """Клавиатура для выбора бюджета"""
    buttons = [
        [InlineKeyboardButton(text="💰 До 5 000₽", callback_data=f"budget_{goal}_low")],
        [InlineKeyboardButton(text="💸 5 000 - 30 000₽", callback_data=f"budget_{goal}_medium")],
        [InlineKeyboardButton(text="💎 От 30 000₽", callback_data=f"budget_{goal}_high")],
        [InlineKeyboardButton(text="🔙 Назад к выбору цели", callback_data="back_to_goal")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("goal_"))
async def goal_handler(callback: CallbackQuery):
    """Обработчик выбора цели"""
    goal = callback.data.replace("goal_", "")
    goal_names = {
        "gaming": "🎮 Игры",
        "work": "💼 Работа",
        "media": "🎵 Медиа/Стриминг",
        "components": "🖥️ Комплектующие"
    }

    await callback.message.edit_text(
        f"**Цель: {goal_names.get(goal, goal)}**\n\n"
        "Теперь выберите ваш бюджет:",
        reply_markup=get_budget_keyboard(goal)
    )


@router.callback_query(F.data.startswith("budget_"))
async def budget_handler(callback: CallbackQuery):
    """Обработчик выбора бюджета и вывод рекомендации"""
    # Разбираем данные: budget_goal_level
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Ошибка выбора")
        return

    goal = parts[1]
    budget_level = parts[2]

    # Получаем рекомендацию
    if goal in RECOMMENDATIONS and budget_level in RECOMMENDATIONS[goal]:
        item = RECOMMENDATIONS[goal][budget_level]

        # Формируем сообщение
        message_text = (
            f"🎯 **Рекомендация:** {item['name']}\n\n"
            f"📝 **Описание:** {item['description']}\n"
            f"💰 **Цена:** {item['price']}\n\n"
            "Для покупки перейдите по ссылке ниже 👇"
        )

        # Клавиатура с партнёрской ссылкой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Перейти к товару", url=item['link'])],
            [InlineKeyboardButton(text="🔄 Новый подбор", callback_data="new_search")],
            [InlineKeyboardButton(text="📋 Все рекомендации", callback_data="all_recommendations")]
        ])

        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "😕 К сожалению, для выбранных параметров нет рекомендаций.\n"
            "Попробуйте другие настройки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Новый подбор", callback_data="new_search")]
            ])
        )


@router.callback_query(F.data == "back_to_goal")
async def back_to_goal_handler(callback: CallbackQuery):
    """Возврат к выбору цели"""
    await callback.message.edit_text(
        "**Выберите основную цель использования:**",
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "new_search")
async def new_search_handler(callback: CallbackQuery):
    """Начать новый подбор"""
    await callback.message.edit_text(
        "**Выберите основную цель использования:**",
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "all_recommendations")
async def all_recommendations_handler(callback: CallbackQuery):
    """Показать все рекомендации по категориям"""
    text = "📋 **Все рекомендации по категориям:**\n\n"

    for goal_name, items in RECOMMENDATIONS.items():
        if goal_name == "gaming":
            text += "🎮 **Для игр:**\n"
        elif goal_name == "work":
            text += "💼 **Для работы:**\n"

        for level, item in items.items():
            text += f"• {item['name']} - {item['price']}\n"
        text += "\n"

    text += "\nДля подбора под ваши параметры нажмите /start"

    await callback.message.answer(text)


def setup_info_bot(dp):
    """Настройка инфо-бота"""
    dp.include_router(router)
    print("✅ Info bot setup complete")


async def show_start_menu(message):
    """Показывает стартовое меню инфо-бота"""
    await message.answer(
        "🛒 **Подбор оборудования**\n\n"
        "Я помогу подобрать технику по вашим потребностям и бюджету.\n"
        "Все рекомендации содержат партнёрские ссылки на проверенные магазины.\n\n"
        "**Для начала выберите основную цель использования:**",
        reply_markup=get_start_keyboard()
    )