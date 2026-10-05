import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
import uvicorn

# Import your database functions
from database import init_db, add_meal, add_workout, get_daily_summary

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message with command buttons."""
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
    """Prompts the user to enter meal details."""
    await update.message.reply_text(
        "Please enter your meal in the format: `Food Name, Calories, Protein`\n"
        "Example: `Grilled Chicken, 350, 40`",
        parse_mode='Markdown'
    )

async def handle_meal_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses and saves meal data from user input."""
    try:
        text = update.message.text
        parts = [p.strip() for p in text.split(',')]
        if len(parts) != 3:
            raise ValueError("Incorrect format")
        
        food_name = parts[0]
        calories = float(parts[1])
        protein = float(parts[2])
        
        # Save to database (replace with your user ID logic)
        user_id = update.effective_user.id
        add_meal(user_id, food_name, calories, protein)
        
        await update.message.reply_text(
            f"✅ Logged: {food_name} | {calories} kcal | {protein}g protein"
        )
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Please use: `Food Name, Calories, Protein`")

async def log_workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompts the user to enter workout details."""
    await update.message.reply_text(
        "Please enter your workout in the format: `Exercise, Duration (mins), Calories Burned`\n"
        "Example: `Running, 30, 300`"
    )

async def handle_workout_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses and saves workout data from user input."""
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
        await update.message.reply_text("❌ Invalid format. Please use: `Exercise, Duration (mins), Calories Burned`")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a daily summary of calories and protein."""
    user_id = update.effective_user.id
    summary = get_daily_summary(user_id)  # Your database function
    
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

# --- Webhook Server Setup ---

async def healthcheck(request):
    return PlainTextResponse("OK")

# Build the Telegram Application
telegram_app = Application.builder().token(os.environ.get("BOT_TOKEN")).build()

# Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("meal", log_meal_command))
telegram_app.add_handler(CommandHandler("workout", log_workout_command))
telegram_app.add_handler(CommandHandler("summary", summary_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meal_input)) # Simplified for example

# Starlette app to handle webhooks and health checks
async def telegram_webhook(request):
    update = Update.de_json(await request.json(), telegram_app.bot)
    await telegram_app.process_update(update)
    return PlainTextResponse("OK")

app = Starlette(routes=[
    Route("/healthcheck", healthcheck),
    Route("/webhook", telegram_webhook, methods=["POST"])
])

# --- Main Entry Point ---
if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Set webhook (run this once or handle in app startup)
    # Render provides the PORT environment variable
    PORT = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    
    if WEBHOOK_URL:
        # In production on Render, set the webhook
        telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info(f"Webhook set to {WEBHOOK_URL}/webhook")
    
    # Run the web server
    uvicorn.run(app, host="0.0.0.0", port=PORT)
