Giải thích cấu hình server:
1. Database: là file test.db có thể xem bằng "db browser for sqlite"
2. Website:
- Code thực thi để host web: "main.py" ( cụ thể breakdown từ phần code có trong báo cáo đồ án), cần cài đặt các thư viện Flask,sqlite3,...
- Thư mục template chứa các file html giao diện trang web
- Thư mục mqtt chứ code để nhận các bản tin mqtt từ các thiết bị gửi về (mqtt_insert_db.py) cần cài đặt thư viện paho.mqtt
3. MQTT:
Hiện đang dùng mosquitto để cấu hình MQTT Broker trên port 8002
Có thể config trong /etc/mosquitto/mosquitto.conf
***********
Để remote server sử dụng ssh tài khoản của thầy hải:
username/psw: vuhai / Xaj57612
***********
Để không bị ngắt lệnh sau khi thoát ssh sử dụng nohup
**********
2 code cần thực thi:
mqtt_insert_db.py : để lưu thông tin thiết bị vào database
main.py : Để host web ( hiện đang dùng port 8008)