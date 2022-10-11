#include "BluetoothSerial.h"
#include "elapsedMillis.h"
#include "TagUtils.hpp"
#include "Peripherals.hpp"
#include "Buzzer.hpp"

String whoiam = "";

BluetoothSerial SerialBT;
TagUtils tagUtils(TagErrorCB);
char btSerialBuffer[256];

void setup() {
  Serial.begin(115200);
  
  // Get Bluetooth classic MAC address
  uint64_t mac = ESP.getEfuseMac();
  uint8_t *macBytes = (uint8_t *)&mac;
    
  Serial.print("MAC addr: ");
  for (int i = 0; i < 8; i++) {
    Serial.print(macBytes[i], HEX);
    whoiam += String(macBytes[i], HEX);    
  }
  
  // Initialise Bluetooth serial
  SerialBT.begin("Door" + String(macBytes[0]) + String(macBytes[1])
    + String(macBytes[2]) + String(macBytes[3]));

  // Initialise RFID reader serial
  Serial2.begin(9600);

  // Setup peripherals
  ledSetup();
  buzzerSetup();
  doorLatchSetup();

  SerialBT.print("Hello");
}

void loop() {
  static bool inEmergencyMode = false;
  static elapsedMillis dataSendInterval;
  
  // read RFID and Bluetooth serial every 100 ms
  if (dataSendInterval > 100) {
    // reset timer
    dataSendInterval -= 100;

    // Reads RFID serial 
    int nbytes = Serial2.available();
    for (int i=0; i < nbytes; i++)
    {
      char * tag = tagUtils.readTagByte(Serial2.read());
      if (tag != NULL)
      {
        Serial.println("Tag read: " + String(tag));

        // Send a message upstream via Bluetooth to indicate
        // a tag has been swiped
        SerialBT.print("TAGSWIPE," + String(tag) + "\n");
      }
    }

    // Reads Bluetooth serial and execute actions
    static int buffCounter = 0;
    nbytes = SerialBT.available();
    if(nbytes)
    {
      for (int i = 0; i < nbytes; i++) {
        char b = SerialBT.read();
        btSerialBuffer[buffCounter] = b;
        buffCounter++;

        // TODO check for buffer boundary
        
        if (b == '\n')
        {
          btSerialBuffer[buffCounter-1] = 0;
          Serial.printf("Command rcvd BT: %s\n", btSerialBuffer);
          String command(btSerialBuffer);
          command.trim();
    
          if (inEmergencyMode)
          {
            if (command == "EMERGENCY,OFF") {
              Serial.println("Emergency off");
              buzzerTrackStop();
              inEmergencyMode = false;
              doorLatchClose();
            }
          }
          else
          {
            if (command == "ACCESS,GRANTED") {
              Serial.println("Granting access");
              buzzerPlayTrack(1);
              doorLatchOpen();
            }
            else if (command == "ACCESS,DENIED") {
              Serial.println("Access denied");
              buzzerPlayTrack(2);
            }
            else if (command == "EMERGENCY,ON") {
              Serial.println("Emergency on");
              buzzerPlayTrack(3);
              inEmergencyMode = true;
              doorLatchKeepOpen();
            }
            else if (command == "WHOAREYOU") {
              Serial.print("Who am I? " + whoiam);
              SerialBT.print("WHOIAM," + whoiam +"\n");
            }
          }
          
          // Reset command buffer
          memset(btSerialBuffer, 0, sizeof(btSerialBuffer));
          buffCounter = 0;
        }
      }
    }
  }

  buzzerLoop();
  doorLatchLoop();
}



void TagErrorCB(String error)
{
  Serial.println("Tag error: " + error);
}
