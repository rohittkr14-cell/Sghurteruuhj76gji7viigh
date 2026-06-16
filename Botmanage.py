import asyncio
import re
import os
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ChatPermissions, CallbackQuery
)
from pyrogram.errors import (
    ChatAdminRequired, UserAdminInvalid, RPCError,
    UsernameNotOccupied, PeerIdInvalid
)

API_ID = 36474759
API_HASH = "d3ca3639e29187dbf67b0111a02fc529"
BOT_TOKEN = "8671613935:AAFsG7gbKFjZ2VRdKQaJZnGTrut__K9M59w"

ADMIN_IDS = [7913633925, 7691071175]

BOT_USERNAME = "Secureblebot"
MM_SERVICE_USERNAME = "@Secureble"
MM_AGENT_USERNAME = "@shuify"

VOUCH_LINK = "https://t.me/Secureble/24?comment=1"

INR_PHOTO_FILE = "inr.jpg"
INR_CAPTION = (
    "**💳 UPI Payment Details**\n\n"
    "**UPI ID:** `example@upi`\n"
    "**UPI Name:** John Doe\n\n"
    "**💰 Deal Amount + {amount} Fees**"
)

CRYPTO_ADDRESS = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
CRYPTO_CAPTION = (
    "**₿ Crypto Payment Details**\n\n"
    "**Network:** Bitcoin\n"
    "**Address:** `{address}`\n\n"
    "**💰 Deal Amount + {amount} Fees**\n\n"
    "⚠️ Please double-check the network before sending."
)

edit_sessions = {}

app = Client(
    name="mm____bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

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
# /start
# ============================================================
@app.on_message(filters.command("start"))
async def start_private(client: Client, message: Message):
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
            photo="pfp1.jpg",
            caption=welcome_text,
            reply_markup=button
        )
    except Exception:
        await message.reply(welcome_text, reply_markup=button)


# ============================================================
# /set
# ============================================================
@app.on_message(filters.command("set"))
async def set_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    try:
        async for msg in client.get_chat_history(chat_id):
            try:
                await msg.delete()
            except Exception:
                pass
    except Exception:
        pass

    get_next_deal_number(chat_id)

    try:
        expire_date = datetime.now() + timedelta(hours=1)
        link = await client.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=2,
            expire_date=expire_date,
            name=f"Deal Link - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        link_msg = (
            f"Please join & share this with the other user involved in the deal.\n\n\n"
            f"🔗 **Invite Link - {link.invite_link} **\n"
        )
        await message.reply(link_msg)
    except Exception as e:
        await message.reply(f"❌ Error creating link: {e}")

    deal_msg = (
        "**Hey. Please state the terms of the deal.**\n\n"
        "• **What is the deal?**\n"
        "• **Who is the buyer/seller?**\n"
        "• **What is the agreed price and which crypto or currency.**\n"
        "• **Include any other relevant information**"
    )

    sent = await message.reply(deal_msg)
    
    try:
        await sent.pin(disable_notification=True)
    except Exception:
        pass


# ============================================================
# /rec
# ============================================================
@app.on_message(filters.command("rec"))
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
# /agree <user_id> - Updated: Sirf naam dikhega, click krte hi profile khulegi
# ============================================================
@app.on_message(filters.command("agree"))
async def agree_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    
    target_user_id = None
    if len(message.command) > 1:
        try:
            target_user_id = int(message.command[1].strip())
        except ValueError:
            await message.reply("❌ Usage: `/agree <user_id>`\nExample: `/agree 123456789`")
            return
    
    if not target_user_id:
        await message.reply("❌ Usage: `/agree <user_id>`\nExample: `/agree 123456789`")
        return
    
    chat_id = message.chat.id
    
    # Fetch user info for display
    try:
        target_user = await client.get_users(target_user_id)
        user_name = target_user.first_name or "User"
        # Clickable profile link using tg:// protocol
        user_link = f"[{user_name}](tg://user?id={target_user_id})"
    except Exception:
        user_link = f"User (`{target_user_id}`)"
    
    agree_text = (
        "**📝 Deal Agreement**\n\n"
        "Please confirm that you agree to the terms stated above.\n\n"
        f" **{user_link}** can confirm this agreement.\n\n"
        "Click the button below to confirm your agreement."
    )

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Agreed ", callback_data=f"agree_confirm|{target_user_id}|{chat_id}")]
    ])

    sent = await message.reply(agree_text, reply_markup=button)
    try:
        await sent.pin(disable_notification=True)
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^agree_confirm\|"))
async def agree_callback(client: Client, callback_query: CallbackQuery):
    msg = callback_query.message
    user = callback_query.from_user
    
    data = callback_query.data.split("|")
    target_user_id = int(data[1])
    
    # Check if the clicking user's ID matches the target user ID
    if user.id != target_user_id:
        await callback_query.answer("❌ Only that user can confirm this agreement!", show_alert=True)
        return
    
    new_text = (
        "✅ **Agreed by the dealer.** 🤝\n\n"
        f"Both users have agreed to the deal terms.\n"
        f"Confirmed by: {user.mention}\n\n"
        "Now, continue the deal ."
    )
    
    await msg.edit_text(new_text, reply_markup=None)
    await callback_query.answer("✅ Agreement confirmed!", show_alert=False)


# ============================================================
# /confirm <user_id> - Updated: Do buttons - Release aur Refund
# ============================================================
@app.on_message(filters.command("confirm"))
async def confirm_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    
    target_user_id = None
    if len(message.command) > 1:
        try:
            target_user_id = int(message.command[1].strip())
        except ValueError:
            await message.reply("❌ Usage: `/confirm <user_id>`\nExample: `/confirm 123456789`")
            return
    
    if not target_user_id:
        await message.reply("❌ Usage: `/confirm <user_id>`\nExample: `/confirm 123456789`")
        return
    
    chat_id = message.chat.id
    
    # Fetch user info for display
    try:
        target_user = await client.get_users(target_user_id)
        user_name = target_user.first_name or "User"
        user_link = f"[{user_name}](tg://user?id={target_user_id})"
    except Exception:
        user_link = f"User (`{target_user_id}`)"
    
    confirm_text = (
        "**🔄 Final Confirmation**\n\n"
        "When deal is Done. Please choose an action:\n\n"
        f"Only **{user_link}** can make this decision.\n\n"
        "• **Release** - Funds will be released to the seller\n"
        "• **Refund** - Funds will be refunded to the buyer"
    )

    button = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Release", callback_data=f"confirm_release|{target_user_id}|{chat_id}"),
            InlineKeyboardButton("↩️ Refund", callback_data=f"confirm_refund|{target_user_id}|{chat_id}")
        ]
    ])

    sent = await message.reply(confirm_text, reply_markup=button)
    try:
        await sent.pin(disable_notification=True)
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^confirm_(release|refund)\|"))
async def confirm_callback(client: Client, callback_query: CallbackQuery):
    msg = callback_query.message
    user = callback_query.from_user
    
    data = callback_query.data.split("|")
    action = data[0].split("_")[1]  # "release" or "refund"
    target_user_id = int(data[1])
    
    # Check if the clicking user's ID matches the target user ID
    if user.id != target_user_id:
        await callback_query.answer("❌ Only the specified user can make this decision!", show_alert=True)
        return
    
    if action == "release":
        await msg.edit_text(
            "✅ **Funds Released initiated** 🎉\n\n"
            f"The buyer has agreed to release the funds.\n"
            f"Action taken by: {user.mention}",
            reply_markup=None
        )
        
        await callback_query.answer("✅ Release confirmed!", show_alert=False)
        
        await msg.reply(
            f"**Released confirmation occurs** 🚀\n\n"
            f"@{MM_AGENT_USERNAME.replace('@', '')} please release the funds .\n\n"
            f"Seller, Please Drop the Qr or upi !\n\n"
            f"**Now , Wait @shuify Responspe as soon as possible.**"
        )
    
    elif action == "refund":
        await msg.edit_text(
            "↩️ **Refund Initiated** 🔄\n\n"
            f"The buyer has requested a refund.\n"
            f"Action taken by: {user.mention}",
            reply_markup=None
        )
        
        await callback_query.answer("↩️ Refund confirmed!", show_alert=False)
        
        await msg.reply(
            f"**Refund confirmation occurs** ↩️\n\n"
            f"@{MM_AGENT_USERNAME.replace('@', '')} please process the refund .\n\n"
            f"Refund has been requested!\n"
            f"Seller Please Confirm this Refund and Buyer Drop the Qr or Upi.\n\n"
            f"**Now , Wait @shuify Responspe as soon as possible.**"
        )


# ============================================================
# /inr <amount>
# ============================================================
@app.on_message(filters.command("inr"))
async def inr_payment(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    
    amount = None
    if len(message.command) > 1:
        amount = message.command[1].strip()
    
    if not amount:
        await message.reply("❌ Usage: `/inr <amount>`\nExample: `/inr 5000`")
        return
    
    inr_msg = (
        "**Pay on this Qr, Must Send the payment Screenshot.**\n\n"
        f"**💰 Deal Amount + {amount} Fees**"
    )

    try:
        if os.path.exists(INR_PHOTO_FILE):
            await message.reply_photo(
                photo=INR_PHOTO_FILE,
                caption=inr_msg
            )
        else:
            await message.reply(inr_msg)
    except Exception:
        await message.reply(inr_msg)


# ============================================================
# /crp <amount>
# ============================================================
@app.on_message(filters.command("crp"))
async def crp_payment(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    
    amount = None
    if len(message.command) > 1:
        amount = message.command[1].strip()
    
    if not amount:
        await message.reply("❌ Usage: `/crp <amount>`\nExample: `/crp 0.005`")
        return
    
    crp_msg = (
        "**Network:** Bep20\n"
        f"**Address:** `{CRYPTO_ADDRESS}`\n\n"
        f"**💰 Deal Amount + {amount} Fees**\n\n"
        "⚠️ Please double-check the network before sending."
    )
    
    await message.reply(crp_msg)


# ============================================================
# /link
# ============================================================
@app.on_message(filters.command("link"))
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
            f"Please join & share this with the other user involved in the deal.\n\n\n"
            f"🔗 **Invite Link - {link.invite_link} **\n"
        )

        await message.reply(link_msg)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ============================================================
# /done
# ============================================================
@app.on_message(filters.command("done"))
async def done_deal(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return
    
    if not is_admin_user(message.from_user.id):
        await delete_command(message)
        return

    await delete_command(message)
    chat_id = message.chat.id

    deal_num = None
    if len(message.command) > 1:
        try:
            deal_num = int(message.command[1])
        except ValueError:
            deal_num = group_deal_map.get(chat_id, {}).get("deal_number", "1")
    else:
        deal_num = group_deal_map.get(chat_id, {}).get("deal_number", "1")

    try:
        await client.set_chat_title(chat_id, f" Deal #{deal_num} • @Completed ")
    except Exception:
        pass

    done_msg = (
        f"Thank you for using my Middleman service! 🤝\n\n"
        f"Please leave me a vouch here:\n"
        f"{VOUCH_LINK}\n\n"
        f"Tap to copy - `Vouch {MM_AGENT_USERNAME} MM'd`"
   )
   
    await message.reply(done_msg)


# ============================================================
# /lock / /unlock / /kick / /ban / /mute / /unmute / /id
# ============================================================
@app.on_message(filters.command("lock"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("unlock"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("kick"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("ban"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("mute"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("unmute"))
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
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("id"))
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
# ADMIN DM COMMANDS
# ============================================================
@app.on_message(filters.command("editinr") & filters.private)
async def edit_inr(client: Client, message: Message):
    if not is_admin_user(message.from_user.id):
        return
    
    user_id = message.from_user.id
    edit_sessions[user_id] = {"mode": "inr", "step": "awaiting_text"}
    
    await message.reply(
        "📝 **Edit INR/UPI Payment Details**\n\n"
        "Send me the new UPI details text.\n"
        "Use `{amount}` where you want the deal amount to appear.\n"
        "You can use Markdown.\n\n"
        f"**Current:**\n{INR_CAPTION}\n\n"
        "To change photo: /setinrphoto\n"
        "To cancel: /cancel"
    )


@app.on_message(filters.command("setinrphoto") & filters.private)
async def set_inr_photo_start(client: Client, message: Message):
    if not is_admin_user(message.from_user.id):
        return
    
    user_id = message.from_user.id
    edit_sessions[user_id] = {"mode": "inr", "step": "awaiting_photo"}
    
    await message.reply(
        "📸 **Set INR/UPI Photo**\n\n"
        "Send me a photo to use for UPI payments.\n"
        "Just upload the image directly.\n\n"
        "To cancel: /cancel"
    )


@app.on_message(filters.command("editcrp") & filters.private)
async def edit_crp(client: Client, message: Message):
    if not is_admin_user(message.from_user.id):
        return
    
    user_id = message.from_user.id
    edit_sessions[user_id] = {"mode": "crp", "step": "awaiting_address"}
    
    await message.reply(
        "📝 **Edit Crypto Payment Details**\n\n"
        "Step 1: Send me the **new crypto address** (or /skip to keep current).\n\n"
        f"**Current address:** `{CRYPTO_ADDRESS}`\n\n"
        "To cancel: /cancel"
    )


@app.on_message(filters.command("cancel") & filters.private)
async def cancel_edit(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in edit_sessions:
        edit_sessions.pop(user_id, None)
        await message.reply("❌ Editing cancelled.")
    else:
        await message.reply("No active editing session.")


@app.on_message(filters.photo & filters.private)
async def handle_inr_photo(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_admin_user(user_id):
        return
    
    session = edit_sessions.get(user_id)
    if not session or session.get("mode") != "inr" or session.get("step") != "awaiting_photo":
        return
    
    global INR_PHOTO_FILE
    file_path = await message.download(file_name=INR_PHOTO_FILE)
    if file_path:
        INR_PHOTO_FILE = file_path
        edit_sessions.pop(user_id, None)
        await message.reply("✅ INR/UPI photo has been updated!")
    else:
        await message.reply("❌ Failed to download photo. Try again.")


@app.on_message(filters.text & filters.private)
async def handle_edit_text(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_admin_user(user_id):
        return
    
    session = edit_sessions.get(user_id)
    if not session:
        return
    
    text = message.text
    mode = session.get("mode")
    step = session.get("step")
    
    global INR_CAPTION, CRYPTO_ADDRESS, CRYPTO_CAPTION
    
    if mode == "inr":
        if step == "awaiting_text":
            INR_CAPTION = text
            edit_sessions.pop(user_id, None)
            await message.reply("✅ INR/UPI payment details updated!")
            await message.reply(f"**Preview (template):**\n\n{INR_CAPTION}")
    
    elif mode == "crp":
        if step == "awaiting_address":
            if text.lower() == "/skip":
                await message.reply(f"✅ Address kept unchanged: `{CRYPTO_ADDRESS}`")
            else:
                CRYPTO_ADDRESS = text.strip()
                await message.reply(f"✅ Address updated to: `{CRYPTO_ADDRESS}`")
            
            edit_sessions[user_id]["step"] = "awaiting_caption"
            await message.reply(
                "Step 2: Send me the **new caption** (fee info, network, etc.)\n\n"
                f"**Current:**\n{CRYPTO_CAPTION}\n\n"
                "To cancel: /cancel"
            )
        
        elif step == "awaiting_caption":
            CRYPTO_CAPTION = text
            edit_sessions.pop(user_id, None)
            await message.reply("✅ Crypto payment details updated!")
            preview = CRYPTO_CAPTION.format(address=CRYPTO_ADDRESS, amount="{amount}")
            await message.reply(f"**Preview:**\n\n{preview}")


# ============================================================
# /help
# ============================================================
@app.on_message(filters.command("help"))
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
        "`/set` - Clear msgs + send invite link + deal msg + pin\n"
        "`/rec` - Confirm payment received & pin\n"
        "`/agree <user_id>` - Send agreement (only that user can confirm)\n"
        "`/confirm <user_id>` - Send release/refund buttons (only that user can decide)\n"
        "`/inr <amount>` - Send UPI payment details with amount\n"
        "`/crp <amount>` - Send crypto payment details with amount\n"
        "`/link` - Create invite link only\n"
        "`/done <number>` - Mark deal completed + set group name\n\n"
        "**Group Control:**\n"
        "`/lock` - Lock group (read-only)\n"
        "`/unlock` - Unlock group\n\n"
        "**User Management (reply to their message):**\n"
        "`/kick` / `/ban` / `/mute` / `/unmute`\n\n"
        "**Admin DM Only (edit config via bot):**\n"
        "`/setinrphoto` - Change UPI photo\n"
        "`/editcrp` - Edit crypto address & fees\n"
        "`/cancel` - Cancel any editing session\n\n"
        "**Utility:**\n"
        "`/id` - Show IDs\n"
        "`/help` - This message"
    )

    await message.reply(help_text)


@app.on_message(filters.command)
async def ignore_non_admin(client: Client, message: Message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not is_admin_user(message.from_user.id):
            try:
                await message.delete()
            except Exception:
                pass


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 MM BOT STARTING...")
    print(f"   Admin IDs: {ADMIN_IDS}")
    print(f"   Bot: @{BOT_USERNAME}")
    print("=" * 50)
    print("Bot is running! Press Ctrl+C to stop.")
    
    app.run()