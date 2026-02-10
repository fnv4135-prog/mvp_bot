# bots/content_bot.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging
import aiohttp
import json

router = Router()
logger = logging.getLogger(__name__)

# Если есть OpenAI API ключ - используем его, иначе заглушка
try:
    from core.config import OPENAI_API_KEY

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# Состояния для FSM
class ContentGen(StatesGroup):
    waiting_for_topic = State()
    waiting_for_platform = State()
    waiting_for_style = State()


# Шаблоны промптов для разных платформ
PLATFORM_PROMPTS = {
    "telegram": "Напиши пост для Telegram канала на тему: {topic}. Пост должен быть информативным, с эмодзи, хештегами и призывом к действию. Длина: 2-3 абзаца.",
    "instagram": "Напиши пост для Instagram на тему: {topic}. Включи подпись с хештегами (10-15 хештегов), эмодзи и призыв к действию. Длина: 150-250 слов.",
    "vk": "Напиши пост для ВКонтакте на тему: {topic}. Используй неформальный стиль, эмодзи, хештеги. Можно добавить вопрос для вовлечения аудитории. Длина: 200-300 слов.",
    "twitter": "Напиши твит на тему: {topic}. Ограничение: 280 символов. Используй хештеги, эмодзи. Сделай цепляющим.",
    "blog": "Напиши статью для блога на тему: {topic}. Структура: введение, основная часть (3-5 пунктов), заключение. Длина: 500-700 слов."
}


def get_start_keyboard():
    """Клавиатура для начала работы"""
    buttons = [
        [InlineKeyboardButton(text="📝 Сгенерировать пост", callback_data="generate_post")],
        [InlineKeyboardButton(text="📋 Шаблоны постов", callback_data="templates")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_content")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_platform_keyboard():
    """Клавиатура для выбора платформы"""
    buttons = [
        [InlineKeyboardButton(text="📱 Telegram", callback_data="platform_telegram"),
         InlineKeyboardButton(text="📸 Instagram", callback_data="platform_instagram")],
        [InlineKeyboardButton(text="🌐 ВКонтакте", callback_data="platform_vk"),
         InlineKeyboardButton(text="🐦 Twitter", callback_data="platform_twitter")],
        [InlineKeyboardButton(text="📝 Блог", callback_data="platform_blog")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def generate_with_openai(prompt: str) -> str:
    """Генерация текста через OpenAI API"""
    if not HAS_OPENAI:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenAI API error: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return None


def generate_fake_content(prompt: str) -> str:
    """Заглушка для генерации контента (если нет OpenAI API)"""
    # Примеры сгенерированного контента
    examples = {
        "telegram": """🚀 **Новый тренд в digital-маркетинге!**

В 2025 году на первый план выходит персонализированный контент. Вот что нужно знать:

• **AI-ассистенты** помогают создавать уникальный контент для каждого пользователя
• **Видеоформаты** доминируют в соцсетях (Reels, Shorts, TikTok)
• **Интерактивность** - ключ к вовлечению (опросы, квизы, игры)

🔥 Совет: Начните тестировать AI-инструменты уже сегодня!

#маркетинг #тренды2025 #digital #контент #AI""",

        "instagram": """✨ Персонализированный контент - новый must-have в digital! 🎯

Главные тренды 2025 года:
✅ AI-помощники для создания уникального контента
✅ Короткие видео - короли соцсетей
✅ Интерактивные форматы для максимального вовлечения

💡 Не отставайте - тестируйте новые инструменты уже сейчас!

Что думаете о этих трендах? 👇

#тренды2025 #digitalмаркетинг #контент #соцсети #instagram #маркетинг #SMM #AI""",

        "blog": """# Персонализированный контент: главный тренд digital-маркетинга 2025 года

## Введение
В быстро меняющемся мире digital-маркетинга 2025 год приносит новые вызовы и возможности. Ключевой тренд, который определяет успех брендов - это персонализированный контент.

## Основная часть

### 1. AI-ассистенты в создании контента
Современные инструменты на основе искусственного интеллекта позволяют создавать уникальный контент для каждой аудитории. Это больше не просто "дорого и сложно" - теперь это доступно каждому.

### 2. Доминирование видеоформатов
Reels, Shorts, TikTok - эти платформы определяют правила игры. Короткие, динамичные видео захватывают внимание пользователей лучше любого текста.

### 3. Интерактивность как стандарт
Опросы, квизы, интерактивные истории - пользователи хотят участвовать, а не просто потреблять.

## Заключение
Персонализация контента перестала быть опцией и стала необходимостью. Бренды, которые внедряют эти технологии сегодня, будут лидерами завтра."""
    }

    # Определяем, для какой платформы генерируем
    for platform in ["telegram", "instagram", "vk", "twitter", "blog"]:
        if platform in prompt.lower():
            return examples.get(platform, examples["telegram"])

    return examples["telegram"]


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Начало работы с контент-ботом"""
    await state.clear()
    await message.answer(
        "📝 **Контент-завод**\n\n"
        "Я помогаю создавать контент для социальных сетей и блогов.\n\n"
        "Что я умею:\n"
        "• Генерировать посты для разных платформ\n"
        "• Предлагать шаблоны и идеи\n"
        "• Адаптировать стиль под вашу аудиторию\n\n"
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "generate_post")
async def start_generation(callback: CallbackQuery, state: FSMContext):
    """Начало генерации поста"""
    await callback.message.edit_text(
        "📝 **Генерация поста**\n\n"
        "Напишите тему для поста (например: \"Запуск нового продукта\", \"Итоги месяца\", \"Промо акция\"):"
    )
    await state.set_state(ContentGen.waiting_for_topic)
    await callback.answer()


@router.message(ContentGen.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    """Обработка темы поста"""
    await state.update_data(topic=message.text)
    await message.answer(
        f"✅ Тема: **{message.text}**\n\n"
        "Теперь выберите платформу для которой нужен пост:",
        reply_markup=get_platform_keyboard()
    )
    await state.set_state(ContentGen.waiting_for_platform)


@router.callback_query(F.data.startswith("platform_"))
async def process_platform(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора платформы"""
    platform = callback.data.replace("platform_", "")
    platform_names = {
        "telegram": "Telegram",
        "instagram": "Instagram",
        "vk": "ВКонтакте",
        "twitter": "Twitter",
        "blog": "Блог"
    }

    await state.update_data(platform=platform)
    data = await state.get_data()

    # Генерируем контент
    await callback.message.edit_text("🔄 Генерирую контент...")

    prompt = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS["telegram"]).format(topic=data["topic"])

    # Пытаемся использовать OpenAI, если есть ключ
    if HAS_OPENAI:
        content = await generate_with_openai(prompt)
    else:
        content = generate_fake_content(platform)

    if content:
        # Сохраняем результат
        await state.update_data(content=content)

        # Показываем результат
        await callback.message.edit_text(
            f"✅ **Готово!**\n\n"
            f"**Платформа:** {platform_names.get(platform, platform)}\n"
            f"**Тема:** {data['topic']}\n\n"
            f"**Ваш пост:**\n\n{content}\n\n"
            f"---\n"
            f"Что дальше?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Новый пост", callback_data="generate_post")],
                [InlineKeyboardButton(text="💾 Сохранить", callback_data="save_content")],
                [InlineKeyboardButton(text="📋 В главное меню", callback_data="main_menu")]
            ])
        )
    else:
        await callback.message.edit_text(
            "😕 Не удалось сгенерировать контент. Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="generate_post")]
            ])
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "templates")
async def show_templates(callback: CallbackQuery):
    """Показать шаблоны постов"""
    templates_text = (
        "📋 **Шаблоны постов**\n\n"
        "1. **Анонс продукта:**\n"
        "   - Проблема, которую решает продукт\n"
        "   - Ключевые преимущества\n"
        "   - Призыв к действию (предзаказ/демо)\n\n"
        "2. **Кейс клиента:**\n"
        "   - Ситуация «до»\n"
        "   - Решение (наш продукт)\n"
        "   - Результат «после» с цифрами\n\n"
        "3. **Экспертное мнение:**\n"
        "   - Актуальная тема в нише\n"
        "   - Анализ/прогноз\n"
        "   - Совет для аудитории\n\n"
        "4. **Промо-акция:**\n"
        "   - Ограниченное предложение\n"
        "   - Условия участия\n"
        "   - Дедлайн\n\n"
        "Используйте эти шаблоны как основу для ваших постов!"
    )

    await callback.message.edit_text(
        templates_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Сгенерировать пост", callback_data="generate_post")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
        ])
    )


@router.callback_query(F.data == "about_content")
async def about_content_bot(callback: CallbackQuery):
    """Информация о контент-боте"""
    about_text = (
        "ℹ️ **О контент-боте**\n\n"
        "Это демо-версия бота для генерации контента.\n\n"
        "**Возможности:**\n"
        "• Генерация постов для 5+ платформ\n"
        "• Шаблоны и структуры постов\n"
        "• Адаптация под разные стили\n\n"
        "**Технологии:**\n"
        "• Python + aiogram\n"
        "• OpenAI GPT API (если настроен)\n"
        "• FSM для управления диалогом\n\n"
        "Для реального использования требуется настройка OpenAI API ключа."
    )

    await callback.message.edit_text(
        about_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Сгенерировать пост", callback_data="generate_post")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
        ])
    )


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена и возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()


def setup_content_bot(dp):
    """Настройка контент-бота"""
    dp.include_router(router)
    print("✅ Content bot setup complete")