#include "Peripherals.hpp"
#include <SoftwareSerial.h>

char tagBuffer[100];

// RFDI serial pins
const byte rfidRxPin = 3;
const byte rfidTxPin = 4;

// Set RFID reader SoftwareSerial
SoftwareSerial rfidSerial(rfidRxPin, rfidTxPin);

// the setup() method runs once, when the sketch starts
void setup() {

  // initialise the debug serial
  Serial.begin(9600);
  Serial.println("IFN649 - Assessment 1");

  rfidSerial.begin(9600);

  // initialise peripherals
  hc05Setup();
  /*ledSetup();
  buzzerSetup();
  rfidSetup();*/
}

void printHex(uint8_t num) {
  char hexCar[3];

  sprintf(hexCar, "%02X", num);
  Serial.print(hexCar);
}

void loop() 
{
  static elapsedMillis dataSendInterval;
  
  // fetch data and send it every 1.5 seconds
  if (dataSendInterval > 1500) {

    int bytesN = rfidSerial.available();
    if (bytesN > 0)
    {
      int i;
      rfidSerial.readBytes(tagBuffer, sizeof(tagBuffer));
      Serial.printf("received tag (%d): ", bytesN);
      for(i=0; i < bytesN; i++){
        printHex(tagBuffer[i]);
      }
      Serial.println();
    }
    else
    {
      Serial1.flush();
    }
  }
}
