import sqlite3
from datetime import date

DB_NAME = "fitness_tracker.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Table for meals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                food_name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                log_date TEXT NOT NULL
            )
        """)
        # Table for workouts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                calories_burned REAL NOT NULL,
                log_date TEXT NOT NULL
            )
        """)
        conn.commit()

def add_meal(user_id, food_name, calories, protein):
    """Adds a meal record to the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meals (user_id, food_name, calories, protein, log_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, food_name, calories, protein, str(date.today()))
        )
        conn.commit()

def add_workout(user_id, exercise, duration, calories_burned):
    """Adds a workout record to the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO workouts (user_id, exercise, duration_minutes, calories_burned, log_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, exercise, duration, calories_burned, str(date.today()))
        )
        conn.commit()

def get_daily_summary(user_id):
    """Retrieves the daily summary for a user."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Sum of calories and protein from meals
        cursor.execute(
            "SELECT SUM(calories), SUM(protein) FROM meals WHERE user_id = ? AND log_date = ?",
            (user_id, str(date.today()))
        )
        meal_result = cursor.fetchone()
        meal_calories = meal_result[0] or 0
        meal_protein = meal_result[1] or 0
        
        # Sum of calories burned from workouts
        cursor.execute(
            "SELECT SUM(calories_burned) FROM workouts WHERE user_id = ? AND log_date = ?",
            (user_id, str(date.today()))
        )
        workout_result = cursor.fetchone()
        workout_calories = workout_result[0] or 0
        
        return meal_calories, meal_protein, workout_calories
