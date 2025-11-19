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
    print("UPDATE RECEIVED:", update)  # DEBUG

    if "message" not in update:
        print("No message field")
        return "ok"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    print("User sent:", text)  # DEBUG

    if text.startswith("24"):
        marks = get_marks(text)
        print("Marks returned:", marks)  # DEBUG

        if marks is None:
            send_message(chat_id, "❌ Invalid roll number or no exam data.")
        else:
            formatted = format_marks(marks)
            send_message(chat_id, formatted)
    else:
        send_message(chat_id, "Send your roll number (e.g., 24CSEAIML015).")

    return "ok"


@app.get("/check")
def check_roll():
    roll_no = request.args.get("roll")

    if not roll_no:
        return "❌ Please provide ?roll=ROLLNUMBER", 400

    marks = get_marks(roll_no)

    if marks is None:
        return "❌ No exam data found for this roll number", 404

    return marks



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
    print("Fetching marks for:", roll_no)

    url1 = "https://gietuerp.in/ExamReport/GetAllScheduledExamForStudents"
    payload1 = {
        "filterForStudentExamReport": {
            "intSemester": -1,
            "vchRollNo": roll_no,
            "intExamTypeID": 0
        }
    }

    try:
        res1 = requests.post(url1, json=payload1)
        print("First API status:", res1.status_code)
        print("First API response:", res1.text)

        data1 = res1.json()
    except Exception as e:
        print("Error calling first API:", e)
        return None

    if "data" not in data1 or len(data1["data"]) == 0:
        print("No exam schedule data found.")
        return None

    student_id = data1["data"][0]["intStudentID"]
    schedule_ids = [item["intExamScheduleMasterID"] for item in data1["data"]]

    print("Student ID:", student_id)
    print("Schedule IDs:", schedule_ids)

    all_marks = []
    url2 = "https://gietuerp.in/ExamReport/GetAllSubjectMarksForStudents"

    for sid in schedule_ids:
        payload2 = {"intExamScheduleMasterID": sid, "intStudentID": student_id}

        try:
            res2 = requests.post(url2, json=payload2)
            print(f"Second API {sid} status:", res2.status_code)
            print(f"Second API {sid} response:", res2.text)
            marks_data = res2.json()
        except Exception as e:
            print("Error calling second API:", e)
            continue

        all_marks.append({
            "examID": sid,
            "data": marks_data.get("data", [])
        })

    return all_marks

from flask import Flask, request, jsonify


@app.get("/fetch")
def fetch_marks():
    roll = request.args.get("roll")
    if not roll:
        return jsonify({"error": "Roll number required"}), 400

    # Step 1 → Get exam schedule
    try:
        payload1 = {
            "filterForStudentExamReport": {
                "intSemester": -1,
                "vchRollNo": roll,
                "intExamTypeID": 0
            }
        }
        r1 = requests.post("https://gietuerp.in/ExamReport/GetAllScheduledExamForStudents", json=payload1)
        schedule_data = r1.json()

        if not schedule_data.get("data"):
            return jsonify({"error": "No exam schedule found"}), 404

        student_id = schedule_data["data"][0]["intStudentID"]
        schedule_ids = [x["intExamScheduleMasterID"] for x in schedule_data["data"]]

        all_marks = []

        # Step 2 → Loop through all schedule IDs
        for sid in schedule_ids:
            payload2 = {
                "intExamScheduleMasterID": sid,
                "intStudentID": student_id
            }
            r2 = requests.post("https://gietuerp.in/ExamReport/GetAllSubjectMarksForStudents", json=payload2)
            marks = r2.json()

            all_marks.append({
                "examID": sid,
                "marks": marks.get("data", [])
            })

        return jsonify({
            "roll": roll,
            "studentID": student_id,
            "examCount": len(all_marks),
            "marksReport": all_marks
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run()
