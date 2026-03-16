import os
import json
import random
import logging
import re
from datetime import datetime, date
import math

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────────
#  CONFIG – Your personal details
#  ⚠️ IMPORTANT: Replace with your NEW token from BotFather!
# ─────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
# Telegram user IDs
ALLOWED_USERS = [6944104031, 5726835273]  # 6944104031 = Lu (gf), 5726835273 = Abi (you)

# Display names with your actual names
USER_NAMES = {
    6944104031: "🌸 My Lu",      # Your girlfriend
    5726835273: "💙 Your Abi",    # You
}

# Birthdays (month, day)
LU_BIRTHDAY = (4, 17)    # Lu's birthday: April 17, 2001
ABI_BIRTHDAY = (8, 21)   # Abi's birthday: August 21, 2001

# Relationship milestones (month, day, year, description)
MILESTONES = [
    (10, 15, 2023, "The day we first met ✨"),  # Replace with your actual date
    (11, 1, 2023, "When we became official 💑"),  # Replace with your actual date
    (12, 25, 2023, "Our first Christmas together 🎄"),
    (2, 14, 2024, "First Valentine's Day 💕"),
]

# Relationship start date for anniversary calculation
RELATIONSHIP_START = date(2023, 10, 15)  # Replace with your actual date

# Directories
PHOTO_DIR = "photos"
CAPTION_DIR = "captions"
NOTES_FILE = "love_notes.json"

# ─────────────────────────────────────────────

# Helper function to escape MarkdownV2 special characters
def escape_markdown(text):
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    return escaped_text

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(CAPTION_DIR, exist_ok=True)

# Conversation states
WAITING_FOR_NOTE = 1

# ── Love quotes (personalized) ─────────────────────────────────────────────
LOVE_QUOTES = [
    "Lu, you're the April to my August, the perfect balance in my life. 🌸💙",
    "Every love story is beautiful, but ours is my favourite. Especially with you, Lu. 🌹",
    "From April 17 to August 21, we complete each other's calendar. 📅💕",
    "In all the world, there is no heart for me like yours, my Lu. 💞",
    "I love you not only for what you are, but for what I am when I'm with you. ✨",
    "You are my today and all of my tomorrows, Lu. 🌅",
    "If I know what love is, it is because of you, my beautiful girlfriend. 💛",
    "Lu, you make my heart smile every single day. 😊",
    "I fell in love with you because of a million tiny things you never knew you were doing. 🌸",
    "Distance means so little when someone means as much as you do to me, Lu. 💌",
    "You are the best thing that ever happened to me, Lu. 🎉",
    "My favourite place in the world is right next to you. 🏡",
    "Every day I love you more than the day before. 📅",
    "With you, Lu, every moment is a memory worth keeping. 📸",
    "You're the reason I believe in love at first sight. 💘",
    "Lu + Abi = Forever ❤️",
]

# ── Sweet nicknames for different moods ────────────────────────────────────
NICKNAMES = {
    "morning": ["Sunshine", "Sleepyhead", "Morning Star", "Beautiful"],
    "afternoon": ["Sweetheart", "Darling", "Love", "Gorgeous"],
    "evening": ["Moonbeam", "Starlight", "Dream Girl", "Princess"],
    "night": ["Angel", "Sweet Dreams", "Baby", "My Everything"],
}

# ── Special responses for important dates ──────────────────────────────────
SPECIAL_DATE_MESSAGES = {
    "new_year": "🎉 Happy New Year, my love! Another year of us begins! ✨",
    "valentine": "💕 Happy Valentine's Day, Lu! Every day with you feels like Valentine's! 🌹",
    "christmas": "🎄 Merry Christmas, my love! You're the best gift I've ever received! 🎁",
    "lu_birthday": "🎂🎉 HAPPY BIRTHDAY MY LU! April 17th is the day the world became more beautiful! 🌸💖",
    "abi_birthday": "🎂🎉 It's my birthday, but you're the best gift I could ever ask for, Lu! 💙",
}

# ────────────────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

def get_name(user_id: int) -> str:
    return USER_NAMES.get(user_id, "Someone special")

def get_nickname_for_time() -> str:
    """Return a nickname based on time of day"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        mood = "morning"
    elif 12 <= hour < 17:
        mood = "afternoon"
    elif 17 <= hour < 22:
        mood = "evening"
    else:
        mood = "night"
    return random.choice(NICKNAMES[mood])

def days_until_birthday(birthday: tuple) -> int:
    """Calculate days until a specific birthday"""
    today = date.today()
    bday = date(today.year, birthday[0], birthday[1])
    if bday < today:
        bday = date(today.year + 1, birthday[0], birthday[1])
    return (bday - today).days

def is_birthday_today(birthday: tuple) -> bool:
    """Check if today is a specific birthday"""
    today = date.today()
    return today.month == birthday[0] and today.day == birthday[1]

def get_relationship_duration() -> dict:
    """Calculate relationship duration in years, months, days"""
    today = date.today()
    delta = today - RELATIONSHIP_START
    
    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = (delta.days % 365) % 30
    
    return {
        "years": years,
        "months": months,
        "days": days,
        "total_days": delta.days
    }

def get_next_anniversary() -> int:
    """Get days until next anniversary"""
    today = date.today()
    anniversary = date(today.year, RELATIONSHIP_START.month, RELATIONSHIP_START.day)
    if anniversary < today:
        anniversary = date(today.year + 1, RELATIONSHIP_START.month, RELATIONSHIP_START.day)
    return (anniversary - today).days

def check_special_date() -> str | None:
    """Check if today is a special date and return appropriate message"""
    today = date.today()
    
    # Check birthdays
    if today.month == 4 and today.day == 17:
        return SPECIAL_DATE_MESSAGES["lu_birthday"]
    elif today.month == 8 and today.day == 21:
        return SPECIAL_DATE_MESSAGES["abi_birthday"]
    
    # Check holidays
    if today.month == 12 and today.day == 25:
        return SPECIAL_DATE_MESSAGES["christmas"]
    elif today.month == 2 and today.day == 14:
        return SPECIAL_DATE_MESSAGES["valentine"]
    elif today.month == 1 and today.day == 1:
        return SPECIAL_DATE_MESSAGES["new_year"]
    
    # Check milestones
    for month, day, year, desc in MILESTONES:
        if today.month == month and today.day == day:
            years_ago = today.year - year
            return f"🎉 {years_ago} year{'s' if years_ago != 1 else ''} ago today: {desc}"
    
    return None

def get_photo_list() -> list[str]:
    """Return sorted list of photo filenames."""
    photos = [
        f for f in os.listdir(PHOTO_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    photos.sort(key=lambda f: os.path.getmtime(os.path.join(PHOTO_DIR, f)), reverse=True)
    return photos

def get_caption(file_id_stem: str) -> str:
    caption_file = os.path.join(CAPTION_DIR, f"{file_id_stem}.txt")
    if os.path.exists(caption_file):
        with open(caption_file, "r", encoding="utf-8") as cf:
            return cf.read().strip()
    return ""

def get_sender(file_id_stem: str) -> str:
    """Get who sent a photo."""
    sender_file = os.path.join(CAPTION_DIR, f"{file_id_stem}_sender.txt")
    if os.path.exists(sender_file):
        with open(sender_file, "r", encoding="utf-8") as sf:
            return sf.read().strip()
    return ""

# ── Love notes persistence ──────────────────────────────────────────────────

def load_notes() -> list[dict]:
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notes(notes: list[dict]):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def add_note(user_id: int, user_name: str, text: str):
    notes = load_notes()
    notes.append({
        "from_id": user_id,
        "from_name": user_name,
        "text": text,
        "time": datetime.now().strftime("%b %d, %Y • %I:%M %p"),
    })
    save_notes(notes)

# ── Keyboards ────────────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🖼 Our Gallery", callback_data="memories"),
            InlineKeyboardButton("🎲 Surprise Me", callback_data="random"),
        ],
        [
            InlineKeyboardButton("💌 Leave a Note", callback_data="write_note"),
            InlineKeyboardButton("📬 Read Notes", callback_data="read_notes"),
        ],
        [
            InlineKeyboardButton("💕 Love Quote", callback_data="quote"),
            InlineKeyboardButton("🎂 Birthdays", callback_data="birthdays"),
        ],
        [
            InlineKeyboardButton("📅 Our Story", callback_data="story"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def photo_nav_keyboard(index: int, total: int) -> InlineKeyboardMarkup:
    """Navigation buttons for browsing photos one by one."""
    buttons = []
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"photo_{index - 1}"))
    nav_row.append(InlineKeyboardButton(f"📸 {index + 1}/{total}", callback_data="noop"))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"photo_{index + 1}"))
    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def notes_nav_keyboard(index: int, total: int) -> InlineKeyboardMarkup:
    """Navigation buttons for browsing notes one by one."""
    buttons = []
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"note_{index - 1}"))
    nav_row.append(InlineKeyboardButton(f"💌 {index + 1}/{total}", callback_data="noop"))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"note_{index + 1}"))
    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ────────────────────────────────────────────────────────────────────────────
#  Command handlers
# ────────────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 Sorry, this bot is private for Lu and Abi only.")
        return

    user_id = update.effective_user.id
    name = get_name(user_id)
    nickname = get_nickname_for_time()
    
    photos_count = len(get_photo_list())
    notes_count = len(load_notes())
    relationship = get_relationship_duration()
    
    # Check for special date
    special_message = check_special_date()
    
    # Personalize based on who's using
    if user_id == 6944104031:  # Lu
        greeting = f"Good {get_time_of_day()}, my beautiful {nickname}! 💕"
    else:  # Abi
        greeting = f"Good {get_time_of_day()}, Abi! Ready to see more of Lu? 💙"
    
    # Build message without Markdown first
    message_parts = []
    message_parts.append(f"✨ {greeting} ✨")
    message_parts.append("")
    
    if special_message:
        message_parts.append(f"🎊 {special_message} 🎊")
        message_parts.append("")
    
    # Relationship stats
    message_parts.append("━━━━━━━━━━━━━━━━━━━━━━")
    message_parts.append(f"📸 {photos_count} beautiful memories")
    message_parts.append(f"💌 {notes_count} love notes shared")
    message_parts.append(f"💑 Together for: {relationship['years']}y {relationship['months']}m {relationship['days']}d")
    message_parts.append(f"❤️ {relationship['total_days']} days of love")
    message_parts.append("━━━━━━━━━━━━━━━━━━━━━━")
    message_parts.append("")
    
    # Birthday countdowns
    lu_days = days_until_birthday(LU_BIRTHDAY)
    abi_days = days_until_birthday(ABI_BIRTHDAY)
    
    if user_id == 6944104031:  # Lu seeing her own countdown
        message_parts.append(f"🌸 Your birthday: {lu_days} days away")
        message_parts.append(f"💙 Abi's birthday: {abi_days} days away")
        message_parts.append("")
    else:  # Abi seeing
        message_parts.append(f"💙 Your birthday: {abi_days} days away")
        message_parts.append(f"🌸 Lu's birthday: {lu_days} days away")
        message_parts.append("")
    
    anniversary_days = get_next_anniversary()
    if anniversary_days == 0:
        message_parts.append("🎉 HAPPY ANNIVERSARY! 🎉")
        message_parts.append("")
    else:
        message_parts.append(f"💕 Next anniversary: {anniversary_days} days")
        message_parts.append("")
    
    message_parts.append("This is our private space — send photos to save")
    message_parts.append("memories, leave love notes, and celebrate our love.")
    message_parts.append("")
    message_parts.append("Tap a button below to get started:")
    
    # Join all parts with newlines
    full_message = "\n".join(message_parts)
    
    await update.message.reply_text(
        full_message,
        reply_markup=main_menu_keyboard(),
    )

def get_time_of_day() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    elif hour < 22:
        return "evening"
    else:
        return "night"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    user_id = update.effective_user.id
    if user_id == 6944104031:
        recipient = "Abi"
    else:
        recipient = "Lu"
    
    text = (
        "📖 Our Memory Bot — Guide\n\n"
        "━━━ 📷 Photos & Memories ━━━\n"
        "• Send any photo → saved as a memory\n"
        "• Add a caption → saved with the photo\n"
        f"• /memories → browse all photos (for you and {recipient})\n"
        "• /random → get a surprise photo\n\n"
        "━━━ 💌 Love Notes ━━━\n"
        f"• /note → write a message for {recipient}\n"
        "• /notes → read all love notes\n\n"
        "━━━ 💕 Special Features ━━━\n"
        "• /quote → get a romantic quote\n"
        "• /birthdays → check both our birthdays\n"
        "• /story → see our relationship timeline\n"
        "• /fortune → get a love fortune\n\n"
        "Made with ❤️ for Lu and Abi's love story."
    )
    await update.message.reply_text(text)

async def story_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    relationship = get_relationship_duration()
    
    story = (
        "📅 Our Love Story 💕\n\n"
        f"💑 Together for: {relationship['years']} years, {relationship['months']} months, {relationship['days']} days\n"
        f"❤️ That's {relationship['total_days']} days of love!\n\n"
        "Our Journey:\n"
    )
    
    for month, day, year, desc in MILESTONES:
        milestone_date = date(year, month, day)
        days_ago = (date.today() - milestone_date).days
        story += f"• {milestone_date.strftime('%B %d, %Y')}: {desc} ({days_ago} days ago)\n"
    
    story += "\nBirthdays:\n"
    story += f"🌸 Lu: April 17, 2001\n"
    story += f"💙 Abi: August 21, 2001\n"
    
    # Age difference
    lu_age = date.today().year - 2001 - ((date.today().month, date.today().day) < (4, 17))
    abi_age = date.today().year - 2001 - ((date.today().month, date.today().day) < (8, 21))
    story += f"\nAge now: Lu is {lu_age}, Abi is {abi_age}\n"
    
    if lu_age == abi_age:
        story += f"✨ We're the same age! Perfect match! ✨\n"
    elif lu_age > abi_age:
        story += f"🌸 Lu is {lu_age - abi_age} year{'s' if (lu_age - abi_age) != 1 else ''} older than Abi 💙\n"
    else:
        story += f"💙 Abi is {abi_age - lu_age} year{'s' if (abi_age - lu_age) != 1 else ''} older than Lu 🌸\n"
    
    await update.message.reply_text(story)

async def birthdays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    lu_days = days_until_birthday(LU_BIRTHDAY)
    abi_days = days_until_birthday(ABI_BIRTHDAY)
    
    lu_next = date(date.today().year, 4, 17)
    if lu_next < date.today():
        lu_next = date(date.today().year + 1, 4, 17)
    
    abi_next = date(date.today().year, 8, 21)
    if abi_next < date.today():
        abi_next = date(date.today().year + 1, 8, 21)
    
    # Visual countdown bars (using simple characters, no Markdown needed)
    def create_bar(days_left, total_days=365):
        filled = max(0, total_days - days_left)
        filled_bars = int((filled / total_days) * 20)
        return "█" * filled_bars + "░" * (20 - filled_bars)
    
    msg = (
        "🎂 Our Birthdays 🎂\n\n"
        f"🌸 Lu — April 17, 2001\n"
        f"📅 Next: {lu_next.strftime('%B %d, %Y')}\n"
        f"⏳ {lu_days} days to go\n"
        f"{create_bar(lu_days)}\n\n"
        f"💙 Abi — August 21, 2001\n"
        f"📅 Next: {abi_next.strftime('%B %d, %Y')}\n"
        f"⏳ {abi_days} days to go\n"
        f"{create_bar(abi_days)}\n\n"
    )
    
    # Special birthday message if it's someone's birthday
    if is_birthday_today(LU_BIRTHDAY):
        msg += "🎉🎂✨ HAPPY BIRTHDAY LU! ✨🎂🎉\n"
        msg += "The world became more beautiful on April 17, 2001! 🌸💖\n"
    elif is_birthday_today(ABI_BIRTHDAY):
        msg += "🎉🎂✨ HAPPY BIRTHDAY ABI! ✨🎂🎉\n"
        msg += "The world became more amazing on August 21, 2001! 💙💖\n"
    
    await update.message.reply_text(msg)

async def fortune_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    
    fortunes = [
        "🌟 Today you'll receive a sweet message from your love!",
        "💫 A beautiful memory will make you smile today.",
        "✨ Your love grows stronger with every passing day.",
        "🌈 Something wonderful is coming your way!",
        "💝 The universe has special plans for you two today.",
        "🌺 A surprise is waiting for you in your memories.",
        "⭐️ Today is perfect for creating new memories together.",
        "💖 Your love story is one for the ages!",
        "🎁 A pleasant surprise awaits you in the next 24 hours.",
        "🌙 Tonight, dream of beautiful moments together.",
    ]
    
    # Personalize based on user
    if update.effective_user.id == 6944104031:
        recipient = "Abi"
    else:
        recipient = "Lu"
    
    fortune = random.choice(fortunes)
    await update.message.reply_text(
        f"🔮 Love Fortune for {recipient} 🔮\n\n"
        f"{fortune}\n\n"
        f"Remember: The best fortune is having each other. ❤️"
    )

async def anniversary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """New command to show detailed anniversary info"""
    if not is_allowed(update.effective_user.id):
        return
    
    relationship = get_relationship_duration()
    next_anniversary = get_next_anniversary()
    
    # Calculate total days including leap years (more accurate)
    def days_between_dates(date1, date2):
        return abs((date2 - date1).days)
    
    # Calculate in different units
    total_days = relationship['total_days']
    total_weeks = total_days // 7
    total_months = relationship['years'] * 12 + relationship['months']
    total_hours = total_days * 24
    total_minutes = total_hours * 60
    
    msg = (
        f"💕 Our Anniversary Countdown 💕\n\n"
        f"📅 Together since: {RELATIONSHIP_START.strftime('%B %d, %Y')}\n"
        f"⏳ Time together:\n"
        f"   • {relationship['years']} years, {relationship['months']} months, {relationship['days']} days\n"
        f"   • {total_days} days\n"
        f"   • {total_weeks} weeks\n"
        f"   • {total_months} months\n"
        f"   • {total_hours:,} hours\n"
        f"   • {total_minutes:,} minutes\n\n"
    )
    
    if next_anniversary == 0:
        msg += "🎉 TODAY IS OUR ANNIVERSARY! 🎉\n"
        msg += "Celebrate your beautiful love story! 💑"
    else:
        msg += f"🎁 Next anniversary: {next_anniversary} days from now\n"
        
        # Add a little progress bar to the next anniversary
        total_year_days = 365
        days_passed_this_year = total_days % total_year_days
        progress = int((days_passed_this_year / total_year_days) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        msg += f"Progress to next anniversary:\n{bar}"
    
    await update.message.reply_text(msg)

# ────────────────────────────────────────────────────────────────────────────
#  Photos
# ────────────────────────────────────────────────────────────────────────────

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        stem = photo.file_id
        path = os.path.join(PHOTO_DIR, f"{stem}.jpg")
        await file.download_to_drive(path)

        # Save caption
        caption_text = update.message.caption or ""
        if caption_text:
            caption_path = os.path.join(CAPTION_DIR, f"{stem}.txt")
            with open(caption_path, "w", encoding="utf-8") as cf:
                cf.write(caption_text)

        # Save who sent it
        sender_name = get_name(update.effective_user.id)
        sender_path = os.path.join(CAPTION_DIR, f"{stem}_sender.txt")
        with open(sender_path, "w", encoding="utf-8") as sf:
            sf.write(sender_name)

        total = len(get_photo_list())
        
        # Different responses based on who sent it
        if update.effective_user.id == 6944104031:  # Lu
            response = (
                f"📸 Beautiful memory saved, Lu! ❤️\n\n"
                f"Saved by: {sender_name}\n"
                f"Total memories: {total}\n"
                "Abi will love seeing this! 💙\n"
            )
        else:  # Abi
            response = (
                f"📸 Perfect memory saved, Abi! ❤️\n\n"
                f"Saved by: {sender_name}\n"
                f"Total memories: {total}\n"
                "Lu will smile when she sees this! 🌸\n"
            )
        
        if caption_text:
            response += f'Caption: "{caption_text}"\n'
        response += "\nSend more photos to grow our collection! 🌹"

        await update.message.reply_text(response)
    except Exception as e:
        logger.error("Error saving photo: %s", e)
        await update.message.reply_text("😔 Oops! Something went wrong saving that. Please try again.")

async def show_memories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the photo gallery — show first photo with nav buttons."""
    if not is_allowed(update.effective_user.id):
        return

    photos = get_photo_list()
    if not photos:
        await update.message.reply_text(
            "📭 No memories yet!\n\n"
            "Send your first photo and let the magic begin! 💫"
        )
        return

    await _send_photo_at_index(update.message, photos, 0)

async def _send_photo_at_index(message, photos, index):
    """Send a single photo with caption + nav buttons."""
    photo_name = photos[index]
    stem = os.path.splitext(photo_name)[0]
    saved_caption = get_caption(stem)
    sender = get_sender(stem)

    caption = f"🖼 Memory {index + 1} of {len(photos)}\n"
    if sender:
        caption += f"📩 Sent by: {sender}\n"
    if saved_caption:
        caption += f"\n{saved_caption}"

    try:
        with open(os.path.join(PHOTO_DIR, photo_name), "rb") as pf:
            await message.reply_photo(
                pf,
                caption=caption,
                reply_markup=photo_nav_keyboard(index, len(photos)),
            )
    except Exception as e:
        logger.error("Error showing photo %d: %s", index, e)
        await message.reply_text("😔 Couldn't load that memory.")

async def random_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    photos = get_photo_list()
    if not photos:
        await update.message.reply_text(
            "📭 No memories yet!\n\nSend your first photo! 💫"
        )
        return

    index = random.randint(0, len(photos) - 1)
    chosen = photos[index]
    stem = os.path.splitext(chosen)[0]
    saved_caption = get_caption(stem)
    sender = get_sender(stem)

    # Personalize based on who's viewing
    if update.effective_user.id == 6944104031:
        viewer = "Lu"
    else:
        viewer = "Abi"

    caption = f"🎲 A surprise memory for {viewer}! 💞\n\n"
    if sender:
        caption += f"📩 Sent by: {sender}\n"
    if saved_caption:
        caption += f"{saved_caption}\n"
    caption += f"\nMemory {index + 1} of {len(photos)}"

    try:
        with open(os.path.join(PHOTO_DIR, chosen), "rb") as pf:
            await update.message.reply_photo(
                pf,
                caption=caption,
                reply_markup=photo_nav_keyboard(index, len(photos)),
            )
    except Exception as e:
        logger.error("Error sending random photo: %s", e)
        await update.message.reply_text("😔 Couldn't load that memory.")

# ────────────────────────────────────────────────────────────────────────────
#  Love Notes
# ────────────────────────────────────────────────────────────────────────────

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start writing a note — ask user for their message."""
    if not is_allowed(update.effective_user.id):
        return

    if update.effective_user.id == 6944104031:
        recipient = "Abi"
    else:
        recipient = "Lu"

    await update.message.reply_text(
        f"✏️ Write your love note for {recipient} 💌\n\n"
        f"Type your message below and I'll save it.\n"
        f"{recipient} will see it when they open /notes.\n\n"
        f"Type /cancel to go back."
    )
    return WAITING_FOR_NOTE

async def receive_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the note text."""
    if not is_allowed(update.effective_user.id):
        return ConversationHandler.END

    user_id = update.effective_user.id
    name = get_name(user_id)
    text = update.message.text.strip()

    add_note(user_id, name, text)
    total = len(load_notes())

    # Personalize response
    if user_id == 6944104031:
        response = (
            f"💌 Note saved, Lu! ❤️\n\n"
            f"From: {name}\n"
            f"Total notes: {total}\n\n"
            "Abi will smile reading this! 🥰"
        )
    else:
        response = (
            f"💌 Note saved, Abi! ❤️\n\n"
            f"From: {name}\n"
            f"Total notes: {total}\n\n"
            "Lu will love reading this! 🌸"
        )

    await update.message.reply_text(
        response,
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END

async def cancel_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ No worries! Come back whenever you're ready. 💖",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END

async def show_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the first note with navigation to browse all."""
    if not is_allowed(update.effective_user.id):
        return

    notes = load_notes()
    if not notes:
        await update.message.reply_text(
            "📭 No love notes yet!\n\n"
            "Be the first to leave one! Use /note 💌"
        )
        return

    # Show the most recent note first (reverse order)
    await _send_note_at_index(update.message, notes, len(notes) - 1)

async def _send_note_at_index(message, notes, index):
    """Send a single note with nav buttons."""
    note = notes[index]
    text = (
        f"💌 Note {index + 1} of {len(notes)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✍️ {note['text']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"From: {note['from_name']}\n"
        f"🕐 {note['time']}"
    )
    await message.reply_text(
        text,
        reply_markup=notes_nav_keyboard(index, len(notes)),
    )

# ────────────────────────────────────────────────────────────────────────────
#  Quote
# ────────────────────────────────────────────────────────────────────────────

async def love_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    quote = random.choice(LOVE_QUOTES)
    
    if update.effective_user.id == 6944104031:
        signature = "All my love, Abi 💙"
    else:
        signature = "All my love, Lu 🌸"
    
    await update.message.reply_text(
        f"💕 A little love note…\n\n"
        f"{quote}\n\n"
        f"— {signature}"
    )

# ────────────────────────────────────────────────────────────────────────────
#  Inline keyboard callback router
# ────────────────────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not is_allowed(query.from_user.id):
        return

    # Use query.message as the target for replies
    msg = query.message

    if data == "noop":
        return

    elif data == "main_menu":
        await msg.reply_text(
            "🏠 Main Menu\n\nWhat would you like to do?",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "memories":
        photos = get_photo_list()
        if not photos:
            await msg.reply_text(
                "📭 No memories yet! Send a photo to start! 💫"
            )
            return
        await _send_photo_at_index(msg, photos, 0)

    elif data.startswith("photo_"):
        index = int(data.split("_")[1])
        photos = get_photo_list()
        if 0 <= index < len(photos):
            await _send_photo_at_index(msg, photos, index)

    elif data == "random":
        photos = get_photo_list()
        if not photos:
            await msg.reply_text(
                "📭 No memories yet! Send a photo to start! 💫"
            )
            return
        index = random.randint(0, len(photos) - 1)
        await _send_photo_at_index(msg, photos, index)

    elif data == "write_note":
        if query.from_user.id == 6944104031:
            recipient = "Abi"
        else:
            recipient = "Lu"
            
        await msg.reply_text(
            f"✏️ Write your love note for {recipient} 💌\n\n"
            "Type your message below and I'll save it.\n"
            f"{recipient} will see it when they open /notes\n\n"
            "Type /cancel to go back."
        )
        # Set user data flag so the text handler picks it up
        context.user_data["awaiting_note"] = True

    elif data == "read_notes":
        notes = load_notes()
        if not notes:
            await msg.reply_text(
                "📭 No love notes yet!\n\nBe the first! Use /note 💌"
            )
            return
        await _send_note_at_index(msg, notes, len(notes) - 1)

    elif data.startswith("note_"):
        index = int(data.split("_")[1])
        notes = load_notes()
        if 0 <= index < len(notes):
            await _send_note_at_index(msg, notes, index)

    elif data == "quote":
        quote = random.choice(LOVE_QUOTES)
        if query.from_user.id == 6944104031:
            signature = "All my love, Abi 💙"
        else:
            signature = "All my love, Lu 🌸"
            
        await msg.reply_text(
            f"💕 A little love note…\n\n{quote}\n\n— {signature}"
        )

    elif data == "birthdays":
        await birthdays_command(update, context)

    elif data == "story":
        await story_command(update, context)

    elif data == "help":
        if query.from_user.id == 6944104031:
            recipient = "Abi"
        else:
            recipient = "Lu"
            
        text = (
            "📖 Quick Guide\n\n"
            "📷 Send photo → saves a memory\n"
            "🖼 /memories → browse photos\n"
            "🎲 /random → surprise photo\n"
            f"💌 /note → leave a note for {recipient}\n"
            "📬 /notes → read love notes\n"
            "💕 /quote → romantic quote\n"
            "🎂 /birthdays → check birthdays\n"
            "📅 /story → see our timeline\n"
            "🔮 /fortune → love fortune"
        )
        await msg.reply_text(text)

# ────────────────────────────────────────────────────────────────────────────
#  Handle text messages — notes mode or general
# ────────────────────────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    # If the user is writing a note via the button flow
    if context.user_data.get("awaiting_note"):
        context.user_data["awaiting_note"] = False
        user_id = update.effective_user.id
        name = get_name(user_id)
        text = update.message.text.strip()

        add_note(user_id, name, text)
        total = len(load_notes())

        # Personalize response
        if user_id == 6944104031:
            response = (
                f"💌 Note saved, Lu! ❤️\n\n"
                f"From: {name}\n"
                f"Total notes: {total}\n\n"
                "Abi will smile reading this! 🥰"
            )
        else:
            response = (
                f"💌 Note saved, Abi! ❤️\n\n"
                f"From: {name}\n"
                f"Total notes: {total}\n\n"
                "Lu will love reading this! 🌸"
            )

        await update.message.reply_text(
            response,
            reply_markup=main_menu_keyboard(),
        )
        return

    # General text — respond with something sweet
    user_id = update.effective_user.id
    name = get_name(user_id)
    
    sweet_responses = [
        f"Hey {name}! 💕 What would you like to do?",
        f"I'm listening, {name}! Want to check our memories or write a note? 📸💌",
        f"Everything okay, {name}? The menu below is always ready for you! 💖",
        f"{name}, you're the best thing that ever happened to me! Want to see our photos? 🖼️",
    ]
    
    await update.message.reply_text(
        random.choice(sweet_responses),
        reply_markup=main_menu_keyboard(),
    )

# ────────────────────────────────────────────────────────────────────────────
#  Main
# ────────────────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    note_conv = ConversationHandler(
        entry_points=[CommandHandler("note", note_command)],
        states={
            WAITING_FOR_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_note),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_note)],
    )

    app.add_handler(note_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("memories", show_memories))
    app.add_handler(CommandHandler("random", random_memory))
    app.add_handler(CommandHandler("notes", show_notes))
    app.add_handler(CommandHandler("quote", love_quote))
    app.add_handler(CommandHandler("birthdays", birthdays_command))
    app.add_handler(CommandHandler("story", story_command))
    app.add_handler(CommandHandler("fortune", fortune_command))
    app.add_handler(CommandHandler("anniversary", anniversary_command))

    app.add_handler(MessageHandler(filters.PHOTO, save_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("💖 Lu & Abi's Memory Bot is running…")

    app.run_polling()


if __name__ == "__main__":
    main()
