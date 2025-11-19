from telegram.ext import Updater, MessageHandler, Filters
import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
API_URL = "https://giet-marks-api.onrender.com/get_marks"

def handle_message(update, context):
    roll_no = update.message.text.strip()

    update.message.reply_text("Fetching your data...")

    r = requests.post(API_URL, json={"roll_no": roll_no})
    data = r.json()

    if "error" in data:
        update.message.reply_text(f"Error: {data['error']}")
        return

    msg = f"Results for {data['roll_no']}:\n\n"

    for exam in data["exams"]:
        msg += f"📘 {exam['exam_name']}\n"
        msg += f"Total: {exam['total_mark']}\n"
        msg += f"Secured: {exam['secured_mark']}\n\n"

        msg += "Subject-wise:\n"
        for sub in exam["subject_details"]:
            msg += f"- {sub['vchSubjectShortName']}: {sub['decMarkSecured']} / {sub['decTotalMark']}\n"

        msg += "\n---------------------\n\n"

    update.message.reply_text(msg)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
