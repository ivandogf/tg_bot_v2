from aiogram import Router, F # Импорт класса Router для создания маршрутов и F для фильтрации сообщений
from aiogram.types import Message, CallbackQuery # Импорт классов для работы с сообщениями и коллбек-запросами
from utils.json_manager import get_user, update_user, get_content # Импорт функций для работы с данными пользователей и контентом из JSON
from keyboards.builder import quiz_kb , main_menu_kb # Импорт функций для создания клавиатур

router = Router() 

@router.message(F.text == "🧠 Пройти тест") 
async def start_test(message: Message):
    """
    Запускает процесс тестирования для пользователя.
    Определяет текущий уровень, достает соответствующий вопрос 
    и отправляет его с инлайн-кнопками вариантов ответа.
    """
    user = get_user(message.from_user.id)

    if user.get("is_finished"):
        await message.answer("🎉 Ты прошел все доступные уровни! Жди новых обновлений.")
        return 

    content = get_content()
    level_str = str(user["level"])
    level_data = content["levels"].get(level_str)
    
    if not level_data or not level_data.get("questions"):
        await message.answer("Для твоего уровня пока нет доступных тестов.")
        return

    questions = level_data["questions"]
    q_index = user.get("current_q_index", 0)

    # Если индекс вопроса превышает количество вопросов, сбрасываем его и сохраняем
    if q_index >= len(questions):
        q_index = 0
        user["current_q_index"] = 0
        update_user(message.from_user.id, user)

    # Достаем текущий вопрос для отправки   
    question = questions[q_index]
    
    await message.answer(
        f"❓ <b>Вопрос {q_index + 1} из {len(questions)}:</b>\n\n<b>{question['text']}</b>\n\n<i>Награда: {question['reward']} баллов</i>",
        reply_markup=quiz_kb(question["id"], question["options"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ans_")) # Фильтр для обработки коллбеков, начинающихся с "ans_"
async def handle_answer(callback: CallbackQuery):
    """
    Обрабатывает нажатие на кнопку с вариантом ответа.
    Проверяет правильность, начисляет баллы и переводит на следующий вопрос или уровень.
    """
    data_parts = callback.data.split("_") # Формат данных: ans_{question_id}_{selected_index}
    selected_index = int(data_parts[-1]) # Получаем индекс выбранного ответа (последняя часть данных)
    q_id = "_".join(data_parts[1:-1])  # Получаем ID вопроса (все части между ans и индексом) - это нужно для поиска вопроса в данных

    user = get_user(callback.from_user.id) 
    content = get_content()
    level_str = str(user["level"])
    level_data = content["levels"].get(level_str)
    
    if not level_data:
        await callback.answer("Ошибка уровня", show_alert=True)
        return

    questions = level_data["questions"] # Получаем список вопросов для текущего уровня пользователя
    
    # Ищем вопрос только в текущем уровне
    question = next((q for q in questions if q["id"] == q_id), None)

    if not question:
        await callback.message.edit_text("❌ Ошибка: вопрос не найден.")
        await callback.answer()
        return

    if selected_index == question["correct_index"]:
        # Начисляем баллы 
        reward = question.get("reward", 10)
        user["points"] += reward
        user["current_q_index"] += 1
        
        # Читаем из JSON, сколько баллов нужно для этого уровня
        required_score = level_data.get("required_score", 0)
        
        # Считаем, сколько баллов пользователь уже набрал на этом уровне
        # (кол-во правильных ответов * награду за вопрос)
        current_level_points = user["current_q_index"] * reward

        if current_level_points < required_score:
            update_user(callback.from_user.id, user)
            next_q = questions[user["current_q_index"]]
            
            answer_text = (
                            f"✅ <b>Верно!</b> 🎯 Прогресс: <b>{current_level_points}</b> из <b>{required_score}</b> баллов до следующего уровня \n\n"
                            f"💬 <b>Вопрос №{user['current_q_index'] + 1}:</b>\n"
                            f"<blockquote>{next_q['text']}</blockquote>"
            )
            
            await callback.message.edit_text(
                text=answer_text,
                reply_markup=quiz_kb(next_q["id"], next_q["options"]),
                parse_mode="HTML"
            )
        
        else:
            # Eсли вопросы закончились , то повышение уровня
            next_lvl = user["level"] + 1
            
            if str(next_lvl) in content["levels"]:
                user["level"] = next_lvl
                user["current_q_index"] = 0 # Сбрасываем счетчик для новой темы
                update_user(callback.from_user.id, user)
                
                next_lvl_data = content["levels"][str(next_lvl)]
                await callback.message.edit_text(
                    f"✅ <b>Верно!</b>\n\n"
                    f"🎉 <b>Поздравляю! Уровень {level_str} пройден!</b>\n\n"
                    f"🚀 <b>Твой новый уровень: {next_lvl}.</b>\n"
                    f"Тема: <i>{next_lvl_data['name']}</i>\n\n"
                    f"Смело жми «📖 Изучить теорию», чтобы подготовиться к новым испытаниям!",
                    parse_mode="HTML"
                )
            else:
                user["is_finished"] = True
                update_user(callback.from_user.id, user)
                await callback.message.edit_text(
                    "✅ <b>Идеально!</b>\n\n🎉 <b>Ты прошел ВСЕ доступные уровни C# в игре!</b> Ты настоящий профи. Жди новых обновлений!",
                    parse_mode="HTML"
                )
    else:
        # Ответ неверный
        user["current_q_index"] = 0 # Сброс прогресса текущего теста
        update_user(callback.from_user.id, user)
        
        await callback.message.edit_text(
            f"❌ <b>Ой, ошибка!</b>\n\n"
            f"Тест провален 😔. Твой прогресс на этом уровне сброшен.\n"
            f"Советую нажать «📖 Изучить теорию», чтобы освежить знания, а затем попробовать с самого начала.",
            parse_mode="HTML"
        )

    await callback.answer()


