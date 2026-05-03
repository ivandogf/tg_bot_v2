import asyncio # Импорт библиотеки для работы с асинхронным кодом
import logging # Импорт библиотеки для логирования событий и ошибок
from aiogram import Bot, Dispatcher # Импорт классов для создания бота и диспетчера
from handlers import base_handlers, quiz_handlers, admin_handlers # Импорт модулей общих команд, игровой логики , администрирования с обработчиками
from os import getenv # Импорт функции для получения переменных окружения (списка админов, токена бота)
from dotenv import load_dotenv # Импорт функции для загрузки переменных окружения из файла .env (для безопасности хранения)

load_dotenv() # Загрузка переменных окружения из файла .env
TOKEN = getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO) # Настройка логирования

async def on_startup(bot: Bot):
    """
    Функция, выполняемая автоматически при старте бота для проверки его запуска
    """ 
    print("Бот успешно запущен и готов к работе!")

async def on_shutdown(bot: Bot):
    """
    Функция, выполняемая при корректном завершении работы.
    """ 
    print("Бот завершает работу... Сохраняем данные и отключаемся.")


async def main():
    """
    Основная точка входа в асинхронное приложение.
    Здесь происходит инициализация объектов Bot и Dispatcher,
    регистрация роутеров и запуск опроса серверов Telegram.
    """ 
    bot = Bot(token=TOKEN) # Объект Bot отвечает за отправку запросов к Telegram API
    dp = Dispatcher() # Объект Dispatcher управляет очередью входящих обновлений

    dp.startup.register(on_startup) #безопасный запус
    dp.shutdown.register(on_shutdown) #безопасное завершение

    #Подключение роутеров
    dp.include_router(admin_handlers.router)
    dp.include_router(quiz_handlers.router)
    dp.include_router(base_handlers.router)
 

    await bot.delete_webhook(drop_pending_updates=True) # Пропускаем накопившиеся сообщения, пока бот был оффлайн
    await dp.start_polling(bot) # Запуск бесконечного цикла опроса обновлений

if __name__ == "__main__": # Запуск асинхронного цикла событий
    try:
        asyncio.run(main())
    except KeyboardInterrupt: # Обработка нажатия Ctrl+C в консоли для красивого выхода
        print("Программа прервана пользователем. Бот остановлен.")


#Для запуска программы введите в коноль: python main.py