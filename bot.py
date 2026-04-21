import asyncio
import random
import schedule
import time
import threading
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "0"))

TEST_VAQTLARI = ["09:00", "13:00", "18:00"]

def lugat_yukla(fayl_nomi="Lugat.txt"):
    lugat = {}
    try:
        with open(fayl_nomi, "r", encoding="utf-8") as f:
            for qator in f:
                qator = qator.strip()
                if " — " in qator:
                    soz, tarjima = qator.split(" — ", 1)
                    lugat[soz.strip()] = tarjima.strip()
                elif " - " in qator:
                    soz, tarjima = qator.split(" - ", 1)
                    lugat[soz.strip()] = tarjima.strip()
    except FileNotFoundError:
        print(f"Fayl topilmadi: {fayl_nomi}")
    return lugat

def test_yarat(lugat):
    if len(lugat) < 4:
        return None
    sozlar = list(lugat.keys())
    yonalish = random.choice(["soz_tarjima", "tarjima_soz"])
    togri_soz = random.choice(sozlar)
    togri_tarjima = lugat[togri_soz]
    notogri = random.sample([s for s in sozlar if s != togri_soz], 3)
    if yonalish == "soz_tarjima":
        savol = f"📝 '{togri_soz}' so'zining tarjimasi nima?"
        togri_javob = togri_tarjima
        variantlar = [lugat[s] for s in notogri]
    else:
        savol = f"🔄 '{togri_tarjima}' tarjimasining asl so'zi nima?"
        togri_javob = togri_soz
        variantlar = notogri
    variantlar.append(togri_javob)
    random.shuffle(variantlar)
    return {"savol": savol, "variantlar": variantlar, "togri_index": variantlar.index(togri_javob)}

app_global = None

async def auto_test_yuborish():
    global app_global
    if not app_global:
        return
    lugat = app_global.bot_data.get("lugat", {})
    test = test_yarat(lugat)
    if not test:
        return
    await app_global.bot.send_poll(
        chat_id=GROUP_CHAT_ID,
        question=test["savol"],
        options=test["variantlar"],
        type="quiz",
        correct_option_id=test["togri_index"],
        is_anonymous=False,
        open_period=60
    )
    print(f"Test yuborildi!")

def scheduler_thread():
    def job():
        asyncio.run(auto_test_yuborish())
    for vaqt in TEST_VAQTLARI:
        schedule.every().day.at(vaqt).do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n/test — test olish\n/lugat — so'zlar soni\n/guruh — guruhga yuborish"
    )

async def test_yuborish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lugat = context.bot_data.get("lugat", {})
    test = test_yarat(lugat)
    if not test:
        await update.message.reply_text("⚠️ Kamida 4 ta so'z kerak!")
        return
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=test["savol"],
        options=test["variantlar"],
        type="quiz",
        correct_option_id=test["togri_index"],
        is_anonymous=False,
        open_period=60
    )

async def lugat_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lugat = context.bot_data.get("lugat", {})
    await update.message.reply_text(f"📚 Jami: {len(lugat)} ta so'z")

async def guruhga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_test_yuborish()
    await update.message.reply_text("✅ Guruhga yuborildi!")

async def post_init(application):
    global app_global
    app_global = application
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()

def main():
    global app_global
    lugat = lugat_yukla()
    print(f"{len(lugat)} ta so'z yuklandi")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.bot_data["lugat"] = lugat
    app_global = app
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_yuborish))
    app.add_handler(CommandHandler("lugat", lugat_info))
    app.add_handler(CommandHandler("guruh", guruhga))
    app.run_polling()

if __name__ == "__main__":
    main()
