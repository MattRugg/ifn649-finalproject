#include "SensorData.hpp"

void hc05Setup();
void dhtSetup();
void ledSetup();
void dhtRead(SensorData *sensorData);
void soilRead(SensorData *sensorData);
void ledOn();
void ledOff();
void buzzerSetup();
void buzzerPlayTrack(int i);
