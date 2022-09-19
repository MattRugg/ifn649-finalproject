#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

void setup() {
  // put your setup code here, to run once:
  SerialBT.begin("Door1");
  Serial.begin(115200);
  Serial2.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  SerialBT.println("Hello World");

  int nbytes = Serial2.available();
  if (nbytes > 0) {
     for (int i=0; i < nbytes; i++)
      Serial.print(Serial2.read());
  }
  
  delay(1000);
}
