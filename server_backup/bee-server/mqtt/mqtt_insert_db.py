import random
import sqlite3
from paho.mqtt import client as mqtt_client
broker = '127.0.1.1'
port =8002
topic = "#"
# client_id = f'subscribe-{random.randint(0, 100)}'
client_id= "insert_db2"
# Database setup
db_name = "/media/data3/home/vuhai/bee-server/test.db"
def create_connection():
    conn = sqlite3.connect(db_name)
    return conn
def insert_status(conn, datetime, camera_status, disk_space, cpu_temp, hive_id):
    insert_sql = "INSERT INTO device_status (id, datetime, camera_status, disk_space, cpu_temp, hive_id) VALUES (NULL, ?, ?, ?, ?, ?)"
    try:
        cursor = conn.cursor()
        cursor.execute(insert_sql, (datetime, camera_status, disk_space, cpu_temp, hive_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting status: {e}")
def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc,properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id,clean_session=False)
    client.on_connect = on_connect
    client.connect(broker, port,100)
    return client
def subscribe(client: mqtt_client.Client, conn):
    def on_message(client, userdata, msg):
        message = msg.payload.decode()
        topic = msg.topic
        print(f"Received `{message}` from `{topic}` topic")
        # Parse the message
        parts = message.split(',')
        datetime = parts[0]
        camera_status = parts[1]
        disk_space = parts[2]
        cpu_temp = parts[3]
        hive_id = topic[2:]  # Extract hive from the topic
        # Insert into the database
        insert_status(conn, datetime, camera_status, disk_space, cpu_temp, hive_id)
    client.subscribe(topic)
    client.on_message = on_message
def run():
    conn = create_connection()
    client = connect_mqtt()
    subscribe(client, conn)
    client.loop_forever()
if __name__ == '__main__':
    run()
