import 'package:flutter/material.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:workmanager/workmanager.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert'; // Import for JSON serialization
import 'package:url_launcher/url_launcher.dart';
import 'dart:async'; // Import for Timer
import 'package:connectivity_plus/connectivity_plus.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  Workmanager().initialize(callbackDispatcher, isInDebugMode: false);
  Workmanager().registerPeriodicTask(
    "1",
    "checkDevicesTask",
    frequency: Duration(minutes: 15),
  );
  runApp(MyApp());
}

// Global variable to track the last message time for each device
Map<String, DateTime> deviceLastMessageTime = {};

// Callback Dispatcher for Workmanager
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

    // Initialize the notifications plugin
    const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    final InitializationSettings initializationSettings = InitializationSettings(android: initializationSettingsAndroid);
    await flutterLocalNotificationsPlugin.initialize(initializationSettings);

    const AndroidNotificationDetails androidPlatformChannelSpecifics = AndroidNotificationDetails(
      'your_channel_id',
      'your_channel_name',
      channelDescription: 'your_channel_description',
      importance: Importance.max,
      priority: Priority.high,
      showWhen: false,
    );
    const NotificationDetails platformChannelSpecifics = NotificationDetails(android: androidPlatformChannelSpecifics);

    final currentTime = DateTime.now();
    print("Current time: $currentTime");

    // Check network connectivity
    var connectivityResult = await Connectivity().checkConnectivity();
    if (connectivityResult == ConnectivityResult.none) {
      print('No network connection available.');
      flutterLocalNotificationsPlugin.show(
        0,
        'Thiết bị thùng ong ngắt kết nối',
        'No network connection available',
        platformChannelSpecifics,
        payload: 'Default_Sound',
      );
      return Future.value(true);
    }

    // Create a unique clientId for the WorkManager task to avoid conflicts
    final mqttClient = MqttServerClient('mica.edu.vn', 'workmanager_client_${DateTime.now().millisecondsSinceEpoch}');
    mqttClient.port = 50202;
    mqttClient.logging(on: true);  // Enable detailed logging for debugging

    try {
      await mqttClient.connect();
      print('Connected to MQTT broker in WorkManager task');

      final devices = ["Pi01", "Pi02", "Pi03", "JS04"];
      final Map<String, DateTime> newDeviceLastMessageTime = {};

      // Subscribe to device topics and listen for messages
      devices.forEach((device) {
        mqttClient.subscribe(device, MqttQos.atLeastOnce);
      });

      // Listen for messages and update the map
      mqttClient.updates!.listen((List<MqttReceivedMessage<MqttMessage>> c) {
        final MqttPublishMessage recMess = c[0].payload as MqttPublishMessage;
        final String message = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        print('WorkManager - Received message: $message on topic: ${c[0].topic}');
        newDeviceLastMessageTime[c[0].topic] = DateTime.now();
      });

      // Wait for a duration to receive messages
      await Future.delayed(Duration(minutes: 2));

      // Update SharedPreferences with the latest message times
      final prefs = await SharedPreferences.getInstance();
      final lastMessageTimeMapString = json.encode(newDeviceLastMessageTime.map((key, value) => MapEntry(key, value.toIso8601String())));
      prefs.setString('deviceLastMessageTime', lastMessageTimeMapString);
      print('WorkManager - Updated SharedPreferences with latest message times');

      // Debugging: Print out newDeviceLastMessageTime
      print('WorkManager - newDeviceLastMessageTime: $newDeviceLastMessageTime');

      // Now perform the check for disconnected devices
      final storedLastMessageTimeMapString = prefs.getString('deviceLastMessageTime') ?? '{}';
      final Map<String, String> storedLastMessageTimeMap = Map<String, String>.from(json.decode(storedLastMessageTimeMapString));
      List<String> disconnectedDevices = [];

      devices.forEach((device) {
        if (!storedLastMessageTimeMap.containsKey(device) || storedLastMessageTimeMap[device]!.isEmpty) {
          print('WorkManager - Device $device has no last message time.');
          disconnectedDevices.add(device);
        }
      });

      if (disconnectedDevices.isNotEmpty) {
        String notificationMessage;
        if (disconnectedDevices.length == 1) {
          notificationMessage = 'Thiết bị ${disconnectedDevices[0]} mất kết nối';
        } else {
          notificationMessage = 'Các thiết bị ${disconnectedDevices.join(', ')} mất kết nối';
        }

        flutterLocalNotificationsPlugin.show(
          0,
          'Cảnh báo thiết bị',
          notificationMessage,
          platformChannelSpecifics,
          payload: 'Default_Sound',
        );
        print("WorkManager - Notification sent for devices: $disconnectedDevices");
      } else {
        print("WorkManager - All devices are connected.");
      }
    } catch (e) {
      print('WorkManager - Exception: $e');
      flutterLocalNotificationsPlugin.show(
        0,
        'Thiết bị thùng ong ngắt kết nối',
        'Failed to connect to MQTT broker',
        platformChannelSpecifics,
        payload: 'Default_Sound',
      );
    } finally {
      // Ensure to disconnect the client
      if (mqttClient.connectionStatus!.state == MqttConnectionState.connected) {
        mqttClient.disconnect();
        print('MQTT client disconnected.');
      }
    }

    return Future.value(true);
  });
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner :false,
      title: 'MQTT Table Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MQTTTableScreen(),
    );
  }
}

class MQTTTableScreen extends StatefulWidget {
  @override
  _MQTTTableScreenState createState() => _MQTTTableScreenState();
}

class _MQTTTableScreenState extends State<MQTTTableScreen> {
  late MqttServerClient client;
  FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();
  String broker = 'mica.edu.vn';
  int port = 50202;
  String clientId = 'mqtt_client_redmi';
  List<String> devices = ["Pi01", "Pi02", "Pi03", "JS04"]; // Your list of devices
  Map<String, Map<String, String>> devicesInfo = {}; // Stores info for all devices

  @override
  void initState() {
    super.initState();
    initializeNotifications();
    connect();
    // Load saved device status when the app starts
    loadSavedDeviceStatus();
  }

  void initializeNotifications() {
    const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    final InitializationSettings initializationSettings = InitializationSettings(android: initializationSettingsAndroid);
    flutterLocalNotificationsPlugin.initialize(initializationSettings);
  }

  Future<void> connect() async {
    client = MqttServerClient(broker, clientId);
    client.port = port;
    client.logging(on: false);

    client.onConnected = onConnected;
    client.onDisconnected = onDisconnected;
    client.onSubscribed = onSubscribed;
    client.onUnsubscribed = onUnsubscribed;
    client.onSubscribeFail = onSubscribeFail;
    client.pongCallback = pong;

    final connMessage = MqttConnectMessage()
        .withClientIdentifier(clientId)
        .startClean()
        .withWillQos(MqttQos.atLeastOnce);

    client.connectionMessage = connMessage;

    try {
      await client.connect();
      print('Connected to MQTT broker');

      // Subscribe to all device topics
      devices.forEach((device) {
        client.subscribe(device, MqttQos.atLeastOnce);
        // Initialize device info map if not already set
        devicesInfo[device] = {
          'time': '',
          'cameraStatus': '',
          'diskSpace': '',
          'cpuTemperature': '',
        };
        // Set initial last message time to 15 minutes ago
        deviceLastMessageTime[device] = DateTime.now().subtract(Duration(minutes: 15));
      });

      client.updates!.listen((List<MqttReceivedMessage<MqttMessage>> c) {
        final MqttPublishMessage recMess = c[0].payload as MqttPublishMessage;
        final String message = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        print('Received message: $message on topic: ${c[0].topic}');
        updateDeviceInfo(c[0].topic, message);
      });
    } catch (e) {
      print('Exception: $e');
      disconnect();
    }
  }

  void disconnect() {
    client.disconnect();
    print('Disconnected from MQTT broker');
  }

  void onConnected() {
    print('Connected');
  }

  void onDisconnected() {
    print('Disconnected');
    // Attempt to reconnect
    connect();
  }

  void onSubscribed(String topic) {
    print('Subscribed to $topic');
  }

  void onUnsubscribed(String? topic) {
    print('Unsubscribed from $topic');
  }

  void onSubscribeFail(String topic) {
    print('Failed to subscribe to $topic');
  }

  void pong() {
    print('Ping response client callback invoked');
  }

  void updateDeviceInfo(String topic, String message) async {
    print('Topic: $topic, Message: $message');

    // Split the message string into components
    List<String> info = message.split(',');

    print('Parsed Info: $info');

    // Update the devicesInfo map with new values for the topic
    setState(() {
      devicesInfo[topic] = {
        'time': info[0],
        'cameraStatus': info[1],
        'diskSpace': info[2],
        'cpuTemperature': info[3],
      };

      // Update the last message time for the device
      deviceLastMessageTime[topic] = DateTime.now();
      print('Updated devicesInfo: $devicesInfo');
      print('Updated deviceLastMessageTime: $deviceLastMessageTime');
    });

    // Save deviceLastMessageTime to SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    final lastMessageTimeMapString = json.encode(deviceLastMessageTime.map((key, value) => MapEntry(key, value.toIso8601String())));
    prefs.setString('deviceLastMessageTime', lastMessageTimeMapString);
    print('Saved to SharedPreferences');
  }

  void loadSavedDeviceStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final savedDevicesInfo = prefs.getString('devicesInfo') ?? '{}';
    final savedDeviceInfoMap = json.decode(savedDevicesInfo) as Map<String, dynamic>;

    setState(() {
      devicesInfo = savedDeviceInfoMap.map((key, value) => MapEntry(key, Map<String, String>.from(value)));
    });
    print('Loaded saved device info: $devicesInfo');
  }

  void _launchURL() async {
    var url = Uri.http('mica.edu.vn:50208', '');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      throw 'Could not launch $url';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Thông tin thiết bị'),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: ElevatedButton(
                onPressed: _launchURL,
                child: Text('Mở trình duyệt'),
              ),
            ),
            SizedBox(height: 10), // Add spacing between the button and table
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: [
                  DataColumn(label: Text('Thiết bị')),
                  DataColumn(label: Text('Thời gian')),
                  DataColumn(label: Text('Camera')),
                  DataColumn(label: Text('Bộ nhớ')),
                  DataColumn(label: Text('Nhiệt độ CPU')),
                ],
                rows: devices.map((device) {
                  final info = devicesInfo[device];
                  return DataRow(
                    cells: [
                      DataCell(Text(device)),
                      DataCell(Text(info?['time'] ?? '')),
                      DataCell(Text(info?['cameraStatus'] ?? '')),
                      DataCell(Text(info?['diskSpace'] ?? '')),
                      DataCell(Text(info?['cpuTemperature'] ?? '')),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    // Properly dispose of the MQTT client
    client.disconnect();
    super.dispose();
  }
}