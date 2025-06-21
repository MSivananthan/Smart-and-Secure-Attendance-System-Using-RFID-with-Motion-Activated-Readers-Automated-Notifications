# Smart-and-Secure-Attendance-System-Using-RFID-with-Motion-Activated-Readers-Automated-Notifications

# Smart Attendance System Using RFID

A smart and secure attendance tracking system built with Flask and Arduino-based RFID readers. Designed for organizations to automate attendance logging, real-time monitoring, and efficient management with motion-activated RFID readers and automatic email notifications.
## Homepage
<img src="Screenshot 2025-06-21 194047.png">

## 🔧 Features

- 🚪 **Motion-Activated RFID Attendance**: Detects employee presence and logs attendance on RFID tag tap.
- 📊 **Real-Time Dashboard**: Live stats of Present, Late, Absent users with date-wise filtering.
- 📥 **Excel Report Download**: One-click export of attendance summary in Excel format.
- 📧 **Email Notifications**: Automated email alerts for late arrivals, absences, and daily summaries.
- 👤 **User Management**: Add, delete, and manage employees with RFID association.
- ⚙️ **Custom Settings**: Set working days, check-in hours, COM port, and notification preferences.

## DashBoard
<img src="Screenshot 2025-06-21 194717.png">

## 🖥️ Technologies Used

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **Microcontroller**: Arduino with RFID reader
- **Data Handling**: JSON & Excel (OpenPyXL)
- **Email**: SMTP (Gmail Integration)
- **Serial Communication**: PySerial
- **WebSocket**: Flask-Sock for real-time RFID events
## User Management
<img src="Screenshot 2025-06-21 194741.png">

## 📁 Project Structure

```

├── App.py                  # Main Flask backend with all endpoints
├── indexx.html             # Responsive frontend dashboard
├── Attendence\_RFID.ino     # Arduino sketch for RFID reader
├── settings.json           # Configurable check-in settings
├── registered\_users.json   # Stores registered users with RFID UIDs
├── /static/                # (Optional) Static assets like CSS/JS

````
## Employee Details
<img src="Screenshot 2025-06-21 194804.png">

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/smart-rfid-attendance.git
cd smart-rfid-attendance
````

### 2. Set Up the Environment

Make sure Python 3.7+ is installed.

```bash
pip install flask flask-cors flask-sock pyserial openpyxl
```

### 3. Run the Flask App

```bash
python App.py
```

Visit `http://127.0.0.1:5000` in your browser.

### 4. Upload the Arduino Sketch

Open `Attendence_RFID.ino` in Arduino IDE and upload it to your Arduino board with the connected RFID module.

## Reports
<img src="Screenshot 2025-06-21 194822.png">

## 🧠 Smart Logic

* **Simulated Attendance**: If no real scan is received, a simulated one is used (useful for testing).
* **Daily Reset**: Attendance records reset automatically each day.
* **Absent Logic**: After the check-in period ends, those who haven't tapped are marked as Absent.

## ⚠️ Note

> Make sure to update your Gmail App Password in the `send_email()` function inside `App.py` for email functionality.

```python
sender_password = "your-app-password"
```

## 📸 UI Highlights

* Modern admin panel with dashboard widgets
* Mobile-responsive layout
* Employee profile cards and attendance table
## Setting
<img src="Screenshot 2025-06-21 194841.png">

## 📬 Contact

Maintained by **Sivananthan M**
📧 [sivananthan46m@gmail.com](mailto:sivananthan46m@gmail.com)

---

```

Would you like this `README.md` saved to a file so you can push it directly to GitHub?
```
