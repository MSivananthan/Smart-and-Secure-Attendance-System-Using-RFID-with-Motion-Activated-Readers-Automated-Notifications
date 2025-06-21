#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 mfrc522(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Scan your card");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial())
    return;

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  // Display on LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ID:");
  lcd.setCursor(3, 0);
  lcd.print(uid);
  lcd.setCursor(0, 1);
  lcd.print("Attendance marked");

  // Print to Serial
  Serial.println(uid);

  delay(3000);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Scan your card");
}
