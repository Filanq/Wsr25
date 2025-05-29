from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

# === Состояния для ConversationHandler ===
BRANCH, SERVICE, DATE, TIME, REMINDER = range(5)
RATE_OPERATOR, RATE_BRANCH, RATE_COMMENT = range(3)

# === Моковые данные ===
MOCK_SERVICES = {
    1: [
        {"id": 1, "name": "Получение справки"},
        {"id": 2, "name": "Регистрация документов"},
    ],
    2: [
        {"id": 3, "name": "Консультация"},
        {"id": 4, "name": "Подача заявления"},
    ],
}


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    keyboard = [
        [InlineKeyboardButton("📝 Записаться", callback_data="record")],
        [InlineKeyboardButton("❌ Отменить запись", callback_data="cancel_appointment")],
        [InlineKeyboardButton("⭐ Оценить работу", callback_data="rate_service")],
    ]
    await update.message.reply_text(
        "Здравствуйте! Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# === Вспомогательные функции ===
def combine_date_and_time(date_choice, time_str):
    today = datetime.now().date()
    if date_choice == "Сегодня":
        day = today
    elif date_choice == "Завтра":
        day = today + timedelta(days=1)
    elif date_choice == "Послезавтра":
        day = today + timedelta(days=2)
    else:
        day = today

    hour, minute = map(int, time_str.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute)


def schedule_reminder(context: ContextTypes.DEFAULT_TYPE, minutes_before):
    print(f"[Напоминание] Запланировано за {minutes_before} минут")


async def create_appointment_mock(context: ContextTypes.DEFAULT_TYPE, date_time, reminder_minutes):
    data = context.user_data
    full_datetime = combine_date_and_time(data["date"], data["time"])
    print(f"[Мок] Запись создана: {data['branch_name']}, {data['service_name']}, {full_datetime}")
    return True


# === Обработчики шагов ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)


async def record_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["data"] = {}

    keyboard = [
        [InlineKeyboardButton("Центральный офис", callback_data="branch_1")],
        [InlineKeyboardButton("Северный филиал", callback_data="branch_2")],
    ]
    await query.edit_message_text("Выберите отделение:", reply_markup=InlineKeyboardMarkup(keyboard))
    return BRANCH


async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    branch_id = int(query.data.split("_")[1])
    context.user_data["branch_id"] = branch_id
    context.user_data["branch_name"] = "Центральный офис" if branch_id == 1 else "Северный филиал"

    services = MOCK_SERVICES.get(branch_id, [])
    keyboard = [[InlineKeyboardButton(s["name"], callback_data=f"service_{s['id']}")] for s in services]

    await query.edit_message_text("Выберите услугу:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SERVICE


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split("_")[1])
    context.user_data["service_id"] = service_id
    context.user_data["service_name"] = next(
        s["name"] for b in MOCK_SERVICES.values() for s in b if s["id"] == service_id
    )

    dates = ["Сегодня", "Завтра", "Послезавтра"]
    keyboard = [[InlineKeyboardButton(d, callback_data=f"date_{i}")] for i, d in enumerate(dates)]

    await query.edit_message_text("Выберите дату:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DATE


async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    date_index = int(query.data.split("_")[1])
    today = datetime.now().date()
    selected_date = today + timedelta(days=date_index)
    context.user_data["date"] = ["Сегодня", "Завтра", "Послезавтра"][date_index]

    times = ["10:00", "11:00", "12:00", "13:00", "14:00"]
    keyboard = [[InlineKeyboardButton(t, callback_data=f"time_{t}")] for t in times]

    await query.edit_message_text("Выберите время:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIME


async def choose_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time = query.data.split("_")[1]
    context.user_data["time"] = time

    reminders = ["15", "30", "60"]
    keyboard = [[InlineKeyboardButton(f"{r} мин", callback_data=f"remind_{r}")] for r in reminders]

    await query.edit_message_text("Выберите напоминание:", reply_markup=InlineKeyboardMarkup(keyboard))
    return REMINDER


async def confirm_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    remind = query.data.split("_")[1]
    data = context.user_data

    full_datetime = combine_date_and_time(data["date"], data["time"])

    confirmation = f"""
    ✅ Ваша запись подтверждена:
    🏢 Отделение: {data["branch_name"]}
    📋 Услуга: {data["service_name"]}
    📅 Дата и время: {full_datetime.strftime("%d.%m.%Y %H:%M")}
    ⏰ Напоминание за {remind} минут
    """
    await query.edit_message_text(confirmation)

    # Мок создания записи
    success = await create_appointment_mock(context, full_datetime, remind)
    if success:
        schedule_reminder(context, remind)

    # Показываем главное меню
    await show_main_menu(query, context)

    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Запись отменена.")

    # Показываем главное меню
    await show_main_menu(query, context)

    return ConversationHandler.END


async def rate_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="rating_operator_1")],
        [InlineKeyboardButton("⭐⭐", callback_data="rating_operator_2")],
        [InlineKeyboardButton("⭐⭐⭐", callback_data="rating_operator_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_operator_4")],
        [InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_operator_5")]
    ]
    await query.edit_message_text("Оцените работу оператора:", reply_markup=InlineKeyboardMarkup(keyboard))
    return RATE_OPERATOR


async def rate_operator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[2])
    context.user_data["rating_operator"] = rating

    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="rating_branch_1")],
        [InlineKeyboardButton("⭐⭐", callback_data="rating_branch_2")],
        [InlineKeyboardButton("⭐⭐⭐", callback_data="rating_branch_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_branch_4")],
        [InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_branch_5")]
    ]
    await query.edit_message_text("Оцените работу отделения:", reply_markup=InlineKeyboardMarkup(keyboard))
    return RATE_BRANCH


async def rate_branch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[2])
    context.user_data["rating_branch"] = rating

    await query.edit_message_text("Напишите свои пожелания или предложения:")
    return RATE_COMMENT


async def rate_comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["rating_comment"] = text

    # Мок сохранения
    print("[Мок] Получена оценка:", context.user_data)

    await update.message.reply_text("Спасибо за вашу оценку!")
    await show_main_menu(update, context)
    return ConversationHandler.END


async def rate_comment_skipped(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rating_comment"] = "(нет комментариев)"

    print("[Мок] Получена оценка без комментария:", context.user_data)

    await show_main_menu(update, context)
    return ConversationHandler.END


# === Обработчик отмены оценки ===
async def cancel_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Вы отменили оценку.")
    await show_main_menu(query, context)
    return ConversationHandler.END


# === Конфигурация ConversationHandler для оценки ===
rate_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(rate_service_start, pattern="rate_service")],
    states={
        RATE_OPERATOR: [CallbackQueryHandler(rate_operator_handler, pattern=r"rating_operator_\d+")],
        RATE_BRANCH: [CallbackQueryHandler(rate_branch_handler, pattern=r"rating_branch_\d+")],
        RATE_COMMENT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, rate_comment_handler),
            CallbackQueryHandler(rate_comment_skipped, pattern="skip_comment"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_rating, pattern="cancel_rating")
    ],
    allow_reentry=True,
)


async def rate_branch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[2])
    context.user_data["rating_branch"] = rating

    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data="skip_comment")]
    ]
    await query.edit_message_text("Напишите свои пожелания или предложения:",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return RATE_COMMENT


async def rate_comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["rating_comment"] = text

    operator_rating = context.user_data.get("rating_operator", 0)
    branch_rating = context.user_data.get("rating_branch", 0)

    message = f"""
✅ Спасибо за оценку!

🧑‍💻 Оценка оператора: {operator_rating} ⭐  
🏢 Оценка отделения: {branch_rating} ⭐  
📝 Пожелания: {text}
"""

    await update.message.reply_text(message)
    await show_main_menu(update, context)
    return ConversationHandler.END


async def cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Ваша запись успешно отменена.")

    # Показываем главное меню
    await show_main_menu(query, context)


# === MAIN ===
def main():
    bot_token = "7736919732:AAE_ElTz0O85JMA-k7ByKVYuseeySAUbDeg"
    if not bot_token:
        raise ValueError("Не указан BOT_TOKEN в .env")

    application = Application.builder().token(bot_token).build()

    # Wizard сцена
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(record_start, pattern="record")],
        states={
            BRANCH: [CallbackQueryHandler(choose_service)],
            SERVICE: [CallbackQueryHandler(choose_date)],
            DATE: [CallbackQueryHandler(choose_time)],
            TIME: [CallbackQueryHandler(choose_reminder)],
            REMINDER: [CallbackQueryHandler(confirm_appointment, pattern=r"remind_\d+")],
        },
        fallbacks=[CallbackQueryHandler(cancel_conversation, pattern="cancel_conversation")],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(rate_conv_handler)
    application.add_handler(CallbackQueryHandler(cancel_appointment, pattern="cancel_appointment"))
    application.add_handler(CallbackQueryHandler(lambda u, c: None, pattern="rate_service"))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
