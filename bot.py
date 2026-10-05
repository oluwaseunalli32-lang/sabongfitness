import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database import init_db, add_meal, add_workout, get_daily_summary

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Log Meal", callback_data='log_meal'),
         InlineKeyboardButton("Log Workout", callback_data='log_workout')],
        [InlineKeyboardButton("Daily Summary", callback_data='summary')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to your Fitness Companion! 💪\n\n"
        "Use the buttons below or commands like /meal, /workout, /summary.",
        reply_markup=reply_markup
    )

async def log_meal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Please enter your meal in the format: `Food Name, Calories, Protein`\n"
        "Example: `Grilled Chicken, 350, 40`",
        parse_mode='Markdown'
    )

async def handle_meal_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        parts = [p.strip() for p in text.split(',')]
        if len(parts) != 3:
            raise ValueError("Incorrect format")
        food_name = parts[0]
        calories = float(parts[1])
        protein = float(parts[2])
        user_id = update.effective_user.id
        add_meal(user_id, food_name, calories, protein)
        await update.message.reply_text(
            f"✅ Logged: {food_name} | {calories} kcal | {protein}g protein"
        )
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid format. Please use: `Food Name, Calories, Protein`"
        )

async def log_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Please enter your workout in the format: `Exercise, Duration (mins), Calories Burned`\n"
        "Example: `Running, 30, 300`"
    )

async def handle_workout_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        parts = [p.strip() for p in text.split(',')]
        if len(parts) != 3:
            raise ValueError("Incorrect format")
        exercise = parts[0]
        duration = int(parts[1])
        calories_burned = float(parts[2])
        user_id = update.effective_user.id
        add_workout(user_id, exercise, duration, calories_burned)
        await update.message.reply_text(
            f"✅ Logged: {exercise} for {duration} mins | {calories_burned} kcal burned"
        )
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid format. Please use: `Exercise, Duration (mins), Calories Burned`"
        )

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    summary = get_daily_summary(user_id)
    if not summary:
        await update.message.reply_text("No data logged for today yet.")
        return
    meal_calories, meal_protein, workout_calories = summary
    await update.message.reply_text(
        f"📊 *Today's Summary*\n\n"
        f"🍽️ Calories Consumed: {meal_calories} kcal\n"
        f"🥩 Protein: {meal_protein} g\n"
        f"🏃 Calories Burned: {workout_calories} kcal\n"
        f"⚖️ Net Calories: {meal_calories - workout_calories} kcal",
        parse_mode='Markdown'
    )

# --- Main Entry Point (Polling Mode) ---

if __name__ == "__main__":
    init_db()
    application = Application.builder().token(os.environ["BOT_TOKEN"]).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("meal", log_meal_command))
    application.add_handler(CommandHandler("workout", log_workout_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meal_input)
    )

    logger.info("Starting bot in polling mode...")
    application.run_polling()
