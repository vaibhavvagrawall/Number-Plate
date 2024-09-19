#include <WiFi.h>
#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "ThingSpeak.h"

// WiFi credentials
const char* ssid = "realme narzo 30";
const char* password = "Adithya@1234";

// ThingSpeak settings
unsigned long myChannelNumber = 2612724;
const char* myWriteAPIKey = "OB7IOZE1SV5H78JG";

// Pins for ultrasonic sensors
const int trigPin1 = 2;
const int echoPin1 = 18;
const int trigPin2 = 4;
const int echoPin2 = 5;

// Servo motor pin
const int servoPin = 14;

// LCD settings
LiquidCrystal_I2C lcd(0x27, 16, 2);

const int Slot = 4;
int availableSlots = Slot;

int flag1 = 0;
int flag2 = 0;

WiFiClient client;
Servo myservo;

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
    retries++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connected to WiFi");
  } else {
    Serial.println("WiFi connection failed, continuing without it");
  }
  
  // Initialize ThingSpeak
  ThingSpeak.begin(client);

  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Smart Parking");
  lcd.setCursor(0, 1);
  lcd.print("System");
  delay(2000);
  lcd.clear();

  // Initialize ultrasonic sensors
  pinMode(trigPin1, OUTPUT);
  pinMode(echoPin1, INPUT);
  pinMode(trigPin2, OUTPUT);
  pinMode(echoPin2, INPUT);

  // Initialize servo motor
  myservo.attach(servoPin);
  myservo.write(100);  // Set the initial servo position (closed)
}

void loop() {
  int distance1 = calculateDistance(trigPin1, echoPin1);
  int distance2 = calculateDistance(trigPin2, echoPin2);

  // Parking entry logic
  if (distance1 < 10 && flag1 == 0) {
    if (availableSlots > 0) {
      flag1 = 1;
      if (flag2 == 0) {
        myservo.write(0);  // Open gate
        availableSlots--;
      }
    } else {
      lcd.setCursor(0, 0);
      lcd.print("    SORRY :(    ");  
      lcd.setCursor(0, 1);
      lcd.print("  Parking Full  "); 
      delay(3000);
      lcd.clear(); 
    }
  }

  // Parking exit logic
  if (distance2 < 10 && flag2 == 0) {
    flag2 = 1;
    if (flag1 == 0) {
      myservo.write(0);  // Open gate for exiting
      availableSlots++;
    }
  }

  // Close gate if both entry and exit are complete
  if (flag1 == 1 && flag2 == 1) {
    delay(1000);
    myservo.write(100);  // Close gate
    flag1 = 0;
    flag2 = 0;
  }

  // Update LCD only if available slots change
  static int lastAvailableSlots = -1;
  if (availableSlots != lastAvailableSlots) {
    lastAvailableSlots = availableSlots;
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WELCOME!");
    lcd.setCursor(0, 1);
    lcd.print("Slot Left: ");
    lcd.print(availableSlots);
  }

  // Update Serial output
  Serial.print("Available Slots: ");
  Serial.println(availableSlots);
  delay(10000);

  // Send data to ThingSpeak every 15 seconds
  static unsigned long lastUpdate = 0;
  if (millis() - lastUpdate >= 15000) {
    ThingSpeak.setField(1, availableSlots);
    ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
    lastUpdate = millis();
  }
  
  delay(500);  // Avoid rapid looping
}

// Function to calculate distance from ultrasonic sensor
int calculateDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;  // Calculate the distance in cm
  return distance;
}