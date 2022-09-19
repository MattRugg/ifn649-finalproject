class SensorData
{
  public:
    float airHumidityPercentage;
    float temperatureCelsius;
    float heatIndexCelsius;
    float soilHumidityPercentage;
  public:
    String toString()
    {
      String retValue = String(airHumidityPercentage) + ",";
      retValue += String(temperatureCelsius) + ",";
      retValue += String(heatIndexCelsius) + ",";
      retValue += String(soilHumidityPercentage);
      return retValue;
    }
    SensorData()
    {
      airHumidityPercentage = NAN;
    }
};
