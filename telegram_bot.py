import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Отчёт за день", callback_data='report_day')],
        [InlineKeyboardButton("Отчёт за неделю", callback_data='report_week')],
        [InlineKeyboardButton("Ввести номер авто", callback_data='enter_number')]
    ]
    await update.message.reply_text("Выберите опцию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "enter_number":
        user_state[query.from_user.id] = "awaiting_car_number"
        await query.edit_message_text("Введите гос. номер авто:")
    else:
        await query.edit_message_text(f"Функция {query.data} пока не реализована.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_state.get(user_id) == "awaiting_car_number":
        car_number = update.message.text.upper()
        user_state[user_id] = None
        await update.message.reply_text(f"Гос. номер принят: {car_number}\nОтправка в Bitrix24...")

        # Отправка в Bitrix24
        payload = {
            'FIELDS': {
                'OWNER_TYPE_ID': 2,
                'OWNER_ID': 1,
                'TYPE_ID': 1,
                'SUBJECT': 'Информация из Yandex Fleet',
                'DESCRIPTION': f'{car_number}\nБаланс: 120₾\nНа линии: Да',
                'DESCRIPTION_TYPE': 1,
                'COMPLETED': 'Y',
                'RESPONSIBLE_ID': 1
            }
        }

        response = requests.post(BITRIX_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            await update.message.reply_text("✅ Успешно отправлено в Bitrix24!")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")
    else:
        await update.message.reply_text("Напишите /start и выберите опцию.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен!")
    app.run_polling()
