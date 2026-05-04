import requests
import time
import os
from flask import Flask, jsonify, request, render_template, Response, session, url_for
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "erp_ultra_secure_key_99"

BASE_URL = "https://gietuerp.in"
erp_sessions = {}

def get_erp_session():
    if 'user_key' not in session:
        session['user_key'] = str(time.time())
    user_key = session['user_key']
    if user_key not in erp_sessions:
        erp_sessions[user_key] = requests.Session()
    return erp_sessions[user_key]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/captcha_image')
def captcha_image():
    s = get_erp_session()
    # Adding a timestamp to prevent browser caching
    img_res = s.get(f"{BASE_URL}/get-captcha-image?t={int(time.time())}", stream=True)
    return Response(img_res.content, mimetype='image/png')

@app.route('/login', methods=['POST'])
def login():
    s = get_erp_session()
    captcha_code = request.form.get('captcha')
    
    # STAGE 1: Get fresh Antiforgery Token from the login page
    # This ensures the session has the initial .AspNetCore.Antiforgery cookie
    login_page = s.get(f"{BASE_URL}/")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    token_element = soup.find('input', attrs={'name': '__RequestVerificationToken'})
    if not token_element:
        return jsonify({"status": "error", "message": "Could not find Verification Token."})
    
    token = token_element['value']
    
    # STAGE 2: Perform Login
    payload = {
        "vchUserName": "24CSEAIML015",
        "vchPassword": "rr943766",
        "CaptchaCode": captcha_code,
        "__RequestVerificationToken": token
    }
    
    headers = {
        'Referer': f"{BASE_URL}/",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # allow_redirects=True is mandatory to catch the UserLoginCookie during the 302 hop
    res = s.post(f"{BASE_URL}/", data=payload, headers=headers, allow_redirects=True)
    
    # STAGE 3: Final Verification & Cookie Storage
    current_cookies = s.cookies.get_dict()
    has_auth = 'UserLoginCookie' in current_cookies
    
    # We verify success by checking the URL and the presence of the Auth cookie
    if "Login" not in res.url and has_auth:
        # Save to file
        with open('cookies.txt', 'w') as f:
            for key, value in current_cookies.items():
                f.write(f"{key}={value}\n")
        
        return jsonify({
            "status": "success",
            "message": "Logged in successfully!",
            "cookies_found": list(current_cookies.keys()),
            "count": len(current_cookies)
        })
    else:
        # Provide specific debugging info in the response
        error_msg = "Invalid Captcha" if "Login" in res.url else "Login failed: Auth cookie not issued."
        return jsonify({
            "status": "error", 
            "message": error_msg,
            "captured_so_far": list(current_cookies.keys())
        })

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# --- TEST6(ALL DATA).PY LOGIC ---

def get_cookies_from_file():
    cookies = {}
    try:
        with open('cookies.txt', 'r') as f:
            content = f.read().strip().split('\n')
            for line in content:
                if '=' in line:
                    key, value = line.split('=', 1)
                    cookies[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Error: cookies.txt not found.")
    return cookies

def fetch_student_data(student_id):
    cookies = get_cookies_from_file()
    ts = int(time.time() * 1000)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/UserProfile/PersonalInfo'
    }

    session = requests.Session()
    session.cookies.update(cookies)

    # STAGE 1: Fetch Summary
    summary_url = f"{BASE_URL}/UserProfile/ProfileSummaryView?id={student_id}&id2=2&_ts={ts}"
    summary_res = session.get(summary_url, headers=headers)
    
    academic_info = {}
    if summary_res.status_code == 200:
        s_soup = BeautifulSoup(summary_res.text, 'html.parser')
        name_el = s_soup.select_one('.profile-username')
        
        def get_summary_val(label_text):
            b_tag = s_soup.find('b', string=lambda s: s and label_text in s)
            if b_tag:
                val_tag = b_tag.find_next_sibling('a', class_='float-right')
                return val_tag.get_text(strip=True) if val_tag else "---"
            return "---"

        academic_info = {            
            "student_id": student_id,
            "name": name_el.get_text(strip=True) if name_el else "Unknown", 
            "roll_number": get_summary_val("Roll Number"),
            "registration_number": get_summary_val("Registration Number"),
            "program": get_summary_val("Program"),
            "branch": get_summary_val("Branch"),
            "semester": get_summary_val("Semester"),
            "section": get_summary_val("Section"),
            "admission_type": get_summary_val("Admission Type")
        }

    # STAGE 2: Fetch Personal Details
    personal_url = f"{BASE_URL}/UserProfile/PersonalInfoView?id={student_id}&id2=2&_ts={ts}"
    personal_res = session.get(personal_url, headers=headers)
    
    if personal_res.status_code != 200:
        return {"error": f"Failed to fetch. Status: {personal_res.status_code}"}

    soup = BeautifulSoup(personal_res.text, 'html.parser')

    def get_val(element_id):
        # 1. Find the element by ID or Name
        el = soup.find(id=element_id) or soup.find(attrs={"name": element_id})
        
        if not el:
            return "---"

        # 2. Dropdown Logic: Find the specifically 'selected' option
        if el.name == 'select':
            selected_option = el.find('option', selected=True)
            # If something is selected and it's not the placeholder "Select", return it
            if selected_option and selected_option.text.strip().lower() != "select":
                return selected_option.text.strip()
            return "---"

        # 3. Input/Textarea Logic: Get the 'value' attribute or text content
        val = el.get('value') or el.get_text() or ""
        
        # Clean up and return
        clean_val = val.strip()
        return clean_val if clean_val and clean_val.lower() != "select" else "---"

    return { # Extracted from summary_url
        "academic_info": academic_info,
        "personal_details": {
            "Father's Name": get_val("vchFathersName"),
            "Mother's Name": get_val("vchMothersName"),
            "Aadhar Number": get_val('vchAdharNo'),
            "PAN Number": get_val("vchPanCardNo"),
            "Date of Birth": get_val("dtmDateOfBirth"),
            "Gender": get_val("vchGender"),
            "Blood Group": get_val("vchBloodGroup"),
            "Nationality": get_val("vchNationality"),
            "Religion": get_val("vchReligion"),
            "Marital Status": get_val("vchMaritalStatus")
        },
        "contact_info": {
            "Personal Phone": get_val("vchContactNo"),
            "Official Phone": get_val("vchOfficialTelephoneNo"),
            "Personal Email": get_val("vchPersonalEmail"),
            "Official Email": get_val("vchOfficialEmail")
        },
        "address": {
            "city": get_val("vchPermCity"),
            "state": get_val("vchPermState"),
            "full_address": get_val("vchCorrpAddress1"),
            "Perm. Pin": get_val("vchPermPinCode"),
            "Corr. City": get_val("vchCorrpCity"),
            "Corr. Dist": get_val("vchCorrpDistrict"),
            "Corr. State": get_val("vchCorrpState"),
        }
    }

@app.route('/get_profile/<student_id>')
def get_profile(student_id):
    try:
        data = fetch_student_data(student_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)