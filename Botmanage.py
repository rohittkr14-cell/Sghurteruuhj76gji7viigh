import asyncio
import re
import os
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ChatPermissions, ChatPrivileges
)
from pyrogram.errors import (
    ChatAdminRequired, UserAdminInvalid, RPCError,
    UsernameNotOccupied, PeerIdInvalid
)

# ============================================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================================
API_ID = 34365075              # Your API ID from my.telegram.org
API_HASH = "23c4c0cd9fef652b967d9f2b66cbf560" # Your API Hash from my.telegram.org
BOT_TOKEN = "8998766171:AAFNNQkOCDuX6sx3PCHMGmrjmpbbywjuiz4" # Bot token from @BotFather

# Admin user IDs who can use all commands (YOUR TELEGRAM IDS)
ADMIN_IDS = [7913633925, 7691071175]  # Already set to your IDs

# Bot usernames for branding
BOT_USERNAME = "Secureblebot"     # Your bot's username
MM_SERVICE_USERNAME = "@Secureble"   # Middleman service username
MM_AGENT_USERNAME = "@shuify"     # MM agent username

# Vouch link - REPLACE WITH YOUR ACTUAL VOUCH LINK
VOUCH_LINK = "https://t.me/Secureble/24?comment=1"

# ============================================================
# INITIALIZE CLIENT
# ============================================================
app = Client(
    name="mm_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ============================================================
# DEAL TRACKING
# ============================================================
deal_counter = 0
group_deal_map = {}


def is_admin_user(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_next_deal_number(chat_id: int) -> int:
    global deal_counter
    deal_counter += 1
    group_deal_map[chat_id] = {"deal_number": deal_counter}
    return deal_counter


async def delete_command(msg: Message):
    try:
        await msg.delete()
    except Exception:
        pass


# ============================================================
# HANDLER: /start in private chat
# ============================================================
@app.on_message(filters.command(["start"]))
async def start_private(client: Client, message: Message):
    # Agar group me hai to ignore karo
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await delete_command(message)
        return

    welcome_text = (
        f"Welcome to the MM Service of {MM_SERVICE_USERNAME}.\n"
        f"Contact Below For Making Secure Gc.\n\n"
        f"Thank you, Have a Nice Day."
    )

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📩 Contact MM",
            url=f"https://t.me/{MM_AGENT_USERNAME.replace('@', '')}"
        )]
    ])

    try:
        await message.reply_photo(
            photo="https://telegra.ph/file/d1c7c8c0a9c1b0a8c8f1e.jpg",
            caption=welcome_text,
            reply_markup=button
        )
    except Exception:
        await message.reply(welcome_text, reply_markup=button)


# ============================================================
# COMMAND: /set
# ============================================================
@app.on_message(filters.command(["set"]))
async def set_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    # Delete all messages
    try:
        async for msg in client.get_chat_history(chat_id):
            try:
                await msg.delete()
            except Exception:
                pass
    except Exception:
        pass

    deal_num = get_next_deal_number(chat_id)

    deal_msg = (
        "**Hey. Please state the terms of the deal.**\n\n"
        "• **What is the deal?**\n"
        "• **Who is the buyer/seller?**\n"
        "• **What is the agreed price?**\n"
        "• **Include any other relevant information**"
    )

    sent = await message.reply(deal_msg)
    try:
        await sent.pin(disable_notification=True)
    except Exception:
        pass


# ============================================================
# COMMAND: /rec
# ============================================================
@app.on_message(filters.command(["rec"]))
async def rec_payment(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    rec_msg = (
        "✅ **I have successfully received the amount and the MM fee.**\n"
        "It is safe to deal forward.\n\n"
        "I will process the payment after the deal concludes.\n"
        "Thank you for your cooperation and for your trust!"
    )

    sent = await message.reply(rec_msg)
    try:
        await sent.pin(disable_notification=True)
    except Exception:
        pass


# ============================================================
# COMMAND: /link
# ============================================================
@app.on_message(filters.command(["link"]))
async def create_invite_link(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    try:
        expire_date = datetime.now() + timedelta(hours=1)
        link = await client.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=2,
            expire_date=expire_date,
            name=f"Deal Link - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        link_msg = (
            f"🔗 **Invite Link Created**\n\n"
            f"Link: {link.invite_link}\n"
            f"⏱ Timezone: {expire_date.strftime('%H:%M:%S')}\n"
            f"Once both Users join, proceed with the deal."
        )

        await message.reply(link_msg)

    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights with 'Invite Users' permission.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /done <number> - EG: /done 263 or /done 69
# Group name set: "Completed Deal #263 • @Secureble"
# ============================================================
@app.on_message(filters.command(["done"]))
async def done_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    # Get deal number from command argument
    # /done 263  => number = 263
    # /done      => number = auto from map
    deal_num = None
    if len(message.command) > 1:
        try:
            deal_num = int(message.command[1])
        except ValueError:
            deal_num = group_deal_map.get(chat_id, {}).get("deal_number", "1")
    else:
        deal_num = group_deal_map.get(chat_id, {}).get("deal_number", "1")

    # Group name: "Completed Deal #N • @Secureble"
    try:
        await client.set_chat_title(chat_id, f"Completed Deal #{deal_num} • {MM_SERVICE_USERNAME}")
    except Exception:
        pass

    # Completion message
    done_msg = (
        f"Thank you for using my Middleman service! 🤝\n\n"
        f"Please leave me a vouch here:\n"
        f"{VOUCH_LINK}\n\n"
        f"Tap to copy - Vouch {MM_AGENT_USERNAME} MM'd"
    )

    await message.reply(done_msg)


# ============================================================
# COMMAND: /lock
# ============================================================
@app.on_message(filters.command(["lock"]))
async def lock_group(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        await client.set_chat_permissions(chat_id, permissions)
        await message.reply("🔒 **Group has been locked.** Have a Nice Day, Byy. ")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights with 'Restrict Members' permission.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /unlock
# ============================================================
@app.on_message(filters.command(["unlock"]))
async def unlock_group(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False,
        )
        await client.set_chat_permissions(chat_id, permissions)
        await message.reply("🔓 **Group has been unlocked.** Members can now send messages.")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights with 'Restrict Members' permission.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /kick
# ============================================================
@app.on_message(filters.command(["kick"]))
async def kick_user(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("❌ Reply to a user's message to kick them.")
        return

    target = message.reply_to_message.from_user
    chat_id = message.chat.id

    try:
        await client.ban_chat_member(chat_id, target.id)
        await client.unban_chat_member(chat_id, target.id)
        await message.reply(f"👢 **Kicked:** {target.mention}")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights to kick users.")
    except UserAdminInvalid:
        await message.reply("❌ Cannot kick another admin.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /ban
# ============================================================
@app.on_message(filters.command(["ban"]))
async def ban_user(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("❌ Reply to a user's message to ban them.")
        return

    target = message.reply_to_message.from_user
    chat_id = message.chat.id

    try:
        await client.ban_chat_member(chat_id, target.id)
        await message.reply(f"🚫 **Banned:** {target.mention}")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights to ban users.")
    except UserAdminInvalid:
        await message.reply("❌ Cannot ban another admin.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /mute
# ============================================================
@app.on_message(filters.command(["mute"]))
async def mute_user(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("❌ Reply to a user's message to mute them.")
        return

    target = message.reply_to_message.from_user
    chat_id = message.chat.id

    try:
        permissions = ChatPermissions(can_send_messages=False)
        await client.restrict_chat_member(chat_id, target.id, permissions)
        await message.reply(f"🔇 **Muted:** {target.mention}")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights to restrict users.")
    except UserAdminInvalid:
        await message.reply("❌ Cannot mute another admin.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /unmute
# ============================================================
@app.on_message(filters.command(["unmute"]))
async def unmute_user(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("❌ Reply to a user's message to unmute them.")
        return

    target = message.reply_to_message.from_user
    chat_id = message.chat.id

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
        )
        await client.restrict_chat_member(chat_id, target.id, permissions)
        await message.reply(f"🔊 **Unmuted:** {target.mention}")
    except ChatAdminRequired:
        await message.reply("❌ Bot needs admin rights to restrict users.")
    except UserAdminInvalid:
        await message.reply("❌ Cannot unmute another admin.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# COMMAND: /id
# ============================================================
@app.on_message(filters.command(["id"]))
async def show_id(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    chat = message.chat
    user = message.from_user
    target = message.reply_to_message.from_user if message.reply_to_message else user

    await message.reply(
        f"📋 **IDs:**\n"
        f"• **Chat ID:** `{chat.id}`\n"
        f"• **Your ID:** `{user.id}`\n"
        f"• **Target ID:** `{target.id}`"
    )


# ============================================================
# COMMAND: /help
# ============================================================
@app.on_message(filters.command(["help"]))
async def help_command(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)

    help_text = (
        "**📋 Available Commands**\n\n"
        "**Deal Management:**\n"
        "`/set` - Clear all messages & start new deal\n"
        "`/rec` - Confirm payment received & pin\n"
        "`/link` - Create invite link (expires after 2 joins)\n"
        "`/done <number>` - Mark deal completed + set group name\n\n"
        "**Group Control:**\n"
        "`/lock` - Lock group (read-only) / `unlock` - Unlock\n\n"
        "**User Management (reply to their message):**\n"
        "`/kick` / `/ban` / `/mute` / `/unmute`\n\n"
        "**Utility:**\n"
        "`/id` - Show IDs | `/help` - This message"
    )

    await message.reply(help_text)


# ============================================================
# IGNORE ALL NON-ADMIN COMMANDS IN GROUP
# ============================================================
@app.on_message(filters.command)
async def ignore_non_admin(client: Client, message: Message):
    """Sirf group me non-admin commands ko delete karo"""
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not is_admin_user(message.from_user.id):
            try:
                await message.delete()
            except Exception:
                pass


# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 MM BOT STARTING...")
    print(f"   Admin IDs: {ADMIN_IDS}")
    print(f"   Bot: @{BOT_USERNAME}")
    print("=" * 50)
    print("Bot is running! Press Ctrl+C to stop.")
    
    app.run()