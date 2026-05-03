import json
import os

USERS_FILE = 'data/users.json' # Файл для хранения прогресса пользователей
CONTENT_FILE = 'data/content.json' # Файл для хранения контента с уровнями и вопросами

def load_json(filepath): 
    """
    Функция для чтения данных из JSON-файла.
    Если файл не найден, возвращает пустой словарь.
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f: 
        return json.load(f) 

def save_json(filepath, data):
    """
    Функция для записи данных в JSON-файл.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user(user_id, first_name=None, username=None): 
    """
    Функция для получения данных пользователя по его ID.
    Если пользователь не найден, создает новую запись с базовыми данными.
    """
    users = load_json(USERS_FILE) 
    str_id = str(user_id) 
    
    # Если пользователя еще нет в базе
    if str_id not in users:
        users[str_id] = {
            "first_name": first_name or "Неизвестно", 
            "username": username or "",
            "level": 1,  # Текущий уровень пользователя
            "points": 0, # Накопленные очки пользователя
            "current_q_index": 0,  # Индекс текущего вопроса
            "is_finished": False # Флаг, указывающий, завершил ли пользователь все уровни
        }
        save_json(USERS_FILE, users) 
    else:
        # Если пользователь уже существует, проверяем и обновляем его имя и username
        updated = False
        if first_name and users[str_id].get("first_name") != first_name: 
            users[str_id]["first_name"] = first_name
            updated = True
        if username and users[str_id].get("username") != username:
            users[str_id]["username"] = username
            updated = True
            
        if updated:
            save_json(USERS_FILE, users) 

    return users[str_id]

def update_user(user_id, data):
    """
    Обновляет данные пользователя, перезаписывая его запись в JSON файле.
    """
    users = load_json(USERS_FILE) 
    users[str(user_id)] = data 
    save_json(USERS_FILE, users)

def get_content():
    """
    Загружает контент с уровнями и вопросами из JSON файла.
    """
    return load_json(CONTENT_FILE)

def save_content(data):
    """
    Сохраняет обновленный контент (используется администратором для редактирования базы вопросов).
    """
    save_json(CONTENT_FILE, data)