from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://gietuerp.in/ExamReport"

# -------------------------------
# Helper: call scheduled exams API
# -------------------------------
def fetch_scheduled_exams(roll_no):
    payload = {
        "filterForStudentExamReport": {
            "intSemester": -1,
            "vchRollNo": roll_no,
            "intExamTypeID": 0
        }
    }

    r = requests.post(f"{BASE_URL}/GetAllScheduledExamForStudents", json=payload)
    return r.json()


# -------------------------------------
# Helper: call subject marks API per exam
# -------------------------------------
def fetch_subject_marks(schedule_id, student_id):
    payload = {
        "intExamScheduleMasterID": schedule_id,
        "intStudentID": student_id
    }

    r = requests.post(f"{BASE_URL}/GetAllSubjectMarksForStudents", json=payload)
    return r.json()


# -------------------------------------
# API Endpoint called by Telegram Bot
# -------------------------------------
@app.route("/get_marks", methods=["POST"])
def get_marks():
    data = request.json
    roll_no = data.get("roll_no")

    if not roll_no:
        return jsonify({"error": "Roll number missing"}), 400

    # Step 1: Get scheduled exams
    scheduled = fetch_scheduled_exams(roll_no)

    if "data" not in scheduled or len(scheduled["data"]) == 0:
        return jsonify({"error": "No data returned for this roll number"}), 404

    exams = scheduled["data"]
    student_id = exams[0]["intStudentID"]

    result = []

    # Step 2: Loop over exam schedule IDs
    for exam in exams:
        exam_id = exam["intExamScheduleMasterID"]

        subject_data = fetch_subject_marks(exam_id, student_id)

        result.append({
            "exam_id": exam_id,
            "exam_name": exam["vchExamName"],
            "total_mark": exam["decTotalMark"],
            "secured_mark": exam["decMarkSecured"],
            "subject_details": subject_data.get("data", [])
        })

    return jsonify({"roll_no": roll_no, "exams": result})


@app.route("/")
def home():
    return "GIET ERP API Bridge Running"
