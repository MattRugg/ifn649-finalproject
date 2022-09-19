#include "BluetoothSerial.h"
#include "elapsedMillis.h"
#include "TagUtils.hpp"

BluetoothSerial SerialBT;
TagUtils tagUtils;

void setup() {
  // Initialise Bluetooth serial
  SerialBT.begin("Door1");
  Serial.begin(115200);

  // Initialise RFID reader serial
  Serial2.begin(9600);
}

void loop() {
  static elapsedMillis dataSendInterval;
  
  // read RFID serial every 100 ms to increase
  // chances of reading an entire Tag ID at once
  if (dataSendInterval > 100) {
    int nbytes = Serial2.available();
    for (int i=0; i < nbytes; i++)
    {
      char * tag = tagUtils.readTagByte(Serial2.read());
      if (tag != NULL)
      {
        Serial.println("Tag read: " + String(tag));
      }
    }
  }
  
  // put your main code here, to run repeatedly:
  SerialBT.println("Hello World");
  delay(1000);
}
