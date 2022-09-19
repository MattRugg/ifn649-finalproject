#include "BluetoothSerial.h"
#include "elapsedMillis.h"
#include "TagUtils.hpp"

BluetoothSerial SerialBT;
TagUtils tagUtils(TagErrorCB);

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
  // chances of reading an entire Tag ID at once.
  // Not a problem if that doesn't happen, as the
  // TagUtils has a state machine to parse the
  // incoming bytestream
  if (dataSendInterval > 100) {
    int nbytes = Serial2.available();
    for (int i=0; i < nbytes; i++)
    {
      char * tag = tagUtils.readTagByte(Serial2.read());
      if (tag != NULL)
      {
        Serial.println("Tag read: " + String(tag));

        // Send a message upstream via Bluetooth to indicate
        // a tag has been swiped
        SerialBT.println("TAGSWIPE," + String(tag));
      }
    }
  }
}

void TagErrorCB(String error)
{
  Serial.println("Tag error: " + error);
}
