from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


main = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Web App"), 
            KeyboardButton(text="Инфа")
        ],
        [KeyboardButton(text="Найти трек/альбом")],
        [KeyboardButton(text="Подключить аккаунт Spotify")],
    ],
    resize_keyboard=True,
)
