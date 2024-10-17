#include <Servo.h>

char buffer[40];
const byte numChars = 32;
char receivedChars[numChars]; // an array to store the received data
boolean inputReceived = false;
Servo servo;
int neutralPos = 30;

int sensorPinA = A6;  // The potentiometer on pin 0
int sensorPinB = A7;  // The potentiometer on pin 0
int sensorValue;

int timeStamp;
boolean presentProbe = true;
boolean endProbe = false;
boolean startRef = false;
boolean endRef = false;
int curr_time;
 
void setup() 
{
  Serial.begin(57600);
  servo.attach(2);   
  servo.write(neutralPos);
}

void recvWithEndMarker() 
{
  static byte ndx = 0;
  char endMarker = '\n';
  char rc;

  while (Serial.available() > 0 && !inputReceived) 
  {
    Serial.println("Reading");
    
    rc = Serial.read();

    if (rc != endMarker) 
    {
      receivedChars[ndx] = rc;
      ndx++;
      
      if (ndx >= numChars) 
      {
        ndx = numChars - 1;
      }
    }
    else 
    {
      receivedChars[ndx] = '\0'; // terminate the string
      ndx = 0;
      inputReceived = true;
    }
  }
}

void loop() 
{
  recvWithEndMarker();

  if (inputReceived)
  {
    Serial.println("Input received");
    curr_time = millis();
    
    //Probe
    if (presentProbe)
    {
      Serial.println("Probe on");
      
      servo.write(neutralPos + 10*4); //probe = middle of stim lvls
      timeStamp = millis();
      presentProbe = false;
      endProbe = true;
    } else if (endProbe && curr_time >= (timeStamp + 210)) //simulates delay of 210ms
    {
      Serial.println("Probe off");
      
      servo.write(neutralPos);
      endProbe = false;
      startRef = true;
    } else if (startRef && curr_time >= (timeStamp + 1210))
    {
      Serial.println("Ref on");
      
      servo.write(neutralPos + 10*atof(receivedChars)); //input 1-7
      startRef = false;
      endRef = true;
    } else if (endRef && curr_time >= (timeStamp + 1420))
    {
      Serial.println("Ref off");
      
      servo.write(neutralPos);
      endRef = false;
      presentProbe = true;
      inputReceived = false;
    } 
  }

  sensorValue = analogRead(sensorPinA) - analogRead(sensorPinB);  // read pin A0  and calc diff between signals 
  Serial.println(abs(sensorValue));         // send data to serial, abs needed since negative values fail to decode
  //sprintf(buffer, "Sensor value %i", sensorValue);
  //Serial.println(buffer);
}
