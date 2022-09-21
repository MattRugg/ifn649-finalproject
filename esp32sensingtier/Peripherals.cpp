#include <Arduino.h>

// Pin mapping
const int ledPin = 12;
const int buzzerPin = 5;

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

void buzzerSetup()
{  
  // initialize the digital pin as an output.
  ledcAttachPin(buzzerPin, 0);
}

void buzzerPlayTrack(int iTrack)
{
  if (iTrack == 0)
  {
    ledcWriteTone(buzzerPin, 293);//, 300);
    delay(300);
    ledcWriteTone(buzzerPin, 293);//, 300);
    delay(400);
  }
  else if (iTrack == 1)
  {  
    ledcWriteTone(buzzerPin, 880);
    delay(150);
    ledcWriteTone(buzzerPin, 698);
    delay(150);
    ledcWriteTone(buzzerPin, 784);
    delay(150);
  }
}
