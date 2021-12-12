#define PIN_DIR_A    8
#define PIN_SLEEP_A  10

#define PIN_DIR_B    4
#define PIN_SLEEP_B  6

void set_motores(void)
{
    pinMode(PIN_DIR_A, OUTPUT);
    pinMode(PIN_SLEEP_A, OUTPUT);
    pinMode(PIN_SLEEP_B, OUTPUT);
    pinMode(PIN_DIR_B, OUTPUT);



    sleepA(0);
    sleepB(0);

    setup_timer_1();
    setup_timer_3();

    speedA(0);
    speedB(0);
}

void speedA(uint8_t vel)
{
    set_speed_timer_1(vel);
}

void speedB(uint8_t vel)
{
    set_speed_timer_3(vel);
}

void sleepA(bool state)
{
    digitalWrite(PIN_SLEEP_A, 1 - state);
}

void sleepB(bool state)
{
    digitalWrite(PIN_SLEEP_B, 1 - state);
}

bool dirA(bool dir)
{
    digitalWrite(PIN_DIR_A, dir);
    return dir;
}

bool dirB(bool dir)
{
    digitalWrite(PIN_DIR_B, dir);
    return dir;
}



 
