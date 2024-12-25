import csv
import os
import io
import telebot
import sqlite3
from datetime import datetime
import pendulum

# Initialize the bot with your token from BotFather
API_TOKEN = os.environ["API_TOKEN"]
bot = telebot.TeleBot(API_TOKEN)

# Database setup
conn = sqlite3.connect("shared/expenses.db", check_same_thread=False)
cursor = conn.cursor()

# Create the expenses table if it does not exist
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    category TEXT,
    amount REAL,
    datetime DATETIME
)
"""
)
conn.commit()

menu_buttons = [
    telebot.types.InlineKeyboardButton(text="/log"),
    telebot.types.InlineKeyboardButton(text="/stats"),
]

# Expense categories
categories = [
    "Grocery",
    "Car",
    "Transportation",
    "House",
    "Eating out",
    "Health",
    "Utilities",
    "Other",
]
category_buttons = [
    telebot.types.InlineKeyboardButton(text=cat, callback_data=cat)
    for cat in categories
]

stats_periods = ["Today", "This week", "This month"]
stats_periods_buttons = [
    telebot.types.InlineKeyboardButton(text=period, callback_data=period)
    for period in stats_periods
]


def get_today_range():
    today = pendulum.now()
    start = today.start_of("day")
    end = today.end_of("day")

    return (start, end)


def get_this_week_range():
    today = pendulum.now()
    start = today.start_of("week")
    end = today.end_of("week")

    return (start, end)


def get_this_month_range():
    today = pendulum.now()
    start = today.start_of("month")
    end = today.end_of("month")

    return (start, end)


stats_periods_fns = {
    "Today": get_today_range,
    "This week": get_this_week_range,
    "This month": get_this_month_range,
}

# Global variable to store user-selected category
user_selected_categories = {}


# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add(*menu_buttons)

    bot.reply_to(
        message,
        "Welcome to the Family Expense Logger Bot! Use /log to log an expense or /stats to view statistics.",
        reply_markup=markup,
    )


# Expense logging command
@bot.message_handler(commands=["log"])
def select_category(message):
    # Display category buttons for user to choose
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(*category_buttons)
    bot.send_message(message.chat.id, "Select a category:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in categories)
def enter_expense_amount(call):
    # Save the user's choice of category
    user_selected_categories[call.from_user.id] = call.data
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text="Enter the amount of the expense:",
    )


@bot.message_handler(
    func=lambda message: message.from_user.id in user_selected_categories
)
def save_expense(message):
    try:
        # Parse the entered amount
        amount = float(message.text)

        # Retrieve user data
        category = user_selected_categories.pop(message.from_user.id)
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save expense to database
        cursor.execute(
            """
        INSERT INTO expenses (user_id, username, category, amount, datetime)
        VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, username, category, amount, datetime_now),
        )
        conn.commit()

        bot.reply_to(message, f"Expense logged! {category}: {amount}")
    except ValueError:
        bot.reply_to(message, "Invalid amount. Please enter a number.")


@bot.message_handler(commands=["stats"])
def show_stats_reply(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(*stats_periods_buttons)
    bot.send_message(message.chat.id, "Select a period:", reply_markup=markup)


# Statistics command
@bot.callback_query_handler(func=lambda call: call.data in stats_periods)
def show_statistics(call):
    stats_period = call.data

    (start, end) = stats_periods_fns[stats_period]()

    user_id = call.from_user.id
    cursor.execute(
        """
    SELECT category, SUM(amount), COUNT(*)
    FROM expenses
    WHERE user_id = ? and datetime BETWEEN ? AND ?
    GROUP BY category
    """,
        (
            user_id,
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    rows = cursor.fetchall()

    if rows:
        stats_message = f"Your expense statistics for {stats_period.lower()}:\n"
        for row in rows:
            category, total_amount, count = row
            stats_message += f"{category}: {total_amount:.2f} (Entries: {count})\n"
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.id, text=stats_message
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="No expenses logged yet.",
        )


@bot.message_handler(commands=["export"])
def export_expenses(message):
    user_id = message.from_user.id

    try:
        # Fetch the user's expenses from the database
        cursor.execute(
            """
        SELECT id, user_id, username, category, amount, datetime
        FROM expenses
        """,
        )
        rows = cursor.fetchall()

        if not rows:
            # If no data is found for the user, inform them
            bot.reply_to(message, "No expenses found to export.")
            return

        # Create an in-memory file
        output = io.StringIO()

        # Write CSV data to the in-memory file
        writer = csv.writer(output)
        writer.writerow(
            ["ID", "User ID", "Username", "Category", "Amount", "Datetime"]
        )  # Header
        writer.writerows(rows)  # Rows of data

        # Move the cursor of the in-memory file to the start
        output.seek(0)

        # Send the file to the user as a document
        bot.send_document(
            chat_id=message.chat.id,
            document=io.BytesIO(
                output.getvalue().encode("utf-8")
            ),  # Convert to binary for Telegram
            visible_file_name=f'expenses_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.csv',
            caption="Here is your expense data in CSV format!",
        )

        # Close the in-memory file
        output.close()

    except Exception as e:
        # Handle any errors that occur during the process
        bot.reply_to(message, f"An error occurred during export: {str(e)}")


# Run the bot
bot.polling()
