from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards.main_menu import get_main_menu, get_faq_keyboard, get_back_to_menu_keyboard, get_anonymous_post_keyboard
from models.user import UserRole
from config import ADMIN_IDS, CHANNEL_ID
from aiogram import Bot
import asyncio
import logging

router = Router()

class AnnouncementState(StatesGroup):
    waiting_for_announcement = State()

class AnonymousPostState(StatesGroup):
    waiting_for_post = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    welcome_text = """
👋 Добро пожаловать в *Подслушано*!

Здесь ты можешь анонимно делиться своими мыслями, признаниями и историями. Всё полностью конфиденциально! ✨

*Что ты можешь сделать:*
📨 • Отправить анонимный пост
🤫 • Поделиться секретом
💌 • Сделать признание
📖 • Рассказать историю

Выбери действие в меню ниже 👇
    """
    
    await message.answer(
        welcome_text,
        reply_markup=await get_main_menu(message.from_user.id),
        parse_mode="Markdown"
    )

@router.message(F.text == "📨 Отправить анонимку")
async def start_anonymous_post(message: Message, state: FSMContext):
    await message.answer(
        "📝 *Напиши свой анонимный пост*\n\n"
        "Просто напиши сюда всё, что хочешь сказать анонимно. "
        "Пост будет сразу опубликован в канале!\n\n"
        "*Правила:*\n"
        "• Минимум 10 символов\n"
        "• Без оскорблений\n"
        "• Без личной информации\n\n"
        "Или нажми '🔙 Отмена' чтобы вернуться",
        reply_markup=get_anonymous_post_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AnonymousPostState.waiting_for_post)

@router.message(AnonymousPostState.waiting_for_post)
async def process_anonymous_post(message: Message, state: FSMContext, bot: Bot):
    if message.text == "🔙 Отмена":
        await message.answer(
            "Отмена отправки.",
            reply_markup=await get_main_menu(message.from_user.id)
        )
        await state.clear()
        return
    
    post_text = message.text
    
    # Проверка длины
    if len(post_text) < 10:
        await message.answer(
            "❌ Пост слишком короткий! Нужно минимум 10 символов.\n\n"
            "Попробуй еще раз или нажми '🔙 Отмена':",
            reply_markup=get_anonymous_post_keyboard()
        )
        return
    
    # Проверка на запрещенные слова
    forbidden_words = ["мат", "оскорбление", "спам"]  # Добавь свои
    if any(word in post_text.lower() for word in forbidden_words):
        await message.answer(
            "❌ В посте найдены запрещенные слова!\n\n"
            "Попробуй еще раз или нажми '🔙 Отмена':",
            reply_markup=get_anonymous_post_keyboard()
        )
        return
    
    try:
        # Публикуем в канал
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"💌 *Анонимное признание:*\n\n{post_text}\n\n#подслушано",
            parse_mode="Markdown"
        )
        
        # Сохраняем в базу
        post_id = await db.create_anonymous_post(message.from_user.id, post_text)
        
        await message.answer(
            "✅ *Твой пост опубликован!*\n\n"
            "Теперь его могут видеть все подписчики канала 🔥\n\n"
            "Можешь отправить еще один пост или вернуться в меню:",
            reply_markup=await get_main_menu(message.from_user.id),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Ошибка публикации поста: {e}")
        await message.answer(
            "❌ *Ошибка публикации!*\n\n"
            "Не удалось опубликовать пост. Попробуй позже.",
            reply_markup=await get_main_menu(message.from_user.id),
            parse_mode="Markdown"
        )
    
    await state.clear()

@router.message(Command("announcement"))
async def announcement_command(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде!")
        return
    
    await message.answer(
        "📢 *Панель объявлений*\n\n"
        "Отправь сообщение, которое будет разослано всем пользователям бота.\n\n"
        "Просто напиши текст объявления:",
        parse_mode="Markdown"
    )
    await state.set_state(AnnouncementState.waiting_for_announcement)

@router.message(AnnouncementState.waiting_for_announcement)
async def process_announcement(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде!")
        await state.clear()
        return
    
    announcement_text = message.text
    all_users = await db.get_all_users()
    total_users = len(all_users)
    
    if total_users == 0:
        await message.answer("❌ Нет пользователей для рассылки!")
        await state.clear()
        return
    
    progress_msg = await message.answer(
        f"📤 *Начинаю рассылку...*\n\nВсего получателей: {total_users}",
        parse_mode="Markdown"
    )
    
    success_count = 0
    announcement_message = f"📢 *ОБЪЯВЛЕНИЕ*\n\n{announcement_text}\n\n_От администрации Подслушано_"
    
    for i, user_id in enumerate(all_users):
        try:
            await bot.send_message(user_id, text=announcement_message, parse_mode="Markdown")
            success_count += 1
        except:
            pass
        
        if (i + 1) % 10 == 0:
            try:
                await progress_msg.edit_text(
                    f"📤 *Рассылка...*\n\nОтправлено: {i + 1}/{total_users}",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        await asyncio.sleep(0.05)
    
    await message.answer(
        f"✅ *Рассылка завершена!*\n\nДоставлено: {success_count}/{total_users}",
        parse_mode="Markdown"
    )
    await state.clear()

# Остальные обработчики без изменений
@router.message(F.text == "❓ ФАК")
async def show_faq(message: Message):
    faq_text = "ℹ️ *Часто задаваемые вопросы*\n\nВыбери вопрос который тебя интересует:"
    await message.answer(faq_text, reply_markup=get_faq_keyboard(), parse_mode="Markdown")

@router.message(F.text == "📋 Правила")
async def show_rules(message: Message):
    rules_text = """
📋 *Правила Подслушано*:

✅ *Можно:*
• Анонимные признания
• Истории из школьной жизни
• Вопросы и советы
• Позитивные посты

❌ *Нельзя:*
• Всё можно, ну только если модерация посчитает сообщение агресивным или не по тематике канал возможно буде удаленно
    """
    await message.answer(rules_text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("faq_"))
async def handle_faq_questions(callback: CallbackQuery):
    faq_type = callback.data
    faq_answers = {
        "faq_what_is": "🤔 *Что такое анонимка?*\n\nАнонимка - это пост, который публикуется без указания твоего имени! 🔒",
        "faq_how_to_send": "📝 *Как отправить пост?*\n\n1. Нажми 'Отправить анонимку'\n2. Напиши текст\n3. Пост сразу публикуется в канале! ✨",
        "faq_time": "⏰ *Сколько ждать публикации?*\n\nПосты публикуются мгновенно! ⚡",
        "faq_rejection": "🚫 *Почему пост не опубликовали?*\n\nПосты публикуются автоматически. Если пост не прошел - возможно, нарушены правила."
    }
    answer = faq_answers.get(faq_type, "Вопрос не найден")
    await callback.message.edit_text(answer, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Возвращаемся в главное меню:", reply_markup=await get_main_menu(callback.from_user.id))

@router.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message):
    await message.answer("Возвращаемся в главное меню:", reply_markup=await get_main_menu(message.from_user.id))