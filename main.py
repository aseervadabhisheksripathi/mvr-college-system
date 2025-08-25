# FIXED VERSION - main.py
# MVR College Automated Call System
# This version has all syntax errors fixed

import os
from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# ============= CONFIGURATION =============
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
GOOGLE_SHEETS_CREDS = os.environ.get('GOOGLE_SHEETS_CREDS')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')

# Initialize Twilio
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

# ============= GOOGLE SHEETS CONNECTION =============
def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        if not GOOGLE_SHEETS_CREDS:
            return None
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID)
        return sheet.worksheet('Students')
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def get_call_log_sheet():
    """Get the call log worksheet"""
    try:
        if not GOOGLE_SHEETS_CREDS:
            return None
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID)
        return sheet.worksheet('CallLogs')
    except:
        return None

# ============= HTML INTERFACE =============
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MVR College - Automated Call System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .controls {
            padding: 30px;
            background: #f7fafc;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #48bb78;
            color: white;
        }
        
        .btn-warning {
            background: #ed8936;
            color: white;
        }
        
        .status {
            padding: 10px 20px;
            border-radius: 8px;
            margin: 20px 30px;
            display: none;
        }
        
        .status.success {
            background: #c6f6d5;
            color: #22543d;
            border: 1px solid #9ae6b4;
        }
        
        .status.error {
            background: #fed7d7;
            color: #742a2a;
            border: 1px solid #fc8181;
        }
        
        .status.info {
            background: #bee3f8;
            color: #2c5282;
            border: 1px solid #90cdf4;
        }
        
        .table-container {
            padding: 30px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #4a5568;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        tr:hover {
            background: #f7fafc;
        }
        
        .action-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }
        
        .call-late {
            background: #f56565;
            color: white;
        }
        
        .call-permission {
            background: #ed8936;
            color: white;
        }
        
        .info-card {
            background: #edf2f7;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 30px;
        }
        
        .info-card h3 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background: white;
            margin: 10% auto;
            padding: 30px;
            width: 80%;
            max-width: 500px;
            border-radius: 10px;
            position: relative;
        }
        
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            color: #718096;
        }
        
        .phone-options label {
            display: block;
            margin: 10px 0;
            cursor: pointer;
            padding: 10px;
            background: #f7fafc;
            border-radius: 6px;
        }
        
        .search-box {
            padding: 10px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            font-size: 1em;
            width: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MVR Engineering & Polytechnic College</h1>
            <p>Automated Call Management System</p>
        </header>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh Data</button>
            <input type="text" class="search-box" id="searchBox" placeholder="Search students..." onkeyup="filterTable()">
            <button class="btn btn-success" onclick="openSheetsLink()">📊 Open Google Sheet</button>
            <button class="btn btn-warning" onclick="viewCallLogs()">📞 Call Logs</button>
        </div>
        
        <div class="status" id="statusMessage"></div>
        
        <div class="info-card">
            <h3>📌 Quick Instructions</h3>
            <p>
                1. Student data is managed directly in Google Sheets<br>
                2. Click "Late Call" to notify parents about late arrival<br>
                3. Click "Permission Call" to request parent permission<br>
                4. All calls are in Telugu with automated voice<br>
                5. Permission calls ask parents to press 1 (allow) or 2 (deny)
            </p>
        </div>
        
        <div class="table-container">
            <div id="tableContent" class="loading">Loading student data...</div>
        </div>
    </div>
    
    <!-- Modal for phone selection -->
    <div id="phoneModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h3 id="modalTitle">Select Phone Number</h3>
            <div id="modalStudentInfo"></div>
            <div class="phone-options" id="phoneOptions"></div>
            <button class="btn btn-primary" onclick="makeSelectedCall()">Make Call</button>
        </div>
    </div>
    
    <script>
        let studentsData = [];
        let currentCallData = {};
        
        window.onload = function() {
            refreshData();
        };
        
        function refreshData() {
            showStatus('info', 'Loading student data...');
            fetch('/api/students')
                .then(response => response.json())
                .then(data => {
                    studentsData = data.students || [];
                    renderTable(studentsData);
                    showStatus('success', 'Loaded ' + studentsData.length + ' students');
                })
                .catch(error => {
                    showStatus('error', 'Failed to load data: ' + error.message);
                });
        }
        
        function renderTable(students) {
            if (!students || students.length === 0) {
                document.getElementById('tableContent').innerHTML = '<p style="text-align: center; padding: 50px;">No students found. Add students in Google Sheets.</p>';
                return;
            }
            
            let html = '<table><thead><tr>';
            html += '<th>S.No</th><th>Reg. Number</th><th>Student Name</th><th>Gender</th>';
            html += '<th>Father Name</th><th>Mother Name</th><th>Father Phone</th>';
            html += '<th>Mother Phone</th><th>Actions</th></tr></thead><tbody>';
            
            students.forEach((student, index) => {
                html += '<tr>';
                html += '<td>' + (student['S.No'] || index + 1) + '</td>';
                html += '<td>' + (student['Register Number'] || '') + '</td>';
                html += '<td>' + (student['Student Name'] || '') + '</td>';
                html += '<td>' + (student['Gender'] || '') + '</td>';
                html += '<td>' + (student['Father Name'] || '') + '</td>';
                html += '<td>' + (student['Mother Name'] || '') + '</td>';
                html += '<td>' + (student['Father Phone'] || '') + '</td>';
                html += '<td>' + (student['Mother Phone'] || '') + '</td>';
                html += '<td><div class="action-buttons">';
                html += '<button class="action-btn call-late" onclick="initiateCall(' + index + ', \'late\')">Late Call</button>';
                html += '<button class="action-btn call-permission" onclick="initiateCall(' + index + ', \'permission\')">Permission</button>';
                html += '</div></td></tr>';
            });
            
            html += '</tbody></table>';
            document.getElementById('tableContent').innerHTML = html;
        }
        
        function filterTable() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const filtered = studentsData.filter(student => {
                return Object.values(student).some(value => 
                    value && value.toString().toLowerCase().includes(searchTerm)
                );
            });
            renderTable(filtered);
        }
        
        function initiateCall(index, callType) {
            const student = studentsData[index];
            currentCallData = { student, callType, index };
            
            const modal = document.getElementById('phoneModal');
            const title = document.getElementById('modalTitle');
            const info = document.getElementById('modalStudentInfo');
            const options = document.getElementById('phoneOptions');
            
            title.textContent = callType === 'late' ? 'Late Attendance Call' : 'Permission Request Call';
            info.innerHTML = '<p><strong>Student:</strong> ' + student['Student Name'] + '</p>';
            info.innerHTML += '<p><strong>Register Number:</strong> ' + student['Register Number'] + '</p>';
            
            let optionsHtml = '';
            if (student['Father Phone']) {
                optionsHtml += '<label><input type="radio" name="phoneSelect" value="father"> ';
                optionsHtml += 'Call Father: ' + student['Father Name'] + ' (' + student['Father Phone'] + ')</label>';
            }
            if (student['Mother Phone']) {
                optionsHtml += '<label><input type="radio" name="phoneSelect" value="mother"> ';
                optionsHtml += 'Call Mother: ' + student['Mother Name'] + ' (' + student['Mother Phone'] + ')</label>';
            }
            
            if (!optionsHtml) {
                optionsHtml = '<p style="color: red;">No phone numbers available for this student</p>';
            }
            
            options.innerHTML = optionsHtml;
            modal.style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('phoneModal').style.display = 'none';
        }
        
        function makeSelectedCall() {
            const selected = document.querySelector('input[name="phoneSelect"]:checked');
            if (!selected) {
                alert('Please select a phone number');
                return;
            }
            
            const target = selected.value;
            const { student, callType, index } = currentCallData;
            
            closeModal();
            showStatus('info', 'Initiating call...');
            
            const endpoint = callType === 'late' ? '/api/call/late' : '/api/call/permission';
            
            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    row_index: index + 2,
                    target: target
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', 'Call initiated successfully! Call ID: ' + data.call_sid);
                } else {
                    showStatus('error', data.error || 'Failed to initiate call');
                }
            })
            .catch(error => {
                showStatus('error', 'Error: ' + error.message);
            });
        }
        
        function showStatus(type, message) {
            const status = document.getElementById('statusMessage');
            status.className = 'status ' + type;
            status.textContent = message;
            status.style.display = 'block';
            
            if (type !== 'error') {
                setTimeout(() => {
                    status.style.display = 'none';
                }, 5000);
            }
        }
        
        function openSheetsLink() {
            const sheetId = ''' + "'" + (SPREADSHEET_ID or '') + "'" + ''';
            if (sheetId) {
                window.open('https://docs.google.com/spreadsheets/d/' + sheetId, '_blank');
            } else {
                alert('Sheet ID not configured');
            }
        }
        
        function viewCallLogs() {
            window.location.href = '/logs';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('phoneModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

# ============= ROUTES =============
@app.route('/')
def index():
    """Main dashboard"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/students')
def get_students():
    """Get all students from Google Sheets"""
    try:
        worksheet = get_google_sheet()
        if not worksheet:
            return jsonify({'error': 'Could not connect to Google Sheets', 'students': []}), 200
        
        records = worksheet.get_all_records()
        return jsonify({'students': records})
    except Exception as e:
        return jsonify({'error': str(e), 'students': []}), 200

@app.route('/api/call/late', methods=['POST'])
def make_late_call():
    """Initiate late attendance call"""
    try:
        if not twilio_client:
            return jsonify({'error': 'Twilio not configured'}), 500
            
        data = request.json
        row_index = data.get('row_index')
        target = data.get('target', 'father')
        
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        
        student_data = {
            'name': student_row[2] if len(student_row) > 2 else '',
            'gender': student_row[3] if len(student_row) > 3 else 'M',
            'father_name': student_row[4] if len(student_row) > 4 else '',
            'mother_name': student_row[5] if len(student_row) > 5 else '',
            'father_phone': student_row[6] if len(student_row) > 6 else '',
            'mother_phone': student_row[7] if len(student_row) > 7 else ''
        }
        
        if target == 'father':
            to_number = student_data['father_phone']
            parent_name = student_data['father_name']
        else:
            to_number = student_data['mother_phone']
            parent_name = student_data['mother_name']
        
        if not to_number:
            return jsonify({'error': 'Phone number not available'}), 400
        
        if not to_number.startswith('+91'):
            to_number = '+91' + to_number.replace(' ', '').replace('-', '')[-10:]
        
        twiml_url = request.url_root + f'twiml/late/{row_index}/{target}'
        
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url
        )
        
        log_call(student_data['name'], 'late', target, to_number, call.sid)
        
        return jsonify({'success': True, 'call_sid': call.sid})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/call/permission', methods=['POST'])
def make_permission_call():
    """Initiate permission request call"""
    try:
        if not twilio_client:
            return jsonify({'error': 'Twilio not configured'}), 500
            
        data = request.json
        row_index = data.get('row_index')
        target = data.get('target', 'father')
        
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        
        student_data = {
            'name': student_row[2] if len(student_row) > 2 else '',
            'gender': student_row[3] if len(student_row) > 3 else 'M',
            'father_name': student_row[4] if len(student_row) > 4 else '',
            'mother_name': student_row[5] if len(student_row) > 5 else '',
            'father_phone': student_row[6] if len(student_row) > 6 else '',
            'mother_phone': student_row[7] if len(student_row) > 7 else ''
        }
        
        if target == 'father':
            to_number = student_data['father_phone']
        else:
            to_number = student_data['mother_phone']
        
        if not to_number:
            return jsonify({'error': 'Phone number not available'}), 400
        
        if not to_number.startswith('+91'):
            to_number = '+91' + to_number.replace(' ', '').replace('-', '')[-10:]
        
        twiml_url = request.url_root + f'twiml/permission/{row_index}/{target}'
        
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url
        )
        
        log_call(student_data['name'], 'permission', target, to_number, call.sid)
        
        return jsonify({'success': True, 'call_sid': call.sid})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/twiml/late/<int:row_index>/<target>')
def twiml_late(row_index, target):
    """Generate TwiML for late attendance call"""
    try:
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        
        student_name = student_row[2] if len(student_row) > 2 else 'Student'
        gender = student_row[3].upper() if len(student_row) > 3 else 'M'
        parent_name = student_row[4] if target == 'father' else student_row[5]
        
        child_term = "mee abbai" if gender == 'M' else "mee ammai"
        
        message = f"Namaskaram {parent_name} garu! Memu MVR Engineering and Polytechnic College nunchi matladutunnamu. {child_term} {student_name} college ki late ga vachinanduku, college gate musiveyabadindi. Andukani {child_term} ki ee roju absent veyabadutundi. Gamaninchagalaru. Dhanyavadamulu!"
        
        response = VoiceResponse()
        response.say(message, voice='Polly.Aditi', language='hi-IN')
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        response = VoiceResponse()
        response.say("Sorry, an error occurred.", voice='Polly.Aditi', language='en-IN')
        return Response(str(response), mimetype='text/xml')

@app.route('/twiml/permission/<int:row_index>/<target>')
def twiml_permission(row_index, target):
    """Generate TwiML for permission request call"""
    try:
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        
        student_name = student_row[2] if len(student_row) > 2 else 'Student'
        gender = student_row[3].upper() if len(student_row) > 3 else 'M'
        parent_name = student_row[4] if target == 'father' else student_row[5]
        
        child_term = "mee abbai" if gender == 'M' else "mee ammai"
        
        message = f"Namaskaram {parent_name} garu! Memu MVR Engineering and Polytechnic College nunchi matladutunnamu. {child_term} {student_name} hostel nunchi bayataki velladaniki anumati adugutunnaru."
        
        response = VoiceResponse()
        response.say(message, voice='Polly.Aditi', language='hi-IN')
        
        gather = Gather(
            num_digits=1,
            action=f'/twiml/permission/response/{row_index}/{target}',
            method='POST'
        )
        gather.say("Anumati ivvadaniki okati nokkandi. Voddu anadaniki rendu nokkandi.", 
                  voice='Polly.Aditi', language='hi-IN')
        response.append(gather)
        
        response.say("Mee spandana pondaledu. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        response = VoiceResponse()
        response.say("Sorry, an error occurred.", voice='Polly.Aditi', language='en-IN')
        return Response(str(response), mimetype='text/xml')

@app.route('/twiml/permission/response/<int:row_index>/<target>', methods=['POST'])
def twiml_permission_response(row_index, target):
    """Handle permission response from parent"""
    try:
        digit = request.form.get('Digits', '')
        
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        student_name = student_row[2] if len(student_row) > 2 else 'Student'
        
        response = VoiceResponse()
        
        if digit == '1':
            response.say("Anumati ivvabadindi. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
            log_permission_response(student_name, target, 'granted')
        elif digit == '2':
            response.say("Anumati nirakarinchbadindi. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
            log_permission_response(student_name, target, 'denied')
        else:
            response.say("Tappu number nokkaru. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        response = VoiceResponse()
        response.say("Sorry, an error occurred.", voice='Polly.Aditi', language='en-IN')
        return Response(str(response), mimetype='text/xml')

@app.route('/logs')
def view_logs():
    """View call logs page"""
    logs_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Call Logs - MVR College</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #4a5568; color: white; }
            .back-btn { padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">Back to Dashboard</a>
            <h1>Call Logs</h1>
            <div id="logsContent">Loading...</div>
        </div>
        <script>
            fetch('/api/logs')
                .then(r => r.json())
                .then(data => {
                    if (data.logs && data.logs.length > 0) {
                        let html = '<table><tr><th>Time</th><th>Student</th><th>Type</th><th>Target</th><th>Phone</th><th>Response</th></tr>';
                        data.logs.forEach(log => {
                            html += '<tr><td>' + log[0] + '</td><td>' + log[1] + '</td><td>' + log[2] + '</td><td>' + log[3] + '</td><td>' + log[4] + '</td><td>' + (log[5] || '-') + '</td></tr>';
                        });
                        html += '</table>';
                        document.getElementById('logsContent').innerHTML = html;
                    } else {
                        document.getElementById('logsContent').innerHTML = '<p>No call logs yet.</p>';
                    }
                })
                .catch(e => {
                    document.getElementById('logsContent').innerHTML = '<p>Error loading logs.</p>';
                });
        </script>
    </body>
    </html>
    """
    return logs_html

@app.route('/api/logs')
def get_logs():
    """Get call logs from Google Sheets"""
    try:
        worksheet = get_call_log_sheet()
        if worksheet:
            logs = worksheet.get_all_values()[1:]
            return jsonify({'logs': logs})
        return jsonify({'logs': []})
    except:
        return jsonify({'logs': []})

# ============= HELPER FUNCTIONS =============
def log_call(student_name, call_type, target, phone, call_sid):
    """Log call to Google Sheets"""
    try:
        worksheet = get_call_log_sheet()
        if worksheet:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            worksheet.append_row([timestamp, student_name, call_type, target, phone, call_sid, ''])
    except:
        pass

def log_permission_response(student_name, target, response):
    """Log permission response to Google Sheets"""
    try:
        worksheet = get_call_log_sheet()
        if worksheet:
            all_values = worksheet.get_all_values()
            for i in range(len(all_values) - 1, 0, -1):
                if all_values[i][1] == student_name and all_values[i][2] == 'permission':
                    worksheet.update_cell(i + 1, 7, response)
                    break
    except:
        pass

# ============= MAIN =============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
