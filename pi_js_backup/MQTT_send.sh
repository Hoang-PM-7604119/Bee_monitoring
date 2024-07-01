# Địa chỉ của MQTT Broker
MQTT_BROKER="mica.edu.vn"
# Chủ đề MQTT để gửi
MQTT_TOPIC="Pi01"
current_time=$(date '+%Y-%m-%d %H:%M:%S')

# Kiểm tra trạng thái của camera sử dụng vcgencmd
CAMERA_STATUS=$(vcgencmd get_camera | grep -oP "detected=\K[0-9]+"   )

DISK_SPACE=$(df -h / | awk 'NR==2 {sub(/G/, "", $4); printf "%.0fG\n", $4}')
CPU_TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
CPU_TEMP_C=$(echo "scale=2; $CPU_TEMP/1000 " | bc)
mosquitto_pub -h $MQTT_BROKER -t $MQTT_TOPIC -m "$current_time,$CAMERA_STATUS,$DISK_SPACE,$CPU_TEMP_C do C" -p 50202
