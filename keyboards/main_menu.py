from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from models.user import UserRole
from database import db

async def get_main_menu(user_id: int):
    user = await db.get_user(user_id)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Отправить анонимку")],
            [KeyboardButton(text="❓ ФАК"), KeyboardButton(text="📋 Правила")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    
    return keyboard

def get_faq_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤔 Что такое анонимка?", callback_data="faq_what_is")],
            [InlineKeyboardButton(text="📝 Как отправить пост?", callback_data="faq_how_to_send")],
            [InlineKeyboardButton(text="⏰ Сколько ждать публикации?", callback_data="faq_time")],
            [InlineKeyboardButton(text="🚫 Почему пост не опубликовали?", callback_data="faq_rejection")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )

def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]
    )

def get_anonymous_post_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши свой анонимный пост..."
    )