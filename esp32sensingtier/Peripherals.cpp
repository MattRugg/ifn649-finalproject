#include <Arduino.h>
#include "elapsedMillis.h"

// Pin mapping
const int ledPin = 12;
const int doorLatchPin = 18;

// How long should the latch be left on
const int latchOpenIntervalms = 1000;

// door latch state machine
static int doorState = 0; // 0 for closed; 1 for open; 2 for "keep open"

void doorLatchSetup()
{
  // initialize the digital pin as an output.
  pinMode(doorLatchPin, OUTPUT);
}

void ledSetup()
{
  // initialize the digital pin as an output.
  pinMode(ledPin, OUTPUT);
}

void ledOn()
{
  digitalWrite(ledPin, true);
}

void ledOff()
{
  digitalWrite(ledPin, false);
}

void doorLatchKeepOpen()
{
  doorState = 2;
}

void doorLatchOpen()
{
  doorState = 1;
}

void doorLatchClose()
{
  doorState = 0;
}

void doorLatchLoop()
{
  static elapsedMillis elapsedOpen;
  static int previousDoorState = 0;

  // Open the door if closed and reset timer
  if (doorState == 1 && previousDoorState == 0){
    elapsedOpen = 0;
    digitalWrite(doorLatchPin, true);
  }
  // Close the latch after latchOpenIntervalms milliseconds
  else if (doorState == 1 && elapsedOpen >= latchOpenIntervalms){
    elapsedOpen = 0;
    doorState = 0;
  }
  // Open the door if closed and reset timer
  else if (doorState == 2 && previousDoorState == 0){
    digitalWrite(doorLatchPin, true);
  }
  // Close the door
  else if (doorState == 0){
    digitalWrite(doorLatchPin, false);
  }

  previousDoorState = doorState;  
}
