#include <avr/io.h>

char recibido = 0;

void setup() {
    // put your setup code here, to run once:
    Serial1.begin(9600);
    pinMode(13, OUTPUT);
}

void loop() {
    // put your main code here, to run repeatedly:
    Serial1.write(recibido);
    recibido++;
    delay(500);
}
