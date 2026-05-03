# Импорт классов для создания клавиатур с кнопками в Telegram. ReplyKeyboardMarkup - для обычных клавиатур, KeyboardButton - для создания отдельных кнопок.
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton 
# Импорт класса для создания встроенных клавиатур, которые отображаются прямо в сообщении и позволяют пользователю взаимодействовать с ними без отправки текста.
from aiogram.utils.keyboard import InlineKeyboardBuilder 

def main_menu_kb():
    """
    Создает основную клавиатуру с четырьмя кнопками: "Изучить теорию", "Пройти тест", "Мой прогресс" и "Справка". 
    Кнопки расположены в два ряда по две кнопки в каждом.
    """ 
    kb = [
        [KeyboardButton(text="📖 Изучить теорию"), KeyboardButton(text="🧠 Пройти тест")],
        [KeyboardButton(text="📊 Мой прогресс"), KeyboardButton(text="ℹ️ Справка")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True) # Возвращает объект ReplyKeyboardMarkup, который можно использовать для отправки клавиатуры пользователю. 

def admin_menu_kb():
    """
    Создает панель управления для администратора. Доступна только пользователям, чей ID указан в .env
    """ 
    kb = [
        [KeyboardButton(text="➕ Добавить вопрос"), KeyboardButton(text="✏️ Изменить вопрос")],
        [KeyboardButton(text="🗑 Удалить вопрос"), KeyboardButton(text="🔙 Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def quiz_kb(question_id, options):
    """
    Создает встроенную клавиатуру для теста с вариантами ответов. 
    Каждая кнопка соответствует одному из вариантов ответа и содержит callback_data, которая позволяет идентифицировать, какой вариант был выбран пользователем.
    """ 
    builder = InlineKeyboardBuilder()
    for index, option in enumerate(options):
        builder.button(text=option, callback_data=f"ans_{question_id}_{index}")
    builder.adjust(1) # Устанавливает количество кнопок в одном ряду.
    return builder.as_markup()