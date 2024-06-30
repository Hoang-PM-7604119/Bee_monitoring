from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, redirect
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import sqlite3
import os
import json
import subprocess
from urllib.parse import unquote

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/stats/<int:hive>', methods=['GET', 'POST'])
def stats(hive):
    if request.method == 'POST':
        selected_date = request.form.get('selected-date')
        hive = request.form.get('selected-hive')
    else:
        selected_date = datetime.now().strftime('%Y-%m-%d')

    with sqlite3.connect('test.db') as conn:
        cur = conn.cursor()

        # Query for detailed data
        query = "SELECT date, time, max, min, avg, median FROM bee WHERE date = ? AND hive = ? ORDER BY time ASC"
        cur.execute(query, (selected_date, hive,))
        rows = cur.fetchall()
        '''
        query = "SELECT date, time, max, min, avg, median FROM bee WHERE hive = ? ORDER BY time ASC"
        cur.execute(query, (hive,))
        rows = cur.fetchall()
        '''
        query5 = "SELECT time, temp, hum FROM temphum WHERE date = ? ORDER BY time ASC"
        cur.execute(query5, (selected_date,))
        rows1 = cur.fetchall()

        # Initialize default values in case there is no data
        dates, times, maxs, mins, avgs, medians, temp, hum, th_times = ([] for _ in range(9))
        total_max, total_min = 0, 0  # Default summary values

        if rows:
            # Extract data only if rows are present
            dates = [row[0] for row in rows]
            times = [row[1] for row in rows]
            maxs = [row[2] for row in rows]
            mins = [row[3] for row in rows]
            avgs = [row[4] for row in rows]
            medians = [row[5] for row in rows]

        if rows1:
            th_times = [row1[0] for row1 in rows1]
            temp = [row1[1] for row1 in rows1]
            hum = [row1[2] for row1 in rows1]

        # Serialize the lists to JSON strings
        dates_json = json.dumps(dates)
        times_json = json.dumps(times)
        maxs_json = json.dumps(maxs)
        mins_json = json.dumps(mins)
        avgs_json = json.dumps(avgs)
        medians_json = json.dumps(medians)
        th_times_json = json.dumps(th_times)
        temp_json = json.dumps(temp)
        hum_json = json.dumps(hum)

        # Query for summary data
        query1 = "SELECT date, SUM(max) AS total_max, SUM(min) AS total_min FROM bee WHERE date = ? AND hive = ? GROUP BY date"
        cur.execute(query1, (selected_date, hive,))
        data = cur.fetchone()

        if data:
            # Extract summary data only if present
            total_max, total_min = data[1], data[2]

        # Query for video src
        query2 = "SELECT video FROM bee WHERE date = ? and hive = ? GROUP BY date LIMIT 1"
        cur.execute(query2, (selected_date, hive,))
        video = cur.fetchone()

        query3 = "SELECT DISTINCT hive FROM bee"
        cur.execute(query3)
        hive_data = cur.fetchall()

        if video:
            video = video[0]

        cur.close()
        conn.commit()

    return render_template('stats.html', dates=dates_json, times=times_json, maxs=maxs_json, mins=mins_json, avgs=avgs_json, medians=medians_json, total_max=total_max, total_min=total_min, selected_date=selected_date, video=video, hive=hive, hive_data=hive_data, temp=temp_json, hum=hum_json, th_times=th_times_json)


@app.route('/custom_bee')
def custom():
    return render_template('custom_bee.html')


@app.route('/')
def home():
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT hive FROM bee")
    data = cur.fetchall()
    cur.close()
    return render_template('home.html', data=data)


@app.route('/table/<int:hive>')
def test(hive):
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    cur.execute("SELECT datetime, video, max, min, avg, median, result, hive, id FROM bee WHERE hive = ? ORDER BY datetime DESC", (hive,))
    data = cur.fetchall()
    cur.close()
    return render_template('table.html', data=data, hive=hive)


@app.route('/delete_record/<int:record_id>')
def delete_record(record_id):
    # Delete the camera from the database using camera_id
    with sqlite3.connect('test.db') as conn:
        cur = conn.cursor()
        query = "DELETE FROM bee WHERE id = ?"
        cur.execute(query, (record_id,))
        conn.commit()

    return redirect(url_for('test', hive=1))


@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_directory = '/media/data3/beehiveDATA/videos/video/'
    return send_from_directory(video_directory, filename)


@app.route('/results/<path:filename>')
def serve_result(filename):
    video_directory = '/media/data3/beehiveDATA/videos/result/'
    # Check if the file has an .avi extension
    if filename.lower().endswith('.avi'):
        # Change the file extension from .avi to .mp4
        filename_no_ext = os.path.splitext(filename)[0]
        filename = f"{filename_no_ext}.mp4"
    return send_from_directory(video_directory, filename)


def convert_avi_to_mp4(avi_file_path, mp4_file_path):
    command = [
        'ffmpeg',
        '-i', avi_file_path,  # Input file path
        '-c:v', 'libx264',  # Video codec
        '-crf', '23',  # Quality level
        '-preset', 'veryfast',  # Encoding speed and compression rate
        '-c:a', 'aac',  # Audio codec
        '-y',  # Overwrite output files without asking
        mp4_file_path  # Output file path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Conversion successful: {mp4_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        raise


@app.route('/api/video', methods=['POST'])
def upload_videos():
    record = request.files['record']
    result = request.files['result']
    name_video = request.form.get('name_video', 'error')
    max_count = request.form.get('max', 'error')
    min_count = request.form.get('min', 'error')
    avg = request.form.get('avg', 'error')
    hive = request.form.get('hive', 'error')
    median = request.form.get('median', 'error')

    if record and max_count != 'error':
        current_datetime_db = name_video
        current_date_db, current_time_db = current_datetime_db.split(' ')
        almost_new_name_video = name_video.replace(":", "-") + "_almost"
        new_name_video = name_video.replace(":", "-")

        # lưu video
        directory_path = os.path.join('/media/data3/beehiveDATA/videos/video/', hive, current_date_db)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        file_path = os.path.join(directory_path, f"{new_name_video}.mp4")
        record.save(file_path)

        # luu result
        directory_path = os.path.join('/media/data3/beehiveDATA/videos/result/', hive, current_date_db)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        almost_file_path = os.path.join(directory_path, f"{almost_new_name_video}.mp4")
        file_path = os.path.join(directory_path, f"{new_name_video}.mp4")
        result.save(almost_file_path)
        convert_avi_to_mp4(str(almost_file_path), str(file_path))
        if os.path.exists(almost_file_path):
            os.remove(almost_file_path)

        # lưu database
        conn = sqlite3.connect('test.db')
        cur = conn.cursor()

        cur.execute("INSERT INTO bee (datetime, date, time, max, min, avg, median, video, result, hive) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (current_datetime_db, current_date_db, current_time_db, max_count, min_count, avg, median, f"{hive}/{current_date_db}/{new_name_video}.mp4", f"{hive}/{current_date_db}/{new_name_video}.mp4", hive))
        conn.commit()

        cur.close()

        return 'OK'
    else:
        return 'Không có count', 400


@app.route('/api/temphum', methods=['GET'])
def handle_temphum():
    temp = request.args.get('temp')
    hum = request.args.get('hum')

    temp = float(temp)
    hum = float(hum)

    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')

    conn = sqlite3.connect('test.db')
    cur = conn.cursor()

    cur.execute("INSERT INTO temphum (datetime, date, time, temp, hum) VALUES (?, ?, ?, ?, ?)", (current_datetime, current_date, current_time, temp, hum))
    conn.commit()
    cur.close()
    return "OK"

@app.route('/device_status/<int:hive>', methods=['POST', 'GET'])
def device_status_chart(hive):
    if hive<10:
        hive_text='0'+str(hive) 
    else:
        hive_text=str(hive)

    if request.method == 'POST':
        selected_date = request.form.get('selected-date')
    else:
        selected_date = datetime.now().strftime('%Y-%m-%d')

    with sqlite3.connect('test.db') as conn:
        cur = conn.cursor()
        query_DS_CPU_temp = """
            SELECT datetime, cpu_temp, disk_space 
            FROM device_status 
            WHERE date(datetime) = ? AND hive_id = ? 
            ORDER BY datetime ASC
        """
        cur.execute(query_DS_CPU_temp, (selected_date, hive_text))
        rows1 = cur.fetchall()

        th_times, cpu_temp, disk_space = [], [], []
        if rows1:
            for row in rows1:
                    th_times.append(row[0])
                    cpu_temp.append(float(row[1].split()[0]))  
                    disk_space.append(float(row[2].rstrip('G'))) 
        th_times_json = json.dumps(th_times)
        cpu_temp_json = json.dumps(cpu_temp)
        disk_space_json = json.dumps(disk_space)
        return render_template('device_status.html', 
                               th_times=th_times_json, 
                               cpu_temp=cpu_temp_json, 
                               disk_space=disk_space_json, 
                               selected_date=selected_date)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8008, allow_unsafe_werkzeug=True, debug=True)
#this is for reload