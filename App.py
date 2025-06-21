from flask import Flask, render_template, jsonify, request
import threading
import serial
from openpyxl import Workbook
from datetime import datetime, time, date, timedelta
import random
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# --- Configuration and Global Variables ---

SERIAL_PORT = 'COM7'
BAUD_RATE = 9600

ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Serial port {SERIAL_PORT} opened successfully.")
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    print("Please check if the serial port is correct and not in use. Running in simulation mode.")
    ser = None

# Path for storing settings and registered users data
SETTINGS_FILE = 'settings.json' 
REGISTERED_USERS_FILE = 'registered_users.json' 
# ATTENDANCE_RECORDS_FILE = 'attendance_records.json' # Removed attendance records file

all_attendance_records = {} # This will now store only today's attendance
all_registered_students = {}

settings = {
    'checkInStart': '09:00',
    'checkInEnd': '10:00',
    'workDays': {
        'monday': True, 'tuesday': True, 'wednesday': True, 'thursday': True, 'friday': True,
        'saturday': False, 'sunday': False
    },
    'notifyLateArrivals': True,
    'notifyAbsences': True,
    'emailSummary': True,
    'notificationEmail': 'sivananthan46m@gmail.com',
    'comPort': SERIAL_PORT,
    'baudRate': BAUD_RATE
}

clients = set()

rfid_scan_event = threading.Event()
last_scanned_rfid = None

# Variable to keep track of the last day for which attendance was processed
last_attendance_date = None

# --- Helper Functions for Data Persistence ---

def load_settings_from_file():
    """Loads settings from a JSON file."""
    global settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                loaded_settings = json.load(f)
                for key, value in loaded_settings.items():
                    if key in settings:
                        settings[key] = value
                print("Settings loaded successfully.")
            except json.JSONDecodeError:
                print("Error decoding settings file. Using default settings.")
    
    settings['CHECK_IN_START_TIME_OBJ'] = datetime.strptime(settings['checkInStart'], '%H:%M').time()
    settings['CHECK_IN_END_TIME_OBJ'] = datetime.strptime(settings['checkInEnd'], '%H:%M').time()

def save_settings_to_file():
    """Saves current settings to a JSON file."""
    serializable_settings = settings.copy()
    if 'CHECK_IN_START_TIME_OBJ' in serializable_settings:
        del serializable_settings['CHECK_IN_START_TIME_OBJ']
    if 'CHECK_IN_END_TIME_OBJ' in serializable_settings:
        del serializable_settings['CHECK_IN_END_TIME_OBJ']

    with open(SETTINGS_FILE, 'w') as f:
        json.dump(serializable_settings, f, indent=4)
    print("Settings saved successfully.")

def load_registered_users_from_file():
    """Loads registered users from a JSON file."""
    global all_registered_students
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, 'r') as f:
            try:
                all_registered_students = json.load(f)
                print("Registered users loaded successfully.")
            except json.JSONDecodeError:
                print("Error decoding registered users file. Starting with empty users.")
    
def save_registered_users_to_file():
    """Saves current registered users to a JSON file."""
    with open(REGISTERED_USERS_FILE, 'w') as f:
        json.dump(all_registered_students, f, indent=4)
    print("Registered users saved successfully.")

# Removed load_attendance_records_from_file and save_attendance_records_to_file

# Load data on startup
load_settings_from_file()

# Ensure registered_users.json is populated at startup
try:
    with open(REGISTERED_USERS_FILE, 'w') as f:
        json.dump({
            "0x282A2279": {
                "name": "Bhuvanesh",
                "email": "bhuvaneshmani66@gmail.com",
                "department": "Quality Analyst"
            },
            "0x370DDF73": {
                "name": "Sivanathan M",
                "email": "21sivacse096@dhaanishcollege.in",
                "department": "Tester"
            },
            "0xCB559ACB": {
                "name": "Lokesh",
                "email": "Lokeshvpl40@gmail.com.com",
                "department": "Service Now"
            },
            "0x83E02D8D": {
                "name": "DineshKumar K",
                "email": "dineshkumar2k4@gmail.com",
                "department": "Infrastructure Management"
            },
            "0x5DFA1E12": {
                "name": "Swetha V",
                "email": "swethav@gmail.com",
                "department": "Infrastructure Management"
            },
            "0x41D3F2A5": {
                "name": "Swetha K",
                "email": "swethak@gmail.com",
                "department": "Tech Support"
            },
            "0x9E48A95E": {
                "name": "Abidass",
                "email": "abidass@gmail.com",
                "department": "Tester"
            },
            "0x125D7C57": {
                "name": "Ramya R",
                "email": "ramyar@gmail.com",
                "department": "Tech Support"
            },
            "0xAFBD7A04": {
                "name": "Shyam S",
                "email": "shyam@gmail.com",
                "department": "Software Developer"
            },
            "0xB171B655": {
                "name": "Sibiraj E",
                "email": "sibiraj@gmail.com",
                "department": "Service Now"
            },
            "0x5356E04B": {
                "name": "Rageshwari",
                "email": "Rageshwari@gmail.com",
                "department": "Software Developer"
            },
            "0x377D81A9": {
                "name": "Saranya s",
                "email": "saranya@gamil.com",
                "department": "Infrastructure"
            },
            "0x66D0D397": {
                "name": "Saranya SR",
                "email": "saranayasr@gmail.com.com",
                "department": "Software Developer"
            },
            "0x1CD34440": {
                "name": "Selvam",
                "email": "selvam@gmail.com",
                "department": "HR"
            },
            "0xA0CEB9C2": {
                "name": "kavi",
                "email": "kavi@gmail.com",
                "department": "HR"
            },
            "0x49F05523": {
                "name": "Srikanth",
                "email": "srikanth@gmail.com",
                "department": "Infrastructure Management"
            },
            "0x55D4D4B2": {
                "name": "Jayaprakesh",
                "email": "jayaprakesh@gmail.com",
                "department": "Web Developer"
            },
            "0xA9B63B68": {
                "name": "Bharath T",
                "email": "bharath@gmail.com",
                "department": "Service Now"
            },
            "0xD4D821B7": {
                "name": "Madhu R",
                "email": "madhu@gmail.com",
                "department": "Web Developer"
            },
            "0xC0037B": {
                "name": "AHILESH K",
                "email": "21sivacse096@dhaanishcollege.in",
                "department": "HR"
            }
        }, f, indent=4)
    print("Registered users file created/updated with provided data.")
    load_registered_users_from_file()
except Exception as e:
    print(f"Error initializing registered users file: {e}")

# --- RFID Reading and Processing ---

def get_student_info(uid):
    """Returns student name, email, and department based on UID."""
    info = all_registered_students.get(uid)
    if info:
        return info['name'], info['email'], info['department']
    return None, None, None

def broadcast_message(message):
    """Sends a message to all connected WebSocket clients."""
    for client in list(clients):
        try:
            client.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to WebSocket client: {e}")
            clients.remove(client)

def process_rfid_tap(tapped_uid, now=None):
    """Processes an RFID tap, updating attendance records and broadcasting status."""
    global all_attendance_records
    if now is None:
        now = datetime.now()
    
    today_date = now.date()

    if not all_registered_students:
        print(f"RFID {tapped_uid} tapped, but no users are registered. Cannot process attendance.")
        broadcast_message({'type': 'no_registered_users', 'uid': tapped_uid})
        return

    uid_to_process = random.choice(list(all_registered_students.keys()))
    name, email, department = get_student_info(uid_to_process)
    print(f"Processing attendance for random user {uid_to_process} ({name}) triggered by {tapped_uid})")

    # The structure of all_attendance_records will be:
    # {uid: {'name': ..., 'email': ..., 'date': ..., 'department': ..., 'first_tap': ..., 'last_tap': ..., 'status': ..., 'work_hours': ...}}
    # We are no longer nesting by date for daily records as it's cleared daily.
    
    current_day_record = all_attendance_records.get(uid_to_process)

    status = 'Present'
    if now.time() > settings['CHECK_IN_END_TIME_OBJ']:
        status = 'Late'
    elif now.time() < settings['CHECK_IN_START_TIME_OBJ']:
        status = 'Early'

    if current_day_record is None:
        all_attendance_records[uid_to_process] = {
            'name': name,
            'email': email,
            'date': today_date,
            'department': department,
            'first_tap': now,
            'last_tap': now,
            'status': status,
            'work_hours': '00:00'
        }
        print(f"Logged: {uid_to_process} ({name}) - First Tap at {now.strftime('%H:%M:%S')}, Status: {status} (Triggered by {tapped_uid})")
    else:
        current_day_record['last_tap'] = now
        
        time_diff = now - current_day_record['first_tap']
        
        if time_diff.total_seconds() < 0:
            time_diff = timedelta(0)

        total_seconds = time_diff.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        current_day_record['work_hours'] = f"{hours:02d}:{minutes:02d}"
        print(f"Logged: {uid_to_process} ({name}) - Re-tap at {now.strftime('%H:%M:%S')}, Work Hours: {current_day_record['work_hours']} (Triggered by {tapped_uid})")
    
    # save_attendance_records_to_file() # Removed saving to file

    broadcast_message({'type': 'rfid_tap', 'uid': uid_to_process})

def read_serial_and_process():
    """Reads from serial port and processes RFID taps."""
    global last_scanned_rfid
    while True:
        if ser:
            try:
                line = ser.readline().decode().strip()
                if line:
                    uid = line.upper()
                    print(f"Serial read: {uid}")
                    if rfid_scan_event.is_set():
                        last_scanned_rfid = uid
                        rfid_scan_event.clear()
                        broadcast_message({'type': 'new_user_rfid_scan', 'uid': uid})
                    else:
                        process_rfid_tap(uid)
            except Exception as e:
                print("Serial read error:", e)
        else:
            pass
        
        threading.Event().wait(0.1)

def simulate_rfid_tap_for_new_user():
    """Simulates a single new RFID for user registration."""
    mock_uid = '0x' + ''.join(random.choices('0123456789ABCDEF', k=8))
    print(f"Simulating new user RFID for registration: {mock_uid}")
    return mock_uid

@app.route('/')
def index():
    return render_template('indexx.html')

@app.route('/summary')
def get_attendance_summary():
    global all_attendance_records, last_attendance_date

    today = datetime.now().date()

    # Clear records if it's a new day
    if last_attendance_date is None or last_attendance_date != today:
        print(f"New day detected ({today}). Clearing all attendance records.")
        all_attendance_records = {}
        last_attendance_date = today

    present_count = 0
    late_count = 0
    absent_count = 0
    
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    filtered_records_for_display = {}
    
    if start_date_str and end_date_str:
        # If date range is provided, treat all_attendance_records as a historical view for this request
        # This part will essentially show nothing if attendance isn't saved.
        # For this specific requirement, only 'today's' data will be available.
        # If the user picks a past date range, it will show empty.
        requested_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        requested_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if requested_start_date <= today <= requested_end_date:
            filtered_records_for_display = all_attendance_records.copy()
        else:
            filtered_records_for_display = {} # No records for past/future dates if not stored
    else:
        # Default to today's attendance
        filtered_records_for_display = all_attendance_records.copy()
        
        current_weekday = datetime.now().strftime('%A').lower()
        if settings['workDays'].get(current_weekday, False) and datetime.now().time() > settings['CHECK_IN_END_TIME_OBJ']:
            for registered_uid in all_registered_students.keys():
                if registered_uid not in filtered_records_for_display:
                    name, email, department = get_student_info(registered_uid)
                    filtered_records_for_display[registered_uid] = {
                        'name': name,
                        'email': email,
                        'date': today,
                        'department': department,
                        'first_tap': None,
                        'last_tap': None,
                        'status': 'Absent',
                        'work_hours': '00:00'
                    }

    detail_list = []
    
    # The counts should reflect all students for today, not just those who tapped
    processed_uids_for_counts = set() 

    # Determine who is absent among registered users for today if it's a workday and after check-in end time
    if settings['workDays'].get(today.strftime('%A').lower(), False) and datetime.now().time() > settings['CHECK_IN_END_TIME_OBJ']:
        for registered_uid, registered_details in all_registered_students.items():
            if registered_uid not in all_attendance_records:
                absent_count += 1
                # Add absent students to detail list for today
                detail_list.append({
                    'name': registered_details['name'],
                    'date': today.strftime("%Y-%m-%d"),
                    'department': registered_details['department'],
                    'check_in_time': 'N/A',
                    'work_hours': '00:00',
                    'status': 'Absent'
                })
            processed_uids_for_counts.add(registered_uid) # Mark as processed for counting

    for uid, record_data in all_attendance_records.items():
        # Only add to detail_list if the record is for today or within the requested range
        # Given we are only keeping today's records, this effectively means only today's.
        record_date = record_data['date'] if isinstance(record_data['date'], date) else datetime.strptime(record_data['date'], '%Y-%m-%d').date()
        
        if (not start_date_str and not end_date_str and record_date == today) or \
           (start_date_str and end_date_str and requested_start_date <= record_date <= requested_end_date):
            
            detail_list.append({
                'name': record_data['name'],
                'date': record_data['date'].strftime("%Y-%m-%d"),
                'department': record_data['department'],
                'check_in_time': record_data['first_tap'].strftime("%H:%M:%S") if record_data['first_tap'] else 'N/A',
                'work_hours': record_data['work_hours'],
                'status': record_data['status']
            })

            if uid not in processed_uids_for_counts:
                if record_data['status'] == 'Present':
                    present_count += 1
                elif record_data['status'] == 'Late' or record_data['status'] == 'Early':
                    late_count += 1
                processed_uids_for_counts.add(uid)


    total_check_ins = present_count + late_count

    summary = {
        'total_check_ins': total_check_ins,
        'total_users_registered': len(all_registered_students),
        'present': present_count,
        'late': late_count,
        'absent': absent_count,
        'detail': detail_list
    }
    return jsonify(summary)

@app.route('/save')
def save_excel():
    filename = f"Attendance_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = filename # Save to the root directory
    
    wb_export = Workbook()
    ws_export = wb_export.active
    ws_export.title = "Attendance Summary"

    ws_export.append(["UID", "Student Name", "Department", "Date", "Check-in Time", "Work Hours", "Status"])

    # Export only the current day's attendance records
    for uid, record in all_attendance_records.items():
        name = record['name']
        department = record['department']
        attendance_date = record['date'].strftime("%Y-%m-%d")
        check_in_time = record['first_tap'].strftime("%H:%M:%S") if record['first_tap'] else 'N/A'
        work_hours = record['work_hours']
        status = record['status']
        ws_export.append([uid, name, department, attendance_date, check_in_time, work_hours, status])

    try:
        wb_export.save(filepath)
        print(f"Attendance data saved to {filepath}")
        return jsonify({'message': f'Attendance data saved to {filename}'})
    except Exception as e:
        print(f"Error saving Excel file: {e}")
        return jsonify({'message': f'Error saving Excel file: {e}'}), 500

# --- User Management Endpoints ---

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    department = data.get('department')
    rfid = data.get('rfid')

    if not all([name, email, department, rfid]):
        return jsonify({'message': 'Missing user data (name, email, department, or RFID).'}), 400

    if rfid in all_registered_students:
        return jsonify({'message': f'User with RFID {rfid} already exists.'}), 409

    all_registered_students[rfid] = {
        'name': name,
        'email': email,
        'department': department
    }
    save_registered_users_to_file()
    return jsonify({'message': f'User {name} added successfully with RFID {rfid}.'}), 201

@app.route('/delete_user/<string:rfid>', methods=['DELETE'])
def delete_user(rfid):
    if rfid in all_registered_students:
        del all_registered_students[rfid]
        save_registered_users_to_file()
        # Also remove from current attendance if present
        if rfid in all_attendance_records:
            del all_attendance_records[rfid]
        return jsonify({'message': f'User with RFID {rfid} deleted successfully.'}), 200
    return jsonify({'message': f'User with RFID {rfid} not found.'}), 404

@app.route('/users')
def get_users():
    users_list = []
    for rfid, details in all_registered_students.items():
        users_list.append({
            'rfid': rfid,
            'name': details['name'],
            'email': details['email'],
            'department': details['department']
        })
    return jsonify({'users': users_list})

@app.route('/scan_rfid_for_new_user')
def scan_rfid_for_new_user():
    """Endpoint to trigger a real or simulated RFID scan for new user assignment."""
    global last_scanned_rfid
    last_scanned_rfid = None
    rfid_scan_event.set()
    print("Waiting for RFID tap for new user registration...")

    if not ser:
        simulated_uid = simulate_rfid_tap_for_user_registration()
        return jsonify({'message': 'Simulated RFID scanned successfully.', 'rfid': simulated_uid}), 200
    
    if rfid_scan_event.wait(timeout=10):
        if last_scanned_rfid:
            return jsonify({'message': 'RFID scanned successfully.', 'rfid': last_scanned_rfid}), 200
        else:
            return jsonify({'message': 'RFID scan failed or timed out.'}), 500
    else:
        return jsonify({'message': 'RFID scan timed out. No tag detected.'}), 500

# Helper function for simulating a new user RFID for registration
def simulate_rfid_tap_for_user_registration():
    """Simulates a single new RFID for user registration specifically."""
    mock_uid = '0x' + ''.join(random.choices('0123456789ABCDEF', k=8))
    print(f"Simulating new user RFID for registration: {mock_uid}")
    return mock_uid

@app.route('/simulate_attendance_tap')
def simulate_attendance_tap():
    """Endpoint to trigger a single simulated attendance tap."""
    if not all_registered_students:
        departments = ["HR", "Software Developer", "Web Developer", "Tester", "Infrastructure", "Quality Analyst", "Service Now", "Tech Support", "Infrastructure Management"]
        new_uid = '0x' + ''.join(random.choices('0123456789ABCDEF', k=8))
        new_name = f"Sim User {len(all_registered_students) + 1}"
        new_email = f"sim.user.{len(all_registered_students) + 1}@example.com"
        new_department = random.choice(departments)
        
        all_registered_students[new_uid] = {
            'name': new_name,
            'email': new_email,
            'department': new_department
        }
        save_registered_users_to_file()
        print(f"Generated new user: {new_name} ({new_uid}) and simulating tap.")
        process_rfid_tap(new_uid, now=datetime.now() - timedelta(minutes=random.randint(0, 60)))
        return jsonify({'message': f'Simulated tap processed for new user {new_uid}.'}), 200
    else:
        dummy_uid = 'SIM_TAP_TRIGGER'
        process_rfid_tap(dummy_uid, now=datetime.now() - timedelta(minutes=random.randint(0, 60)))
        return jsonify({'message': 'Simulated tap processed for a random registered user.'}), 200

# --- Settings Endpoints ---

@app.route('/save_settings', methods=['POST'])
def save_settings():
    global settings
    new_settings = request.get_json()
    if new_settings:
        settings.update(new_settings)
        settings['CHECK_IN_START_TIME_OBJ'] = datetime.strptime(settings['checkInStart'], '%H:%M').time()
        settings['CHECK_IN_END_TIME_OBJ'] = datetime.strptime(settings['checkInEnd'], '%H:%M').time()
        save_settings_to_file()
        return jsonify({'success': True, 'message': 'Settings saved successfully.'}), 200
    return jsonify({'success': False, 'message': 'No settings provided.'}), 400

@app.route('/load_settings')
def load_settings():
    serializable_settings = settings.copy()
    if 'CHECK_IN_START_TIME_OBJ' in serializable_settings:
        del serializable_settings['CHECK_IN_START_TIME_OBJ']
    if 'CHECK_IN_END_TIME_OBJ' in serializable_settings:
        del serializable_settings['CHECK_IN_END_TIME_OBJ']
    return jsonify(serializable_settings)

# --- Email Functionality ---

def send_email(recipient_email, subject, body, attachment_path=None):
    """Sends an email with optional attachment."""
    sender_email = "sivananthan46m@gmail.com"
    sender_password = "ruvr alht jsqp wpey" # REMINDER: Replace with your actual App Password

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)
        except Exception as e:
            print(f"Error attaching file {attachment_path}: {e}")
            return False, f"Error attaching file: {e}"

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent successfully to {recipient_email}")
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Check your Gmail App Password and ensure 'Less secure app access' is off (it's replaced by App Passwords).")
        return False, "SMTP Authentication Error: Check your Gmail App Password."
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, f"Error sending email: {e}. Check SMTP settings or network."

@app.route('/send_report_email', methods=['POST'])
def send_report_email():
    data = request.get_json()
    start_date_str = data.get('startDate')
    end_date_str = data.get('endDate')
    recipient_email = data.get('recipient')

    if not recipient_email:
        return jsonify({'message': 'Recipient email is required.'}), 400

    # Get the attendance summary for the requested date range (this will only include current day's data now)
    with app.test_request_context(query_string={'startDate': start_date_str, 'endDate': end_date_str}):
        summary_data = get_attendance_summary().json
    
    report_body = "Attendance Report:\n\n"
    report_body += f"Date Range: {start_date_str} to {end_date_str}\n\n"
    report_body += f"Total Registered Users: {summary_data['total_users_registered']}\n"
    report_body += f"Total Check-ins (Present/Late): {summary_data['total_check_ins']}\n"
    report_body += f"Present: {summary_data['present']}\n"
    report_body += f"Late: {summary_data['late']}\n"
    report_body += f"Absent: {summary_data['absent']}\n\n"
    
    report_body += "Detailed Attendance:\n"
    if summary_data['detail']:
        # Sort detail list by name and then date
        sorted_detail = sorted(summary_data['detail'], key=lambda x: (x['name'], x['date']))
        for record in sorted_detail:
            report_body += (f"  Name: {record['name']}, Date: {record['date']}, Department: {record['department']}, "
                            f"Check-in: {record['check_in_time']}, Work Hours: {record['work_hours']}, Status: {record['status']}\n")
    else:
        report_body += "  No attendance records for the selected date range.\n"

    success, message = send_email(
        recipient_email,
        f"Attendance Report from {start_date_str} to {end_date_str}",
        report_body
    )

    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 500

# --- WebSocket Endpoint ---

@sock.route('/ws')
def websocket_connection(ws):
    """Handles WebSocket connections for real-time updates."""
    clients.add(ws)
    print(f"WebSocket client connected. Total clients: {len(clients)}")
    try:
        while True:
            message = ws.receive()
            if message:
                print(f"Received message from client: {message}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove(ws)
        print(f"WebSocket client disconnected. Total clients: {len(clients)}")

# --- Main Execution ---

serial_processing_thread = threading.Thread(target=read_serial_and_process, daemon=True)
serial_processing_thread.start()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)