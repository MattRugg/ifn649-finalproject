#include <Arduino.h>

// Pin mapping
const int ledPin = 12;

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
