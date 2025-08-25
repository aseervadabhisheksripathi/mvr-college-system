# COMPLETE WORKING VERSION - main.py
# MVR College Automated Call System
# This is the FULL, COMPLETE, TESTED version

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
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
GOOGLE_SHEETS_CREDS = os.environ.get('GOOGLE_SHEETS_CREDS', '')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '')

# Initialize Twilio
try:
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("Twilio initialized successfully")
    else:
        twilio_client = None
        print("Twilio not configured")
except Exception as e:
    print(f"Twilio error: {e}")
    twilio_client = None

# ============= GOOGLE SHEETS CONNECTION =============
def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        if not GOOGLE_SHEETS_CREDS or not SPREADSHEET_ID:
            print("Missing Google credentials")
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
        print(f"Google Sheets error: {e}")
        return None

def get_call_log_sheet():
    """Get CallLogs worksheet"""
    try:
        if not GOOGLE_SHEETS_CREDS or not SPREADSHEET_ID:
            return None
            
        creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        try:
            return sheet.worksheet('CallLogs')
        except:
            # Create CallLogs sheet if it doesn't exist
            worksheet = sheet.add_worksheet(title='CallLogs', rows=100, cols=7)
            worksheet.append_row(['Timestamp', 'Student Name', 'Call Type', 'Target', 'Phone Number', 'Call SID', 'Response'])
            return worksheet
    except Exception as e:
        print(f"CallLogs error: {e}")
        return None

# ============= MAIN PAGE =============
@app.route('/')
def index():
    """Main dashboard page"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>MVR College - Call System</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .controls {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        button:hover {
            background: #5a67d8;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background: #4a5568;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .action-btn {
            background: #48bb78;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            margin: 2px;
            font-size: 12px;
        }
        .action-btn.late {
            background: #f56565;
        }
        .action-btn.permission {
            background: #ed8936;
        }
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        .instructions {
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MVR Engineering & Polytechnic College</h1>
        <p class="subtitle">Automated Call Management System</p>
        
        <div class="instructions">
            <h3>Quick Instructions</h3>
            <p>
                1. Click "Load Students" to fetch data from Google Sheets<br>
                2. Use "Late Call" buttons to notify parents about absence<br>
                3. Use "Permission Call" buttons for hostel leave requests<br>
                4. Status: <span id="config-status">Checking...</span>
            </p>
        </div>
        
        <div class="controls">
            <button onclick="loadStudents()">Load Students</button>
            <button onclick="checkStatus()">Check Status</button>
            <button onclick="testDebug()">Debug Info</button>
            <button onclick="viewLogs()">View Logs</button>
        </div>
        
        <div id="statusMessage" class="status"></div>
        
        <div id="tableContainer">
            <div class="loading">Click "Load Students" to begin</div>
        </div>
    </div>
    
    <script>
        let studentsData = [];
        
        window.onload = function() {
            checkStatus();
        };
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
        function checkStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    let status = [];
                    if (data.twilio_configured) status.push('Twilio OK');
                    else status.push('Twilio Missing');
                    if (data.sheets_configured) status.push('Sheets OK');
                    else status.push('Sheets Missing');
                    document.getElementById('config-status').textContent = status.join(' | ');
                })
                .catch(error => {
                    document.getElementById('config-status').textContent = 'Error checking';
                });
        }
        
        function loadStudents() {
            showStatus('Loading students...', 'info');
            document.getElementById('tableContainer').innerHTML = '<div class="loading">Loading...</div>';
            
            fetch('/api/students')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showStatus('Error: ' + data.error, 'error');
                        document.getElementById('tableContainer').innerHTML = '<div class="loading">Error: ' + data.error + '</div>';
                    } else {
                        studentsData = data.students || [];
                        if (studentsData.length === 0) {
                            showStatus('No students found', 'info');
                            document.getElementById('tableContainer').innerHTML = '<div class="loading">No students in sheet</div>';
                        } else {
                            showStatus('Loaded ' + studentsData.length + ' students', 'success');
                            displayStudents(studentsData);
                        }
                    }
                })
                .catch(error => {
                    showStatus('Failed: ' + error.message, 'error');
                    document.getElementById('tableContainer').innerHTML = '<div class="loading">Failed to connect</div>';
                });
        }
        
        function displayStudents(students) {
            let html = '<table><thead><tr>';
            html += '<th>S.No</th><th>Reg Number</th><th>Student</th><th>Gender</th>';
            html += '<th>Father</th><th>Mother</th><th>Actions</th></tr></thead><tbody>';
            
            students.forEach((student, index) => {
                html += '<tr>';
                html += '<td>' + (student['S.No'] || (index + 1)) + '</td>';
                html += '<td>' + (student['Register Number'] || '-') + '</td>';
                html += '<td>' + (student['Student Name'] || '-') + '</td>';
                html += '<td>' + (student['Gender'] || 'M') + '</td>';
                html += '<td>' + (student['Father Name'] || '-') + '</td>';
                html += '<td>' + (student['Mother Name'] || '-') + '</td>';
                html += '<td>';
                
                const fatherPhone = student['Father Phone'];
                const motherPhone = student['Mother Phone'];
                
                if (fatherPhone) {
                    html += '<button class="action-btn late" onclick="makeCall(' + index + ', \\'late\\', \\'father\\')">Late-Dad</button>';
                    html += '<button class="action-btn permission" onclick="makeCall(' + index + ', \\'permission\\', \\'father\\')">Permit-Dad</button>';
                }
                if (motherPhone) {
                    html += '<button class="action-btn late" onclick="makeCall(' + index + ', \\'late\\', \\'mother\\')">Late-Mom</button>';
                    html += '<button class="action-btn permission" onclick="makeCall(' + index + ', \\'permission\\', \\'mother\\')">Permit-Mom</button>';
                }
                if (!fatherPhone && !motherPhone) {
                    html += '<span style="color: red;">No phones</span>';
                }
                
                html += '</td></tr>';
            });
            
            html += '</tbody></table>';
            document.getElementById('tableContainer').innerHTML = html;
        }
        
        function makeCall(index, type, target) {
            const student = studentsData[index];
            const name = student['Student Name'];
            
            if (!confirm('Call ' + target + ' of ' + name + ' for ' + type + '?')) {
                return;
            }
            
            showStatus('Calling...', 'info');
            
            const endpoint = type === 'late' ? '/api/call/late' : '/api/call/permission';
            
            fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    row_index: index + 2,
                    target: target
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('Call initiated!', 'success');
                } else {
                    showStatus('Failed: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('Error: ' + error.message, 'error');
            });
        }
        
        function testDebug() {
            window.open('/debug', '_blank');
        }
        
        function viewLogs() {
            window.location.href = '/logs';
        }
    </script>
</body>
</html>
"""
    return html_content

# ============= API ENDPOINTS =============
@app.route('/api/status')
def api_status():
    """Check configuration status"""
    return jsonify({
        'twilio_configured': bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER),
        'sheets_configured': bool(GOOGLE_SHEETS_CREDS and SPREADSHEET_ID)
    })

@app.route('/api/students')
def get_students():
    """Get all students from Google Sheets"""
    try:
        worksheet = get_google_sheet()
        if not worksheet:
            return jsonify({'error': 'Cannot connect to Google Sheets', 'students': []})
        
        records = worksheet.get_all_records()
        return jsonify({'students': records})
    except Exception as e:
        return jsonify({'error': str(e), 'students': []})

@app.route('/debug')
def debug():
    """Debug endpoint to check configuration"""
    debug_info = {
        'twilio_configured': bool(TWILIO_ACCOUNT_SID),
        'twilio_sid': TWILIO_ACCOUNT_SID[:10] + '...' if TWILIO_ACCOUNT_SID else 'Not set',
        'twilio_number': TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else 'Not set',
        'sheets_configured': bool(GOOGLE_SHEETS_CREDS),
        'spreadsheet_id': SPREADSHEET_ID if SPREADSHEET_ID else 'Not set',
        'creds_length': len(GOOGLE_SHEETS_CREDS) if GOOGLE_SHEETS_CREDS else 0
    }
    
    try:
        worksheet = get_google_sheet()
        if worksheet:
            debug_info['sheets_connection'] = 'SUCCESS'
            debug_info['sheet_name'] = worksheet.title
            debug_info['row_count'] = worksheet.row_count
            
            try:
                headers = worksheet.row_values(1)
                debug_info['headers'] = headers
                all_records = worksheet.get_all_records()
                debug_info['data_rows'] = len(all_records)
            except:
                debug_info['headers'] = 'Could not read'
        else:
            debug_info['sheets_connection'] = 'FAILED'
    except Exception as e:
        debug_info['sheets_connection'] = f'ERROR: {str(e)}'
    
    return jsonify(debug_info)

@app.route('/api/call/late', methods=['POST'])
def make_late_call():
    """Initiate late attendance call"""
    try:
        if not twilio_client:
            return jsonify({'success': False, 'error': 'Twilio not configured'})
            
        data = request.json
        row_index = data.get('row_index', 2)
        target = data.get('target', 'father')
        
        worksheet = get_google_sheet()
        if not worksheet:
            return jsonify({'success': False, 'error': 'Cannot connect to sheets'})
            
        student_row = worksheet.row_values(row_index)
        
        if len(student_row) < 8:
            return jsonify({'success': False, 'error': 'Invalid student data'})
        
        student_name = student_row[2]
        gender = student_row[3]
        parent_name = student_row[4] if target == 'father' else student_row[5]
        phone = student_row[6] if target == 'father' else student_row[7]
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number not available'})
        
        # Format phone number
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            phone = '+91' + phone[-10:]
        
        # Create message
        child_term = "mee abbai" if gender.upper() == 'M' else "mee ammai"
        message = f"Namaskaram {parent_name} garu! Memu MVR Engineering College nunchi matladutunnamu. {child_term} {student_name} college ki late ga vachinanduku absent veyabadutundi. Dhanyavadamulu!"
        
        # Make call with TwiML
        twiml = f'<Response><Say voice="Polly.Aditi" language="hi-IN">{message}</Say></Response>'
        
        call = twilio_client.calls.create(
            to=phone,
            from_=TWILIO_PHONE_NUMBER,
            twiml=twiml
        )
        
        log_call(student_name, 'late', target, phone, call.sid)
        
        return jsonify({'success': True, 'call_sid': call.sid})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/call/permission', methods=['POST'])
def make_permission_call():
    """Initiate permission request call"""
    try:
        if not twilio_client:
            return jsonify({'success': False, 'error': 'Twilio not configured'})
            
        data = request.json
        row_index = data.get('row_index', 2)
        target = data.get('target', 'father')
        
        worksheet = get_google_sheet()
        if not worksheet:
            return jsonify({'success': False, 'error': 'Cannot connect to sheets'})
            
        student_row = worksheet.row_values(row_index)
        
        if len(student_row) < 8:
            return jsonify({'success': False, 'error': 'Invalid student data'})
        
        phone = student_row[6] if target == 'father' else student_row[7]
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number not available'})
        
        # Format phone number
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            phone = '+91' + phone[-10:]
        
        # Generate TwiML URL
        twiml_url = request.url_root + f'twiml/permission/{row_index}/{target}'
        
        call = twilio_client.calls.create(
            to=phone,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url
        )
        
        student_name = student_row[2]
        log_call(student_name, 'permission', target, phone, call.sid)
        
        return jsonify({'success': True, 'call_sid': call.sid})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/twiml/permission/<int:row_index>/<target>')
def twiml_permission(row_index, target):
    """Generate TwiML for permission call"""
    try:
        worksheet = get_google_sheet()
        student_row = worksheet.row_values(row_index)
        
        student_name = student_row[2]
        gender = student_row[3]
        parent_name = student_row[4] if target == 'father' else student_row[5]
        
        child_term = "mee abbai" if gender.upper() == 'M' else "mee ammai"
        
        message = f"Namaskaram {parent_name} garu! Memu MVR Engineering College nunchi matladutunnamu. {child_term} {student_name} hostel nunchi bayataki velladaniki anumati adugutunnaru."
        
        response = VoiceResponse()
        response.say(message, voice='Polly.Aditi', language='hi-IN')
        
        gather = Gather(
            num_digits=1,
            action=f'/twiml/response/{row_index}/{target}',
            method='POST'
        )
        gather.say("Anumati ivvadaniki okati nokkandi. Voddu anadaniki rendu nokkandi.", 
                  voice='Polly.Aditi', language='hi-IN')
        response.append(gather)
        
        response.say("Response pondaledu. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        response = VoiceResponse()
        response.say("Error occurred", voice='alice')
        return Response(str(response), mimetype='text/xml')

@app.route('/twiml/response/<int:row_index>/<target>', methods=['POST'])
def handle_response(row_index, target):
    """Handle IVR response"""
    digit = request.form.get('Digits', '')
    
    response = VoiceResponse()
    
    if digit == '1':
        response.say("Anumati ivvabadindi. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
        try:
            worksheet = get_google_sheet()
            student_row = worksheet.row_values(row_index)
            student_name = student_row[2]
            log_permission_response(student_name, target, 'Granted')
        except:
            pass
    elif digit == '2':
        response.say("Anumati nirakarinchbadindi. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
        try:
            worksheet = get_google_sheet()
            student_row = worksheet.row_values(row_index)
            student_name = student_row[2]
            log_permission_response(student_name, target, 'Denied')
        except:
            pass
    else:
        response.say("Invalid input. Dhanyavadamulu!", voice='Polly.Aditi', language='hi-IN')
    
    return Response(str(response), mimetype='text/xml')

@app.route('/logs')
def view_logs():
    """View call logs page"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Call Logs</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4a5568; color: white; }
        .back-btn { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
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
                        html += '<tr>';
                        for (let i = 0; i < 6; i++) {
                            html += '<td>' + (log[i] || '-') + '</td>';
                        }
                        html += '</tr>';
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
""")

@app.route('/api/logs')
def get_logs():
    """Get call logs from Google Sheets"""
    try:
        worksheet = get_call_log_sheet()
        if worksheet:
            logs = worksheet.get_all_values()[1:]  # Skip header
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
    except Exception as e:
        print(f"Error logging call: {e}")

def log_permission_response(student_name, target, response):
    """Log permission response"""
    try:
        worksheet = get_call_log_sheet()
        if worksheet:
            all_values = worksheet.get_all_values()
            for i in range(len(all_values) - 1, 0, -1):
                if len(all_values[i]) > 2:
                    if all_values[i][1] == student_name and all_values[i][2] == 'permission':
                        worksheet.update_cell(i + 1, 7, response)
                        break
    except Exception as e:
        print(f"Error logging response: {e}")

# ============= ERROR HANDLERS =============
@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404

@app.errorhandler(500)
def server_error(e):
    return "Server error", 500

# ============= MAIN =============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    print(f"Twilio: {bool(TWILIO_ACCOUNT_SID)}")
    print(f"Sheets: {bool(GOOGLE_SHEETS_CREDS)}")
    app.run(host='0.0.0.0', port=port, debug=False)
