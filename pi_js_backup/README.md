*************************
Tất cả các máy pi đều có usrname/psw:  ad01/123456
*****************
Đối với máy PI
Các code dùng để quay video (record.py), xem video trực tiếp từ camera (preview.py) trong thư mục "cam"
Đối với Jetson Nano
Sử dụng  câu lệnh Nvargus( có thể tra mạng csi camera jetson nano để biết rõ lệnh) để xem và record
****************
Các profile openvpn nằm trong thư mục ovpn_profile dùng để kết nối VPN (phục vụ việc remote SSH)
Danh sách các máy sử dụng các profile nào viết tring file bee_device_ip_vpn.txt
****************
Yolov5
B1: Để sử dụng cần clone git của yolov5, cài các package, môi trường cần thiết(xem trong quyển đồ án)
B2: Chuyển các code xử lý detect (detect2_csv.py) , gửi dữ liệu về server (send.py) và file weight vào thư mục đã clone
*****************
Chú ý :tạo thư mục record để lưu các video
*****************
Các lệnh để thực thi chính :
- Quay video, xử lý, gửi dữ liệu: send_proc_send.sh
- gửi thông tin thiết bị: MQTT_send.sh
*****************
Các lệnh cronjob sử dụng crontab hiện đang dùng cho tất cả các thiết bị (một số thông tin có thể thay đổi tùy vào tên thiết bị)
crontab_backup.txt
