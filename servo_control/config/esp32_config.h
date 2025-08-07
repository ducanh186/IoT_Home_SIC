/*
 * ESP32 Servo Control Configuration
 * Copy these settings to your main Arduino sketch
 */

// ============================
// WIFI CONFIGURATION
// ============================
const char* ssid = "VIETTEL";        // Replace with your WiFi name
const char* password = "12345678"; // Replace with your WiFi password

// ============================
// MQTT BROKER CONFIGURATION  
// ============================
const char* mqtt_broker = "10.189.169.194";   // Replace with your Raspberry Pi IP
const int mqtt_port = 1883;
const char* mqtt_username = "pi";             // MQTT username
const char* mqtt_password = "1234";      // MQTT password (change this!)

// ============================
// MQTT TOPICS
// ============================
const char* servo_cmd_topic = "home/servo/cmd";      // Commands from dashboard
const char* servo_status_topic = "home/servo/status"; // Status to dashboard

// ============================
// HARDWARE CONFIGURATION
// ============================
#define SERVO_PIN 18          // GPIO pin for servo signal
#define LED_PIN 2             // Built-in LED for status indication

// Servo limits
const int SERVO_MIN_ANGLE = 0;    // Minimum servo angle
const int SERVO_MAX_ANGLE = 180;  // Maximum servo angle
const int SERVO_DEFAULT_ANGLE = 90; // Default/home position

// ============================
// TIMING CONFIGURATION
// ============================
const unsigned long HEARTBEAT_INTERVAL = 30000;  // Heartbeat every 30 seconds
const unsigned long WIFI_RECONNECT_INTERVAL = 30000; // WiFi reconnect timeout
const unsigned long MQTT_RECONNECT_INTERVAL = 5000;  // MQTT reconnect interval

// Servo movement settings
const int SERVO_STEP_DELAY = 15;  // Delay between steps for smooth movement (ms)
const int SERVO_MAX_STEPS = 180;  // Maximum steps for movement

// ============================
// STATUS LED PATTERNS
// ============================
const int LED_WIFI_CONNECTING = 100;   // Fast blink while connecting to WiFi
const int LED_MQTT_CONNECTING = 500;   // Slow blink while connecting to MQTT
const int LED_CONNECTED = 2000;        // Slow pulse when fully connected
const int LED_ERROR = 50;              // Very fast blink on error

// ============================
// ERROR HANDLING
// ============================
const int MAX_WIFI_RETRIES = 20;       // Maximum WiFi connection attempts
const int MAX_MQTT_RETRIES = 5;        // Maximum MQTT connection attempts
const int WATCHDOG_TIMEOUT = 60000;    // System watchdog timeout (ms)

// ============================
// JSON MESSAGE LIMITS
// ============================
const size_t JSON_BUFFER_SIZE = 512;   // JSON document buffer size

// ============================
// DEVICE IDENTIFICATION
// ============================
const char* DEVICE_NAME = "ESP32_Servo_Controller";
const char* FIRMWARE_VERSION = "1.0.0";
const char* DEVICE_TYPE = "servo_controller";

// ============================
// CALIBRATION VALUES
// ============================
// Adjust these if your servo doesn't move to exact angles
const int SERVO_CALIBRATION_OFFSET = 0;  // Add/subtract degrees for calibration
const int SERVO_PULSE_MIN = 500;         // Minimum pulse width (microseconds)
const int SERVO_PULSE_MAX = 2500;        // Maximum pulse width (microseconds)

// ============================
// ADVANCED SETTINGS
// ============================
const bool ENABLE_SERIAL_DEBUG = true;   // Enable serial output for debugging
const bool ENABLE_SERVO_FEEDBACK = true; // Enable position feedback
const bool ENABLE_SMOOTH_MOVEMENT = true; // Enable smooth servo movement
const bool ENABLE_POSITION_MEMORY = true; // Remember last position on restart

// ============================
// EXAMPLE USAGE
// ============================
/*
 * 1. Copy this file content to the top of your ESP32 Arduino sketch
 * 2. Replace YOUR_WIFI_SSID and YOUR_WIFI_PASSWORD with actual values
 * 3. Replace 10.189.169.194 with your Raspberry Pi's IP address
 * 4. Change the default MQTT password for security
 * 5. Adjust servo pin if using different GPIO
 * 6. Upload to ESP32 and monitor serial output
 * 
 * Hardware connections:
 * - Servo Signal (Yellow) -> GPIO 18
 * - Servo VCC (Red) -> 5V
 * - Servo GND (Brown) -> GND
 * - Optional: LED on GPIO 2 for status indication
 */
