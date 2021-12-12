#include <TimerThree.h>
#include <TimerOne.h>

int flanco_A = 0;
int flanco_1 = 1;

void setup()
{
    pinMode(10, OUTPUT);
    pinMode(9, OUTPUT);
    Timer1.initialize(500);              // initialize timer1, and set a 1/2 second period
    Timer1.attachInterrupt(callback);  // attaches callback() as a timer overflow interrupt
    Serial.begin(9600);
}

void callback(void)
{
    if(flanco_1 == 0)
    {
        digitalWrite(10, LOW);
        flanco_1 = 1;
    }
    else
    {
        digitalWrite(10, HIGH);
        flanco_1 = 0;
    }
}


void loop()
{
    show_timerA();
}
