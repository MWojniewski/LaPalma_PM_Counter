#include <Arduino.h>
#include <Wire.h>
#include <U8x8lib.h>
#include "RTClib.h"
#include <TinyGPS++.h>
#include <SPI.h>
#include <SD.h>
#include <SensirionI2CSen5x.h>

// SPI Hardware Pins
#define SPI_MOSI_PIN 5
#define SPI_MISO_PIN 4
#define SPI_SCK_PIN 6
#define SD_CS_PIN 7

// I2C Hardware Pins
#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9

// GPS UART Pins
#define GPS_RX_PIN 10
#define GPS_TX_PIN 20
#define GPS_BAUDRATE 9600

// Analog & UI Pins
#define BUTTON_PIN 3
#define BATTERY_READ_PIN 0

// System State Flags
bool oled_on = false;
bool button_pressed = false;
bool working_rtc = false;
bool working_sd = false;
bool pm_valid = false;

// SEN55 Environmental Data Variables
float pm1p0 = 0.0, pm2p5 = 0.0, pm4p0 = 0.0, pm10p0 = 0.0;
float ambient_humidity = 0.0, ambient_temperature = 0.0;
float voc_index = 0.0, nox_index = 0.0;

// Temporal Variables
unsigned long previousMillis = 0;
unsigned long oled_timer = 0;
float battery_voltage = -1.0;
String file_name = "/Datalog.csv";

// OLED State Machine
enum OLED_MODE {SLEEP, PM_INFO, DEBUG_INFO};
enum OLED_MODE oled_mode = SLEEP;

// Object Instantiation
void logDataToSD(bool new_file = false);
File dataFile;
U8X8_SH1106_128X64_NONAME_HW_I2C display(U8X8_PIN_NONE, I2C_SCL_PIN, I2C_SDA_PIN);
RTC_DS3231 rtc;
TinyGPSPlus gps;
HardwareSerial gpsSerial(0);
SensirionI2CSen5x sen5x;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nSTATUS: System Initialization Sequence Initiated...");

  gpsSerial.begin(GPS_BAUDRATE, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // UI Initialization
  display.begin();
  display.setPowerSave(0);
  display.setFont(u8x8_font_chroma48medium8_r);
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("La Palma SEN55");
  display.setCursor(0, 4);
  display.print("Initializing...");

  // RTC Initialization
  if (!rtc.begin()) {
    Serial.println("CRITICAL ERROR: RTC module not found! Verify I2C wiring.");
    working_rtc = false;
  } else {
    Serial.println("STATUS: RTC initialized properly.");
    working_rtc = true;
  }

  // SEN55 Initialization Protocol
  sen5x.begin(Wire);
  uint16_t error = sen5x.deviceReset();
  if (error) {
    Serial.println("CRITICAL ERROR: SEN55 reset failed.");
  }
  delay(100); 
  
  error = sen5x.startMeasurement();
  if (error) {
    Serial.println("CRITICAL ERROR: SEN55 measurement initialization failed.");
  } else {
    Serial.println("STATUS: SEN55 actively measuring.");
  }

  // SD Card Initialization Sequence
  SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN, -1);
  if (!SD.begin(SD_CS_PIN, SPI)) {
    Serial.println("CRITICAL ERROR: SD Card initialization failed!");
    working_sd = false;
  } else {
    Serial.println("STATUS: SD Card initialized.");
    working_sd = true;
    char time_file_name[40];
    
    if (working_rtc) {
      DateTime now = rtc.now();
      snprintf(time_file_name, sizeof(time_file_name), "/Data_%04d-%02d-%02d__%02d_%02d_%02d.csv", 
               now.year(), now.month(), now.day(), 
               now.hour(), now.minute(), now.second());
    } else {
      snprintf(time_file_name, sizeof(time_file_name), "/Data_rtc_error.csv");
    }
    
    file_name = String(time_file_name);
    dataFile = SD.open(file_name, FILE_APPEND);
    
    if (dataFile) {
      if (dataFile.size() == 0) {
        // Updated CSV Header for SEN55 Parameters
        dataFile.println("Timestamp,GPS_time,Latitude,Longitude,PM1.0,PM2.5,PM4.0,PM10.0,Temp_[C],Hum_[%],VOC,NOx,Battery_[V],oled_on");
      }
      dataFile.close();
      Serial.println("STATUS: Data file ready.");
    } else {
      Serial.println("CRITICAL ERROR: Could not open datalog.");
    }
  }

  Serial.println("STATUS: System ready. Awaiting environmental data.");
  display.setPowerSave(1);
}

void loop() {
  // Continuous GPS buffer parsing
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  unsigned long currentMillis = millis();
  static unsigned long lastSDUpdate = 0;

  if (currentMillis - previousMillis > 1000) {
    previousMillis = currentMillis;
    executeMeasurementCycle();
    
    if (working_sd) {
      if (currentMillis - lastSDUpdate > 120000) {
        lastSDUpdate = currentMillis;
        logDataToSD(true);
      } else {
        logDataToSD();
      }
    }
    Serial.println("STATUS: Measurement cycle completed.");
  }

  // Mechanical Button Debounce Logic
  static unsigned long lastDebounceTime = 0;
  if (digitalRead(BUTTON_PIN) == LOW && !button_pressed) {
    if (currentMillis - lastDebounceTime > 50) {
      button_pressed = true;
      oled_timer = currentMillis;
      
      if (oled_on) {
        oled_mode = (oled_mode == PM_INFO) ? DEBUG_INFO : PM_INFO;
        display.clearDisplay();
        Serial.println("UI: OLED mode toggled.");
      } else {
        oled_on = true;
        display.setPowerSave(0);
        oled_mode = PM_INFO;
        display.clearDisplay();
        Serial.println("UI: OLED awakened.");
      }
    }
  } else if (digitalRead(BUTTON_PIN) == HIGH) {
    button_pressed = false;
    lastDebounceTime = currentMillis;
  }

  // Asynchronous UI Refresh
  static unsigned long lastDisplayUpdate = 0;
  if (oled_on) {
    if (currentMillis - lastDisplayUpdate >= 1000) {
      lastDisplayUpdate = currentMillis;
      display_data();
    }
    if (currentMillis - oled_timer >= 15000) {
      oled_on = false;
      display.clearDisplay();
      display.setPowerSave(1);
      Serial.println("UI: OLED entering low-power sleep mode.");
    }
  }
}

void display_data() {
  if (oled_mode == PM_INFO) {
    display.setCursor(0, 0); display.print("SEN55 Readings:");

    display.setCursor(0, 1); display.print("PM2.5: "); display.print(pm2p5, 1); display.print("    ");
    display.setCursor(0, 2); display.print("PM10:  "); display.print(pm10p0, 1); display.print("    ");
    display.setCursor(0, 3); display.print("Temp:  "); display.print(ambient_temperature, 1); display.print("C  ");
    display.setCursor(0, 4); display.print("Hum:   "); display.print(ambient_humidity, 1); display.print("%  ");
    display.setCursor(0, 5); display.print("VOC:   "); display.print(voc_index, 0); display.print("    ");
    if (working_sd){
      display.setCursor(0, 6); display.print("SD - working"); display.print("    ");
    }
    else{
      display.setCursor(0, 6); display.print("SD ERROR"); display.print("    ");
    }
  }
  
  if (oled_mode == DEBUG_INFO) {
    char timestamp1[16] = "NO RTC DATA    ";
    char timestamp2[16] = "               ";
    
    if (working_rtc) {
      DateTime now = rtc.now();
      snprintf(timestamp1, sizeof(timestamp1), "%04d-%02d-%02d", now.year(), now.month(), now.day());
      snprintf(timestamp2, sizeof(timestamp2), "%02d:%02d:%02d ", now.hour(), now.minute(), now.second());
    }

    String latStr = gps.location.isValid() ? String(gps.location.lat(), 6) : "INVALID   ";
    String lngStr = gps.location.isValid() ? String(gps.location.lng(), 6) : "INVALID   ";

    display.setCursor(0, 0); display.print("GPS (Lat, Lng):");
    display.setCursor(0, 1); display.print(latStr); display.print("   ");
    display.setCursor(0, 2); display.print(lngStr); display.print("   ");
    
    display.setCursor(0, 3); display.print("Time & battery:");
    display.setCursor(0, 4); display.print(timestamp1);
    display.setCursor(0, 5); display.print(timestamp2);

    display.setCursor(0, 6); display.print("In [V]: "); display.print(battery_voltage); display.print("      ");
  }
}

void executeMeasurementCycle() {
  battery_voltage = analogReadMilliVolts(BATTERY_READ_PIN) * 2 / 1000.0;

  // I2C Hardware Polling for SEN55 parameters
  uint16_t error = sen5x.readMeasuredValues(
      pm1p0, pm2p5, pm4p0, pm10p0, 
      ambient_humidity, ambient_temperature, voc_index, nox_index);

  if (error) {
    pm_valid = false;
    Serial.println("HARDWARE WARNING: F-ailed to read data from SEN55.");
  } else {
    // Check if variables are valid (NaN check for initial sensor spin-up phase)
    if (isnan(pm2p5) || isnan(ambient_temperature)) {
      pm_valid = false;
    } else {
      pm_valid = true;
    }
  }
}

void logDataToSD(bool new_file) {
  char time_file_name[40];
  char timestamp[25] = "RTC_OFFLINE";
  
  if (working_rtc) {
    DateTime now = rtc.now();
    if (new_file) {
      snprintf(time_file_name, sizeof(time_file_name), "/Data_%04d-%02d-%02d__%02d_%02d_%02d.csv", 
               now.year(), now.month(), now.day(), 
               now.hour(), now.minute(), now.second());
      file_name = String(time_file_name);
      
      dataFile = SD.open(file_name, FILE_APPEND);
      if (dataFile) {
        dataFile.println("Timestamp,GPS_time,Latitude,Longitude,PM1.0,PM2.5,PM4.0,PM10.0,Temp_[C],Hum_[%],VOC,NOx,Battery_[V],oled_on");
        dataFile.close();
      }
    }
    snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02d %02d:%02d:%02d", 
             now.year(), now.month(), now.day(), 
             now.hour(), now.minute(), now.second());
  }

  String latStr = gps.location.isValid() ? String(gps.location.lat(), 6) : "INVALID";
  String lngStr = gps.location.isValid() ? String(gps.location.lng(), 6) : "INVALID";

  String gpsTimeStr = "INVALID_GPS_TIME";
  if (gps.time.isValid() && gps.date.isValid()) {
    char gpsBuffer[30];
    snprintf(gpsBuffer, sizeof(gpsBuffer), "%04d-%02d-%02d %02d:%02d:%02d", 
            gps.date.year(), gps.date.month(), gps.date.day(),
            gps.time.hour(), gps.time.minute(), gps.time.second());
    gpsTimeStr = String(gpsBuffer);
  }

  String dataString = String(timestamp) + "," + gpsTimeStr + "," +latStr + "," + lngStr + ",";
  
  if (pm_valid) {
    // Compile environmental payload
    dataString += String(pm1p0, 2) + "," + String(pm2p5, 2) + "," + 
                  String(pm4p0, 2) + "," + String(pm10p0, 2) + "," + 
                  String(ambient_temperature, 2) + "," + String(ambient_humidity, 2) + "," + 
                  String(voc_index, 1) + "," + String(nox_index, 1);
  } else {
    dataString += "ERR,ERR,ERR,ERR,ERR,ERR,ERR,ERR";
  }

  dataString += "," + String(battery_voltage);
  dataString += "," + String(oled_on);

  dataFile = SD.open(file_name, FILE_APPEND);
  if (dataFile) {
    dataFile.println(dataString);
    dataFile.close();
    
    Serial.print("TELEMETRY LOGGED: ");
    Serial.println(dataString);
  } else {
    Serial.println("CRITICAL ERROR: Data write operation failed.");
  }
}