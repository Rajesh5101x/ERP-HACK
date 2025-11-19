from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "8318500164:AAE6yAiCh6IJSiBC45GjH5L_LJBin2JhoYQ"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.get("/")
def home():
    return "Server Alive", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        # If user sends roll number
        if text.startswith("24"):
            marks = get_marks(text)

            if marks is None:
                send_message(chat_id, "Invalid roll number or no exam data found.")
            else:
                formatted = format_marks(marks)
                send_message(chat_id, formatted)

        else:
            send_message(chat_id, "Send your roll number (e.g., 24CSEAIML015).")

    return "ok"


def format_marks(all_marks):
    output = "📘 *Exam Marks Report*\n\n"
    for exam in all_marks:
        output += f"📌 *Exam ID:* {exam['examID']}\n"
        for sub in exam["data"]:
            output += f"- {sub['vchSubjectName']}: {sub['decMarksObtained']}/{sub['decTotalMarks']}\n"
        output += "\n"
    return output


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)



import requests

def get_marks(roll_no):
    # STEP 1: First API call
    url1 = "https://gietuerp.in/ExamReport/GetAllScheduledExamForStudents"
    payload1 = {
        "filterForStudentExamReport": {
            "intSemester": -1,
            "vchRollNo": roll_no,
            "intExamTypeID": 0
        }
    }

    res1 = requests.post(url1, json=payload1)
    data1 = res1.json()

    if "data" not in data1 or len(data1["data"]) == 0:
        return None

    student_id = data1["data"][0]["intStudentID"]
    schedule_ids = [item["intExamScheduleMasterID"] for item in data1["data"]]

    all_marks = []

    # STEP 2: Loop through all schedule IDs
    url2 = "https://gietuerp.in/ExamReport/GetAllSubjectMarksForStudents"

    for sid in schedule_ids:
        payload2 = {
            "intExamScheduleMasterID": sid,
            "intStudentID": student_id
        }
        res2 = requests.post(url2, json=payload2)
        marks_data = res2.json()

        all_marks.append({
            "examID": sid,
            "data": marks_data.get("data", [])
        })

    return all_marks


if __name__ == "__main__":
    app.run()
