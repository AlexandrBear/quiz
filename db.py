import aiosqlite
import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from quiz_questions import quiz_data

async def create_table():
    # Создаем соединение с базой данных(если ее нет, то база будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Выполним SQL запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY,
                                                                   question_index INTEGER,
                                                                   result_quiz INTEGER)''')
        # Сохраним изменения
        await db.commit()

# Запускаем создание таблицы базы данных
asyncio.run(create_table())


async def update_quiz_index(user_id, index):
    result_quiz = await get_result_quiz(user_id)
    # Создаем соединение с базой данных.
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Вставляем новую запись или заменяем её, если данные уже существуют
        await db.execute('''INSERT OR REPLACE INTO quiz_state (user_id, question_index, result_quiz) VALUES (?, ?, ?)''', (user_id, index, result_quiz))
        # Сохраняем изменения
        await db.commit()


async def get_quiz_index(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возаращаем результат
            result = await cursor.fetchone()
            if result is not None:
                return result[0]
            else:
                return 0 

def generate_options_keyboard(answer_options):
    # Создаём сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()
    index = 0
    # В цикле создаём 4 Inline Callback-кнопки
    for option in answer_options:
        
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            callback_data=str(index)
        ))
        index += 1
    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()

async def get_question(message, user_id):
    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']
    
    # Функция генерации кнопок для текущего вопроса квиза
    # Вкачестве аргументов передаем варианты ответов и значение правильного ответа (не индекс)
    kb = generate_options_keyboard(opts)
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def new_quiz(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    # Сбрасываем результат прохождения квиза в 0
    await update_result_quiz(user_id, 0)
    # Запрашиваем новый вопрос
    await get_question(message, user_id)
    

async def get_result_quiz(user_id):
    # Создаем соединение с базой данных.
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT result_quiz FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат.
            result = await cursor.fetchone()
            if result is not None:
                return result[0]
            else:
                return 0


async def update_result_quiz(user_id, result):
    # Создаем соединение с базой данных.
    question_index = await get_quiz_index(user_id)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Вставляем новую запись или заменяем ее если данные уже существуют
        await db.execute('''INSERT OR REPLACE INTO quiz_state (user_id, question_index, result_quiz) VALUES (?, ?, ?)''', (user_id, question_index, result))
        # Сохраняем изменения
        await db.commit()
