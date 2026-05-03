import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext # Импорт для работы с машиной состояний
from aiogram.fsm.state import State, StatesGroup # Импорт для определения состояний в машине состояний
from utils.json_manager import get_content, save_content # Импорт функций для работы с данными из JSON
from keyboards.builder import admin_menu_kb, main_menu_kb # Импорт функций для создания клавиатур
from dotenv import load_dotenv

load_dotenv()
router = Router()


raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id) for admin_id in raw_admins.split(",") if admin_id.strip()]

print(f"DEBUG: Список админов загружен: {ADMIN_IDS}") # Выводим список админов при загрузке, чтобы убедиться, что они правильно считались из .env

#  Машина состояний для админки
class AdminStates(StatesGroup): # Состояния для добавления вопроса
    add_lvl = State() # Выбор уровня
    add_text = State() # Ввод текста вопроса
    add_options = State() # Ввод вариантов ответов
    add_correct = State() # Выбор индекса правильного ответа
    
    # Состояния для удаления
    del_lvl = State() 
    del_id = State()
    
    # Состояния для редактирования
    edit_lvl = State()
    edit_id = State()
    edit_text = State()


@router.message(F.text == "/admin", F.from_user.id.in_(ADMIN_IDS)) # Фильтр для команды admin, доступной только для админов
async def cmd_admin(message: Message):
    await message.answer("🛠 <b>Панель администратора активирована.</b>\nВыберите действие:", 
                         reply_markup=admin_menu_kb(), parse_mode="HTML")

@router.message(F.text == "🔙 Выход", F.from_user.id.in_(ADMIN_IDS)) # Выход из админского режима и очистка состояния
async def exit_admin(message: Message, state: FSMContext): 
    await state.clear()
    await message.answer("Вы вышли из режима администратора.", reply_markup=main_menu_kb())


@router.message(F.text == "➕ Добавить вопрос", F.from_user.id.in_(ADMIN_IDS)) # Начало процесса добавления вопроса, переход к первому состоянию
async def add_start(message: Message, state: FSMContext):
    await message.answer("Введите номер уровня (образец: 1). Всего существует 8 уровней")
    await state.set_state(AdminStates.add_lvl)

# Фильтр F.text гарантирует, что бот не упадет, если админ пришлет фото или стикер
@router.message(AdminStates.add_lvl, F.text, F.from_user.id.in_(ADMIN_IDS)) # Обработка ввода уровня, проверка его существования и переход к следующему состоянию
async def add_level(message: Message, state: FSMContext): 
    lvl = message.text.strip() 
    content = get_content()
    
    # Сразу проверяем, существует ли уровень, чтобы не гонять админа по всем шагам зря
    if lvl not in content.get("levels", {}):
        await message.answer(f"⚠️ Уровень '{lvl}' не существует. Введите существующий уровень или нажмите '🔙 Выход':",reply_markup=admin_menu_kb())
        return # Прерываем функцию, ждем правильный ввод
        
    await state.update_data(level=lvl)
    await message.answer("Отлично. Введите текст вопроса:")
    await state.set_state(AdminStates.add_text)

@router.message(AdminStates.add_text, F.text, F.from_user.id.in_(ADMIN_IDS)) # Сохранение текста вопроса и переход к следующему состоянию для ввода вариантов ответов
async def add_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Введите варианты ответов через запятую (минимум 2 варианта):")
    await state.set_state(AdminStates.add_options)

@router.message(AdminStates.add_options, F.text, F.from_user.id.in_(ADMIN_IDS)) # Обработка ввода вариантов ответов, проверка их количества и переход к следующему состоянию для выбора правильного ответа
async def add_options(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split(",") if opt.strip()]
    
    #Проверяем количество вариантов
    if len(options) < 2:
        await message.answer("⚠️ Необходимо ввести как минимум 2 варианта ответа. Попробуйте еще раз:")
        return
        
    await state.update_data(options=options)
    await message.answer(f"Варианты: {options}\nВведите индекс правильного ответа (от 0 до {len(options)-1}):")
    await state.set_state(AdminStates.add_correct)

@router.message(AdminStates.add_correct, F.text, F.from_user.id.in_(ADMIN_IDS)) # Обработка ввода индекса правильного ответа
async def add_correct(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Пожалуйста, введите только число (индекс).")
        return
        
    correct_index = int(message.text.strip())
    data = await state.get_data()
    options = data['options']
    
    if correct_index < 0 or correct_index >= len(options):
        await message.answer(f"⚠️ Индекс должен быть от 0 до {len(options)-1}. Попробуйте еще раз:")
        return

    content = get_content()
    lvl = data['level']
    
    
    questions = content["levels"][lvl]["questions"]
    if not questions:
        new_id = f"q{lvl}_1"
    else:
        try:
            max_num = max([int(q["id"].split("_")[1]) for q in questions if "_" in q["id"]])
            new_id = f"q{lvl}_{max_num + 1}"
        except (IndexError, ValueError):
            new_id = f"q{lvl}_err_{len(questions) + 1}"
    
    #
    reward_per_question = 10 # Фиксированная награда
    new_q = {
        "id": new_id,
        "text": data['text'],
        "options": options,
        "correct_index": correct_index,
        "reward": reward_per_question
    }
    
    #Добавляем вопрос в список
    content["levels"][lvl]["questions"].append(new_q)

    
    #Автоматически пересчитываем required_score для уровня
    #  порог баллов равен количеству вопросов * 10
    new_total_questions = len(content["levels"][lvl]["questions"])
    content["levels"][lvl]["required_score"] = new_total_questions * reward_per_question
    
    
    save_content(content)
    
    await message.answer(
        f"✅ Вопрос добавлен! ID: <b>{new_id}</b>\n"
        f"📈 Порог баллов для уровня {lvl} обновлен: <b>{content['levels'][lvl]['required_score']}</b>", 
        parse_mode="HTML", 
        reply_markup=admin_menu_kb()
    )
    await state.clear()


@router.message(F.text == "🗑 Удалить вопрос", F.from_user.id.in_(ADMIN_IDS))
async def del_start(message: Message, state: FSMContext):
    await message.answer("Введите номер уровня:")
    await state.set_state(AdminStates.del_lvl)

@router.message(AdminStates.del_lvl, F.text, F.from_user.id.in_(ADMIN_IDS))
async def del_level(message: Message, state: FSMContext):
    lvl = message.text.strip()
    content = get_content()
    
    if lvl not in content.get("levels", {}):
        await message.answer("⚠️ Такого уровня нет. Введите правильный номер:")
        return
        
    await state.update_data(level=lvl)
    await message.answer("Введите ID вопроса для удаления (образец: q1_2). Первая цифра это номер уровня , а вторая цифра номер вопроса в этом уровне.")
    await state.set_state(AdminStates.del_id)

@router.message(AdminStates.del_id, F.text, F.from_user.id.in_(ADMIN_IDS))
async def process_del_id(message: Message, state: FSMContext):
    data = await state.get_data()
    lvl = data['level']
    q_id = message.text.strip()
    
    content = get_content()
    questions = content["levels"][lvl]["questions"]
    
    #Безопасное удаление с проверкой
    filtered_q = [q for q in questions if q["id"] != q_id]
    
    if len(questions) != len(filtered_q):
        content["levels"][lvl]["questions"] = filtered_q
        # Пересчитываем порог баллов после удаления
        content["levels"][lvl]["required_score"] = len(filtered_q) * 10
        save_content(content)
        await message.answer(f"✅ Вопрос <b>{q_id}</b> удален.", parse_mode="HTML",reply_markup=admin_menu_kb())
    else:
        await message.answer(f"❌ Вопрос с ID <b>{q_id}</b> не найден в этом уровне. Операция отменена.", parse_mode="HTML",reply_markup=admin_menu_kb())
        
    await state.clear()


@router.message(F.text == "✏️ Изменить вопрос", F.from_user.id.in_(ADMIN_IDS))
async def edit_start(message: Message, state: FSMContext):
    await message.answer("Введите номер уровня:")
    await state.set_state(AdminStates.edit_lvl)

@router.message(AdminStates.edit_lvl, F.text, F.from_user.id.in_(ADMIN_IDS))
async def edit_level(message: Message, state: FSMContext):
    lvl = message.text.strip()
    content = get_content()
    
    if lvl not in content.get("levels", {}):
        await message.answer("⚠️ Такого уровня нет. Введите правильный номер:")
        return
        
    await state.update_data(level=lvl)
    await message.answer("Введите ID вопроса (образец: q1_1). Первая цифра это номер уровня , а вторая цифра номер вопроса в этом уровне. ")
    await state.set_state(AdminStates.edit_id)

@router.message(AdminStates.edit_id, F.text, F.from_user.id.in_(ADMIN_IDS))
async def process_edit_id(message: Message, state: FSMContext):
    data = await state.get_data()
    lvl = data['level']
    q_id = message.text.strip()
    
    content = get_content()
    #Проверяем существование вопроса до того, как просить новый текст
    question_exists = any(q["id"] == q_id for q in content["levels"][lvl]["questions"])
    
    if not question_exists:
        await message.answer("❌ Вопрос с таким ID не найден. Введите верный ID:")
        return
        
    await state.update_data(q_id=q_id)
    await message.answer("Введите новый текст для этого вопроса:")
    await state.set_state(AdminStates.edit_text)

@router.message(AdminStates.edit_text, F.text, F.from_user.id.in_(ADMIN_IDS))
async def process_edit_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lvl = data['level']
    q_id = data['q_id']
    new_text = message.text
    
    content = get_content()
    for q in content["levels"][lvl]["questions"]:
        if q["id"] == q_id:
            q["text"] = new_text
            break
            
    save_content(content)
    await message.answer("✅ Текст вопроса успешно изменен.",reply_markup=admin_menu_kb())
    await state.clear()