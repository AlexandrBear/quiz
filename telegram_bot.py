import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from my_token import API_TOKEN
from db import get_quiz_index, update_quiz_index, quiz_data, get_question, new_quiz, get_result_quiz, update_result_quiz

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Обьект бота
bot = Bot(token=API_TOKEN)

# Диспетчер
dp = Dispatcher()

async def delete_button(callback: types.CallbackQuery):
    # Редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )




@dp.callback_query(F.data != '')
async def user_answer(callback: types.CallbackQuery):
    await delete_button(callback)

    index_callback_data = int(callback.data)

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    # Получение верного варианта ответа на вопрос
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    
    # Отправляем в чат сообщение что ответ
    await callback.message.answer(quiz_data[current_question_index]["options"][index_callback_data])
    if index_callback_data == correct_index:
        current_result = await get_result_quiz(callback.from_user.id)
        current_result += 1
        await update_result_quiz(callback.from_user.id, current_result)
        await callback.message.answer("Верно!")
    else:
        await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_index]}")

    # Обновление номера текущего вопроса
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление о окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершён!")
        # Получим результат ответов
        current_result = await get_result_quiz(callback.from_user.id)
        await callback.message.answer(f"Ваш результат: верных ответов {current_result} из {len(quiz_data)}")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщик клавиатуры типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопку к сообщению
    await message.answer("Добро пожаловать в quiz!!!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Логика начала квиза
    await message.answer(f"Давай начнем квиз!")
    # Запускаем новый квиз
    await new_quiz(message)

# Запуск процесса поллинга новых обьектов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())