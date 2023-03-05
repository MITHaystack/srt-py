int analogPin = A0; // or something else

int readDelay = 500;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // getting the voltage reading from the temperature sensor
  int reading = analogRead(analogPin);  

  // convert the analog reading (0 to 1023) to voltage (0 - 5V)
  float voltage = (float)reading * 5.0;
  voltage /= 1024.0;

  // print out the voltage
  Serial.print(voltage);
  Serial.println(" volts");

  // convert voltage to degree Celsius including the 500mV offset adjustment
  // float temperatureC = (voltage - 0.5) * 100;  
  // Serial.print(temperatureC); Serial.println(" degrees C");

  // // convert from Celsius to Fahrenheit and print to Omega2
  // float temperatureF = (temperatureC * 9.0 / 5.0) + 32.0;
  // Serial.print(temperatureF); Serial.println(" degrees F");

  // delay between readings since the change is gradual
  delay(readDelay);  
}
