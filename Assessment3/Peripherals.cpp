#include "DHT.h"
#include "SensorData.hpp"


// DHT sensor type
#define DHTTYPE DHT11   // DHT 11

// Pin mapping
const int dhtPin = 21;     // Digital pin connected to the DHT sensor
const int ledPin = 12;
const int buzzerPin = 19;
const int soilPin = 20;

// Initialises the DHT sensor
DHT dht(dhtPin, DHTTYPE);


void hc05Setup()
{
  // Set HC-05 serial baudrate in data mode
  Serial1.begin(9600);
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

void buzzerSetup()
{  
  // initialize the digital pin as an output.
  pinMode(buzzerPin, OUTPUT);
}

void buzzerPlayTrack(int iTrack)
{
  if (iTrack == 0)
  {
    tone(buzzerPin, 293, 300);
    delay(400);
    tone(buzzerPin, 293, 300);
    delay(400);
    noTone(buzzerPin);
  }
  else if (iTrack == 1)
  {  
    tone(buzzerPin, 880, 150);
    delay(160);
    tone(buzzerPin, 698, 150);
    delay(160);
    tone(buzzerPin, 784, 150);
    delay(160);
    noTone(buzzerPin);
  }
}
