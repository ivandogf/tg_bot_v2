from aiogram import Router, F #  Импортируем Router для создания маршрутов обработки сообщений и F для фильтрации сообщений по определенным условиям.
from aiogram.types import Message , LinkPreviewOptions # Импортируем класс Message для работы с сообщениями и LinkPreviewOptions для настройки отображения превью ссылок в сообщениях.
from utils.json_manager import get_user, get_content # Импортируем функции для работы с данными пользователей и контентом из JSON файлов.
from keyboards.builder import main_menu_kb # Импортируем функцию для создания основной клавиатуры с кнопками, которая будет использоваться в ответах бота.
import os

router = Router()

@router.message(F.text == "/start") #Обработчик команды start. Регистрирует нового пользователя или обновляет данные существующего, после чего выводит приветственное сообщение и главное меню.
async def cmd_start(message: Message):
    # Инициализируем пользователя и передаем его имя и юзернейм
    get_user(
        user_id=message.from_user.id, 
        first_name=message.from_user.first_name, 
        username=message.from_user.username
    ) 
    

    await message.answer( 
        f"👋 Привет,  {message.from_user.first_name}! Я твой помощник в изучении C#.\n"
        "Выбирай действия в меню ниже, читай теорию, проходи тесты и повышай свой уровень!",
        reply_markup=main_menu_kb()
    )

@router.message(F.text == "ℹ️ Справка")
async def bot_help(message: Message):
    help_text = (
        "ℹ️ <b>Справочная информация</b>\n\n"
        "Бот поможет вам освоить C# — от основ до продвинутых тем.\n\n"
        "<b>Ваши инструменты:</b>\n"
        "• <b>📖 Теория</b> — изучение материалов текущего уровня.\n"
        "• <b>🧠 Тестирование</b> — проверка знаний. За каждый верный ответ вы получаете <b>10 баллов</b>.\n"
        "• <b>📊 Прогресс</b> — ваш текущий статус и общий счет.\n\n"
        "<b>📈 Как перейти на следующий уровень?</b>\n"
        "Для открытия нового уровня сложности необходимо достичь <b>установленного порога баллов</b> в текущем тесте. "
        "Как только ваш счет на уровне сравняется с необходимым, доступ к следующему уровню откроется автоматически.\n\n"
        "🆘 <b>Техническая поддержка:</b>\n"
        "Если бот завис или вы нашли ошибку, пожалуйста, обратитесь к администратору: @ivangelioni\n\n"
        "<i>Секретная команда <code>/admin</code> доступна только администраторам.</i>"
    )
    await message.answer(help_text, parse_mode="HTML")

    
@router.message(F.text == "📖 Изучить теорию") #Обработчик для кнопки "Изучить теорию". Отправляет пользователю учебный материал для текущего уровня.
async def send_theory(message: Message):
    user = get_user(message.from_user.id)

    if user.get("is_finished"):
        await message.answer("🎉 Ты прошел все доступные уровни! Жди новых обновлений.")
        return 
    
    content = get_content()
    level_data = content["levels"].get(str(user["level"])) 
    
    if not level_data:
        await message.answer("Ошибка: данные для твоего уровня не найдены.")
        return

   
    material_source = level_data["material"] # Получаем источник материала из данных уровня.
    
  # Проверяем, является ли это путем к HTML-файлу
    is_path = material_source.endswith('.html') or '/' in material_source
    if is_path:
        if os.path.exists(material_source):
            with open(material_source, 'r', encoding='utf-8') as f:
                theory_text = f.read()
        else:
            # Если файл потерялся, выводим ошибку
            theory_text = "⚠️ <b>Ошибка:</b> <i>Файл с учебным материалом не найден. Обратитесь к администратору.</i>"
    else:
        # Если это не путь, а просто текст, используем его напрямую
        theory_text = material_source

    await message.answer(
        f"📚 <b>Уровень {user['level']}: {level_data['name']}</b>\n\n{theory_text}",
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True) # Отключаем превью для ссылок в теории, чтобы не загромождать сообщение лишними элементами.
    )

@router.message(F.text == "📊 Мой прогресс") # Обработчик для кнопки "Мой прогресс". Показывает пользователю его текущий уровень, количество набранных баллов и прогресс по вопросам в текущем уровне.
async def show_progress(message: Message):
    user = get_user(message.from_user.id)
    content = get_content()
    level_data = content["levels"].get(str(user["level"]))
    
   
    q_index = user.get("current_q_index", 0) # Получаем индекс текущего вопроса, по умолчанию 0, если пользователь еще не проходил тесты.
    total_q = len(level_data["questions"]) if level_data and "questions" in level_data else 0 # Получаем общее количество вопросов в текущем уровне, если данные уровня доступны, иначе 0.
    
    status = "В процессе обучения 📖 " if not user.get("is_finished") else "Курс пройден 🏆"
    
    progress_text = (
        f"👤 <b>Твой профиль:</b>\n\n"
        f"🏆 Уровень: {user['level']}\n"
        f"🎯 Прогресс уровня: {q_index} / {total_q} вопросов\n"
        f"⭐ Всего баллов: {user['points']}\n"
        f"📌 Статус: {status}"
    )
    await message.answer(progress_text, parse_mode="HTML")

@router.message() # Обработчик для всех остальных сообщений, которые не соответствуют предыдущим условиям. Отправляет пользователю сообщение о том, что команда не распознана.
async def unknown_message(message: Message):
    await message.answer(
        "🧐 Похоже, вы ввели неправильную команду для нашего бота.\n\n"
        "Используйте кнопки меню ниже или команду /start, чтобы сориентироваться!",
        reply_markup= main_menu_kb() # Повторно предлагаем меню, чтобы юзер не потерялся
    )