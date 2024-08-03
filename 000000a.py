from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsRecent, ChannelParticipantsSearch
import asyncio

API_ID = '22962676'
API_HASH = '543e9a4d695fe8c6aa4075c9525f7c57'
BOT_TOKEN = '6377543293:AAEnQQiFpz7GiXBZZTkiK0Z-ZuVe5Rk1FIs'
ADMINS = [1062643042, 5539340469]
MOVIE_CHANNEL_ID = -1002185652972
SERIAL_CHANNEL_ID = -1002236615134
MULTFILM_CHANNEL_ID = -1002194981983
GROUP_ID = -1002240152081

user_states = {}
user_messages = {}
user_ids = set()
media_data = {
    "movie": {},
    "serial": {},
    "multfilm": {}
}

mandatory_channels = []

links = {
    "movies": "https://t.me/your_movie_channel_link",
    "serials": "https://t.me/your_serial_channel_link",
    "multfilms": "https://t.me/your_multfilm_channel_link"
}

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_subscribed(user_id, channel_id):
    try:
        result = await bot(GetParticipantsRequest(
            channel_id, ChannelParticipantsSearch(''), 0, 1000, hash=0))
        for participant in result.participants:
            if participant.user_id == user_id:
                return True
        return False
    except:
        return False

async def check_subscription(event):
    not_subscribed_channels = []
    for channel in mandatory_channels:
        if not await is_subscribed(event.sender_id, channel['id']):
            not_subscribed_channels.append(channel)
    
    if not_subscribed_channels:
        channels_list = "\n".join([f"{channel['link']}" for channel in not_subscribed_channels])
        await event.respond(f"Botdan to'liq foydalanish uchun ushbu kanallarga a'zo bo'lishingiz kerak\n{channels_list} \n\n A'zo bo'lib botni qayta ishga tushuring \n\n⬇️\n /start /start /start")
        return False
    return True

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not await check_subscription(event):
        return
    
    user_ids.add(event.sender_id)
    buttons = [
        [Button.text("Kino qidirish🔍"), Button.text("Multfilim qidirish🔍")],
        [Button.text("Serial / Drama qidirish🔍")],
        [Button.text("Filimlar royxati🔍")],
        [Button.text("Admin bilan aloqa👨‍💻")]
    ]
    if event.sender_id in ADMINS:
        buttons.append([Button.text("Admin Panel")])
    await event.respond('Menyudan tanlang⌨️', buttons=buttons)

@bot.on(events.NewMessage(pattern='Admin bilan aloqa'))
async def admin_contact(event):
    if not await check_subscription(event):
        return
    
    buttons = [
        [Button.text("Bot orqali bog'lanish🤖"), Button.text("Telegram orqali bog'lanish✈️")],
        [Button.text("Orqaga qaytish⬅️")]
    ]
    await event.respond('Admin bilan bog\'lanish uchun variantni tanlang:', buttons=buttons)

@bot.on(events.NewMessage(pattern="Orqaga qaytish"))
async def back_to_main(event):
    await start(event)

@bot.on(events.NewMessage(pattern="Bot orqali bog'lanish🤖"))
async def bot_contact(event):
    if not await check_subscription(event):
        return
    
    user_states[event.sender_id] = "awaiting_message"
    await event.respond('Xabaringizni qoldiring:')

    await asyncio.sleep(30)
    if user_states.get(event.sender_id) == "awaiting_message":
        del user_states[event.sender_id]
        await event.respond("Xabar kiritilmadi. Asosiy menyu:", buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Telegram orqali bog'lanish"))
async def telegram_contact(event):
    if not await check_subscription(event):
        return
    
    await event.respond("Admin bilan Telegram orqali bog'lanish \n\n\n @Bot_adminni")

@bot.on(events.NewMessage)
async def handle_message(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]
        if state == "awaiting_message":
            user_states[user_id] = {
                "state": "awaiting_confirmation",
                "message": event.text
            }
            buttons = [
                [Button.inline("✅Ha, tasdiqlayman", b"confirm"), Button.inline("⛔️Yo'q, bekor qilish", b"cancel")]
            ]
            await event.respond(f'Xabaringizni yuborishni tasdiqlaysizmi?\n\n{event.text}', buttons=buttons)
        elif state.get("state") in ["awaiting_movie_name", "awaiting_serial_name", "awaiting_multfilm_name"]:
            user_states[user_id]['name'] = event.text
            user_states[user_id]['state'] = 'awaiting_post_url'
            await event.respond("Post URL kiriting:", buttons=[[Button.text("Bekor qilish")]])
        elif state.get("state") == "awaiting_post_url":
            user_states[user_id]['post_url'] = event.text
            user_states[user_id]['state'] = 'awaiting_code'
            await event.respond("Kodini kiriting:", buttons=[[Button.text("Bekor qilish")]])
        elif state.get("state") == "awaiting_code":
            user_states[user_id]['code'] = event.text
            media_type = state["type"]
            await save_media(state, media_type)
            await event.respond(f"{media_type.capitalize()} qo'shildi:\nNomi: {state['name']}\nKodi: {state['code']}", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_code_search":
            await search_media_by_code(event, state)
        elif state.get("state") == "awaiting_code_delete":
            media_type = state["type"]
            await delete_media(event, media_type)
            del user_states[user_id]
        elif state.get("state") == "awaiting_ad_message":
            user_states[user_id] = {
                "state": "awaiting_ad_media",
                "ad_message": event.text
            }
            await event.respond("Reklama media faylini jo'nating (agar kerak bo'lsa). Agar media yubormoqchi bo'lmasangiz, 'Tasdiqlash' tugmasini bosing.", buttons=[Button.inline("Tasdiqlash", b"confirm_ad_no_media")])
        elif state.get("state") == "awaiting_movie_link":
            links["movies"] = event.text
            await event.respond("Kino kanali linki yangilandi.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_serial_link":
            links["serials"] = event.text
            await event.respond("Serial kanali linki yangilandi.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_multfilm_link":
            links["multfilms"] = event.text
            await event.respond("Multfilm kanali linki yangilandi.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_admin_add":
            try:
                new_admin_id = int(event.text)
                ADMINS.append(new_admin_id)
                await event.respond(f"Admin {new_admin_id} qo'shildi", buttons=[[Button.text('/start')]])
            except ValueError:
                await event.respond("Noto'g'ri ID kiritildi. Qayta urinib ko'ring.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_admin_remove":
            try:
                remove_admin_id = int(event.text)
                if remove_admin_id in ADMINS:
                    ADMINS.remove(remove_admin_id)
                    await event.respond(f"Admin {remove_admin_id} o'chirildi.", buttons=[[Button.text('/start')]])
                else:
                    await event.respond(f"Admin ID {remove_admin_id} topilmadi.", buttons=[[Button.text('/start')]])
            except ValueError:
                await event.respond("Noto'g'ri ID kiritildi. Qayta urinib ko'ring.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_mandatory_channel_link":
            user_states[user_id]['link'] = event.text
            user_states[user_id]['state'] = 'awaiting_mandatory_channel_id'
            await event.respond("Kanal ID'sini kiriting:", buttons=[[Button.text("Bekor qilish")]])
        elif state.get("state") == "awaiting_mandatory_channel_id":
            try:
                channel_id = int(event.text)
                mandatory_channels.append({"id": channel_id, "link": user_states[user_id]['link']})
                await event.respond(f"Kanal {channel_id} qo'shildi.", buttons=[[Button.text('/start')]])
            except ValueError:
                await event.respond("Noto'g'ri ID kiritildi. Qayta urinib ko'ring.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        elif state.get("state") == "awaiting_mandatory_channel_remove":
            try:
                channel_id = int(event.text)
                for channel in mandatory_channels:
                    if channel['id'] == channel_id:
                        mandatory_channels.remove(channel)
                        await event.respond(f"Kanal {channel_id} o'chirildi.", buttons=[[Button.text('/start')]])
                        break
                else:
                    await event.respond(f"Kanal ID {channel_id} topilmadi.", buttons=[[Button.text('/start')]])
            except ValueError:
                await event.respond("Noto'g'ri ID kiritildi. Qayta urinib ko'ring.", buttons=[[Button.text('/start')]])
            del user_states[user_id]
        else:
            return

@bot.on(events.NewMessage)
async def handle_media(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]
        if state.get("state") == "awaiting_ad_media":
            if event.photo or event.video or event.document:
                user_states[user_id] = {
                    "state": "awaiting_ad_confirmation",
                    "ad_message": state["ad_message"],
                    "ad_media": event.media
                }
                buttons = [
                    [Button.inline("Ha, tasdiqlayman", b"confirm_ad"), Button.inline("Yo'q, bekor qilish", b"cancel_ad")]
                ]
                await event.respond(f'Reklamani yuborishni tasdiqlaysizmi?\n\n{state["ad_message"]}', buttons=buttons)
            else:
                await event.respond("Iltimos, faqat media fayl jo'nating.")

@bot.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]
        if state["state"] == "awaiting_confirmation":
            if event.data == b"confirm":
                user_message = state["message"]
                sent_message = await bot.send_message(GROUP_ID, f"Foydalanuvchi xabari:\n\n{user_message}")
                user_messages[sent_message.id] = user_id
                await event.edit("Xabaringiz  yuborildi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
            elif event.data == b"cancel":
                await event.edit("Xabar bekor qilindi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
        elif state["state"] == "awaiting_ad_confirmation":
            if event.data == b"confirm_ad":
                ad_message = state["ad_message"]
                ad_media = state.get("ad_media")
                for user in user_ids:
                    if ad_media:
                        await bot.send_file(user, ad_media, caption=ad_message)
                    else:
                        await bot.send_message(user, ad_message)
                await event.edit("Reklama foydalanuvchilarga yuborildi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
            elif event.data == b"cancel_ad":
                await event.edit("Reklama bekor qilindi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
            elif event.data == b"confirm_ad_no_media":
                ad_message = state["ad_message"]
                for user in user_ids:
                    await bot.send_message(user, ad_message)
                await event.edit("Reklama foydalanuvchilarga yuborildi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]

async def save_media(state, media_type):
    media = {
        "name": state["name"],
        "post_url": state["post_url"],
        "code": state["code"]
    }
    media_data[media_type][state["code"]] = media

async def search_media_by_code(event, state):
    code = event.text
    media = media_data[state["type"]].get(code)
    
    if media:
        post_url = media["post_url"]
        channel_id = MOVIE_CHANNEL_ID if state["type"] == "movie" else SERIAL_CHANNEL_ID if state["type"] == "serial" else MULTFILM_CHANNEL_ID
        try:
            post_id = int(post_url.split('/')[-1])
            message = await bot.get_messages(channel_id, ids=post_id)
            await bot.send_message(event.sender_id, message, buttons=[[Button.text('/start')]])
        except Exception as e:
            await event.respond(f"{state['type'].capitalize()} topilmadi yoki postni yuborishda xatolik yuz berdi.", buttons=[[Button.text('/start')]])
    else:
        await event.respond(f"{state['type'].capitalize()} topilmadi.", buttons=[[Button.text('/start')]])
    del user_states[event.sender_id]

async def delete_media(event, media_type):
    code = event.text
    if code in media_data[media_type]:
        del media_data[media_type][code]
        await event.respond(f"{media_type.capitalize()} o'chirildi.", buttons=[[Button.text('/start')]])
    else:
        await event.respond(f"{media_type.capitalize()} topilmadi.", buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Admin Panel"))
async def admin_panel(event):
    if event.sender_id in ADMINS:
        buttons = [
            [Button.text("Kino qo'shish"), Button.text("Serial qo'shish")],
            [Button.text("Multfilm qo'shish")],
            [Button.text("Kino o'chirish")],
            [Button.text("Serial o'chirish"), Button.text("Multfilm o'chirish")],
            [Button.text("Kino linkini o'zgartirish")],
            [Button.text("Serial linkini o'zgartirish")],
            [Button.text("Multfilm linkini o'zgartirish")],
            [Button.text("Majburiy kanal qo'shish"), Button.text("Majburiy kanal o'chirish")],
            [Button.text("Admin qo'shish"), Button.text("Admin o'chirish")],
            [Button.text("Reklama yuborish"), Button.text("Orqaga qaytish")]
        ]
        await event.respond('Admin Paneli:', buttons=buttons)
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Kino qo'shish"))
async def add_movie(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_movie_name", "type": "movie"}
        await event.respond("Kino nomini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Serial qo'shish"))
async def add_serial(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_serial_name", "type": "serial"}
        await event.respond("Serial nomini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Multfilm qo'shish"))
async def add_multfilm(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_multfilm_name", "type": "multfilm"}
        await event.respond("Multfilm nomini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Kino o'chirish"))
async def delete_movie(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_code_delete", "type": "movie"}
        await event.respond("O'chirilishi kerak bo'lgan kino kodini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Serial o'chirish"))
async def delete_serial(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_code_delete", "type": "serial"}
        await event.respond("O'chirilishi kerak bo'lgan serial kodini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Multfilm o'chirish"))
async def delete_multfilm(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_code_delete", "type": "multfilm"}
        await event.respond("O'chirilishi kerak bo'lgan multfilm kodini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Kino linkini o'zgartirish"))
async def change_movie_link(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_movie_link"}
        await event.respond("Yangi kino kanal linkini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Serial linkini o'zgartirish"))
async def change_serial_link(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_serial_link"}
        await event.respond("Yangi serial kanal linkini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Multfilm linkini o'zgartirish"))
async def change_multfilm_link(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_multfilm_link"}
        await event.respond("Yangi multfilm kanal linkini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Admin qo'shish"))
async def add_admin(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_admin_add"}
        await event.respond("Yangi admin ID sini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Admin o'chirish"))
async def remove_admin(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_admin_remove"}
        await event.respond("O'chirilishi kerak bo'lgan admin ID sini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Majburiy kanal qo'shish"))
async def add_mandatory_channel(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_mandatory_channel_link"}
        await event.respond("Qo'shilishi kerak bo'lgan kanal linkini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Majburiy kanal o'chirish"))
async def remove_mandatory_channel(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_mandatory_channel_remove"}
        await event.respond("O'chirilishi kerak bo'lgan kanal ID sini kiriting:", buttons=[[Button.text("Bekor qilish")]])
    else:
        await event.respond('Sizda bu buyruqni ishlatish uchun huquq yo\'q.', buttons=[[Button.text('/start')]])

@bot.on(events.NewMessage(pattern="Kino qidirish"))
async def search_movie(event):
    if not await check_subscription(event):
        return
    
    user_states[event.sender_id] = {"state": "awaiting_code_search", "type": "movie"}
    buttons = [[Button.text("Bekor qilish")]]
    await event.respond("Kino kodini kiriting:", buttons=buttons)

@bot.on(events.NewMessage(pattern="Serial / Drama qidirish"))
async def search_serial(event):
    if not await check_subscription(event):
        return
    
    user_states[event.sender_id] = {"state": "awaiting_code_search", "type": "serial"}
    buttons = [[Button.text("Bekor qilish")]]
    await event.respond("Serial kodini kiriting:", buttons=buttons)

@bot.on(events.NewMessage(pattern="Multfilim qidirish"))
async def search_multfilm(event):
    if not await check_subscription(event):
        return
    
    user_states[event.sender_id] = {"state": "awaiting_code_search", "type": "multfilm"}
    buttons = [[Button.text("Bekor qilish")]]
    await event.respond("Multfilm kodini kiriting:", buttons=buttons)

@bot.on(events.NewMessage(pattern="Filimlar royxati"))
async def list_media_options(event):
    if not await check_subscription(event):
        return
    
    buttons = [
        [Button.text("Kinolar"), Button.text("Seriallar")],
        [Button.text("Multfilmlar")],
        [Button.text("Orqaga qaytish")]
    ]
    await event.respond('Qaysi turdagi filimlarni ko\'rmoqchisiz?', buttons=buttons)

@bot.on(events.NewMessage(pattern="Kinolar"))
async def list_movies(event):
    buttons = [[Button.url("Kanalga o'tish", links["movies"])]]
    await event.respond("Kinolarni ko'rish uchun kanalga o'ting:", buttons=buttons)

@bot.on(events.NewMessage(pattern="Seriallar"))
async def list_serials(event):
    buttons = [[Button.url("Kanalga o'tish", links["serials"])]]
    await event.respond("Seriallarni ko'rish uchun kanalga o'ting:", buttons=buttons)

@bot.on(events.NewMessage(pattern="Multfilmlar"))
async def list_multfilms(event):
    buttons = [[Button.url("Kanalga o'tish", links["multfilms"])]]
    await event.respond("Multfilmlarni ko'rish uchun kanalga o'ting:", buttons=buttons)

@bot.on(events.NewMessage)
async def group_reply_handler(event):
    if event.is_reply and event.chat_id == GROUP_ID:
        original_msg = await event.get_reply_message()
        if original_msg.id in user_messages:
            user_id = user_messages[original_msg.id]
            await bot.send_message(user_id, f'Admin javobi:\n\n{event.text}')

@bot.on(events.NewMessage)
async def add_user_to_list(event):
    user_ids.add(event.sender_id)

@bot.on(events.NewMessage(pattern="Reklama yuborish"))
async def request_advertisement(event):
    if event.sender_id in ADMINS:
        user_states[event.sender_id] = {"state": "awaiting_ad_content"}
        await event.respond("Reklama uchun matn va media fayl yuboring:", buttons=[[Button.text("Bekor qilish")]])

@bot.on(events.NewMessage)
async def handle_advertisement_content(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]
        if state.get("state") == "awaiting_ad_content":
            if event.media:
                user_states[user_id] = {
                    "state": "awaiting_ad_confirmation",
                    "ad_message": event.text,
                    "ad_media": event.media
                }
                buttons = [
                    [Button.inline("Ha, tasdiqlayman", b"confirm_ad"), Button.inline("Yo'q, bekor qilish", b"cancel_ad")]
                ]
                await event.respond(f'Reklamani yuborishni tasdiqlaysizmi?\n\n{event.text}', buttons=buttons)
            else:
                await event.respond("Iltimos, reklama bilan birga media fayl jo'nating.", buttons=[[Button.text("Bekor qilish")]])

@bot.on(events.CallbackQuery)
async def handle_ad_confirmation(event):
    user_id = event.sender_id
    if user_id in user_states:
        state = user_states[user_id]
        if state.get("state") == "awaiting_ad_confirmation":
            if event.data == b"confirm_ad":
                ad_message = state["ad_message"]
                ad_media = state.get("ad_media")
                for user in user_ids:
                    if ad_media:
                        await bot.send_file(user, ad_media, caption=ad_message)
                    else:
                        await bot.send_message(user, ad_message)
                await event.edit("Reklama foydalanuvchilarga yuborildi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
            elif event.data == b"cancel_ad":
                await event.edit("Reklama bekor qilindi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]
            elif event.data == b"confirm_ad_no_media":
                ad_message = state["ad_message"]
                for user in user_ids:
                    await bot.send_message(user, ad_message)
                await event.edit("Reklama foydalanuvchilarga yuborildi.", buttons=[[Button.text('/start')]])
                del user_states[user_id]

bot.run_until_disconnected()
