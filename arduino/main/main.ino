#include <avr/interrupt.h>
#include <stdint.h>
#include <avr/io.h>

#define UP   1
#define DOWN 2

#define BASE      0
#define VEL_A     1
#define VEL_B     2
#define CALIBRATE 3
#define SLEEP     4
#define CENTER    5

#define NOT_READY 0
#define READY     1

#define CENTER_SPEED 50

#define NONE_LIMIT   0
#define TOP_LIMIT    1
#define BOTTOM_LIMIT 2
#define LEFT_LIMIT   3
#define RIGHT_LIMIT  4

#define CALIBRATE_NONE  0
#define CALIBRATE_BETA  1
#define RETURN_BETA     2
#define CALIBRATE_ALPHA 3
#define RETURN_ALPHA    4

#define CALIBRATE_SPEED 50
#define RETURN_SPEED    50

#define POS_TO_ORIGIN_B  1800
#define POS_TO_ORIGIN_A  650

#define LEFT_DIR  0
#define RIGHT_DIR 1
#define UP_DIR    1
#define DOWN_DIR  0

#define PIN_SWITCH_B 7
#define PIN_SWITCH_A 3

#define LIMITS_A 250
#define LIMITS_B 600

#define CALIBRATE_COMPLETE 0x00
#define CENTER_REACH       0x01
#define REACH_TOP_LIMIT    0x02
#define CLEAR_TOP_LIMIT    0x03
#define REACH_BOTTOM_LIMIT 0x04
#define CLEAR_BOTTOM_LIMIT 0x05
#define REACH_RIGHT_LIMIT  0x06
#define CLEAR_RIGHT_LIMIT  0x07
#define REACH_LEFT_LIMIT   0x08
#define CLEAR_LEFT_LIMIT   0x09
#define ENTER_SLEEP_MODE   0x0a
#define CLEAR_SLEEP_MODE   0x0b
#define WARNING_AWAKE      0x0c
#define HARD_RESETED       0x0d

char recieved;
volatile int state              = BASE;
volatile int calibrate_state    = CALIBRATE_NONE;
volatile int alpha_state        = NONE_LIMIT;
volatile int beta_state         = NONE_LIMIT;
volatile int alpha_center_state = NOT_READY;
volatile int beta_center_state  = NOT_READY;

volatile int countingA = UP;
volatile int countingB = UP;

volatile int posA = 0;
volatile int posB = 0;

volatile int dir_a;
volatile int dir_b;

volatile int next_dir_a;
volatile int next_dir_b;

char hard_reset = 0xff;

void setup() {
    // put your setup code here, to run once:
    set_motores();
    pinMode(PIN_SWITCH_A, INPUT);
    pinMode(PIN_SWITCH_B, INPUT);
    pinMode(13, OUTPUT);
    digitalWrite(13, LOW);
    Serial1.begin(115200);
    sei();
    reset();
}

void loop() {
    // put your main code here, to run repeatedly:
}

void reset(void)
{
    state = SLEEP;
    sleepA(1);
    sleepB(1);
    speedA(0);
    speedB(0);
    state = SLEEP;
    calibrate_state = CALIBRATE_NONE;
    alpha_state = NONE_LIMIT;
    beta_state = NONE_LIMIT;
    alpha_center_state = NOT_READY;
    beta_center_state = NOT_READY;
    Serial1.write(HARD_RESETED);
}

void serialEvent1()
{
    recieved = Serial1.read();
    if (recieved == hard_reset)
    {
        reset();
    }
    else
    {
        switch(state)
        {
            case BASE:
                if (bitRead(recieved, 7))
                {
                    state = VEL_A;
                    next_dir_a = bitRead(recieved, 0);
                    next_dir_b = bitRead(recieved, 1);
                }
                else if (bitRead(recieved, 6))
                {
                    state = CALIBRATE;
                    calibrate_state = CALIBRATE_BETA;
                    sleepA(1);
                    speedA(0);
                    speedB(CALIBRATE_SPEED);
                    dir_b = dirB(RIGHT_DIR);
                }
                else if (bitRead(recieved, 5))
                {
                    state = SLEEP;
                    sleepA(1);
                    sleepB(1);
                    Serial1.write(ENTER_SLEEP_MODE);
                }
                else if (bitRead(recieved, 3))
                {
                    state = CENTER;
                    speedA(0);
                    speedB(0);
                    alpha_center_state = NOT_READY;
                    beta_center_state = NOT_READY;
                    if (posA == 0)
                    {
                        speedA(0);
                        alpha_center_state = READY;
                    }
                    else
                    {
                        if (posA > 0)
                        {
                            dir_a = dirA(DOWN_DIR);
                        }
                        else
                        {
                            dir_a = dirA(UP_DIR);
                        }
                        speedA(CENTER_SPEED);
                    }
                    if (posB == 0)
                    {
                        speedB(0);
                        beta_center_state = READY;
                    }
                    else
                    {
                        if (posB > 0)
                        {
                            dir_b = dirB(LEFT_DIR);
                        }
                        else
                        {
                            dir_b = dirB(RIGHT_DIR);
                        }
                        speedB(CENTER_SPEED);
                    }
                    if (alpha_center_state == READY && beta_center_state == READY)
                    {
                        state = BASE;
                        speedA(0);
                        speedB(0);
                        beta_state = NONE_LIMIT;
                        alpha_state = NONE_LIMIT;
                        Serial1.write(CENTER_REACH);
                    }
                }
                break;
    
            case VEL_A:
                if (alpha_state == TOP_LIMIT)
                {
                    if (next_dir_a == DOWN_DIR)
                    {
                        speedA(0);
                        dir_a = dirA(next_dir_a);
                        speedA(recieved);
                        alpha_state = NONE_LIMIT;
                        Serial1.write(CLEAR_TOP_LIMIT);
                    }
                    else if (next_dir_a == UP_DIR)
                    {
                        speedA(0);
                        alpha_state = TOP_LIMIT;
                    }
                    
                }
                if (alpha_state == BOTTOM_LIMIT)
                {
                    if (next_dir_a == UP_DIR)
                    {
                        speedA(0);
                        dir_a = dirA(next_dir_a);
                        speedA(recieved);
                        alpha_state = NONE_LIMIT;
                        Serial1.write(CLEAR_BOTTOM_LIMIT);
                    }
                    else if (next_dir_a == DOWN_DIR)
                    {
                        speedA(0);
                        alpha_state = BOTTOM_LIMIT;
                    }
                        
                }
                if (alpha_state == NONE_LIMIT)
                {
                    speedA(recieved);
                    dir_a = dirA(next_dir_a);
                }
                state = VEL_B;
                break;
    
            case VEL_B:
                if (beta_state == RIGHT_LIMIT)
                {
                    if (next_dir_b == LEFT_DIR)
                    {
                        speedB(0);
                        dir_b = dirB(next_dir_b);
                        speedB(recieved);
                        beta_state = NONE_LIMIT;
                        Serial1.write(CLEAR_RIGHT_LIMIT);
                    }
                    else if (next_dir_b == RIGHT_DIR)
                    {
                        speedB(0);
                        beta_state = RIGHT_LIMIT;
                    }
                    
                }
                if (beta_state == LEFT_LIMIT)
                {
                   
                    if (next_dir_b == RIGHT_DIR)
                    {
                        speedB(0);
                        dir_b = dirB(next_dir_b);
                        speedB(recieved);
                        beta_state = NONE_LIMIT;
                        Serial1.write(CLEAR_LEFT_LIMIT);
                    }
                    else if (next_dir_b == LEFT_DIR)
                    {
                        speedB(0);
                        beta_state = LEFT_LIMIT;
                    }
                        
                }
                if (beta_state == NONE_LIMIT)
                {
                    speedB(recieved);
                    dir_b = dirB(next_dir_b);
                }
                
                state = BASE;
                break;
    
            case CALIBRATE:
                break;
    
            case SLEEP:
                if (bitRead(recieved, 4))
                {
                    sleepA(0);
                    sleepB(0);
                    state = BASE;
                    Serial1.write(WARNING_AWAKE);
                }
                else if (bitRead(recieved, 6))
                {
                    state = CALIBRATE;
                    calibrate_state = CALIBRATE_BETA;
                    sleepA(1);
                    speedA(0);
                    sleepB(0);
                    speedB(CALIBRATE_SPEED);
                    dir_b = dirB(RIGHT_DIR);
                    Serial1.write(CLEAR_SLEEP_MODE);
                }
                break;
        }
    } 
}


ISR(TIMER1_COMPA_vect)
{
    if (countingA == UP)
    {
        countingA = DOWN;
        posA += dir_a * 2 - 1;
        if (state == CALIBRATE && calibrate_state == RETURN_ALPHA)
        {
            if (posA == 0)
            {
                calibrate_state = CALIBRATE_NONE;
                speedA(0);
                state = BASE;
                alpha_state = NONE_LIMIT;
                beta_state = NONE_LIMIT;
                Serial1.write(CALIBRATE_COMPLETE);
            }
        }
        if (state == BASE)
        {
            if (posA >= LIMITS_A)
            {
                speedA(0);
                alpha_state = TOP_LIMIT;
                posA = LIMITS_A;
                Serial1.write(REACH_TOP_LIMIT);
            }
            if (posA <= -LIMITS_A)
            {
                speedA(0);
                alpha_state = BOTTOM_LIMIT;
                posA = -LIMITS_A;
                Serial1.write(REACH_BOTTOM_LIMIT);
            }
        }
        if (state == CENTER)
        {
            if (posA == 0)
            {
                speedA(0);
                alpha_center_state = READY;
                if (beta_center_state == READY && alpha_center_state == READY)
                {
                    state = BASE;
                    beta_state = NONE_LIMIT;
                    alpha_state = NONE_LIMIT;
                    Serial1.write(CENTER_REACH);
                }
            }
        }
    }
}

ISR(TIMER1_OVF_vect)
{
    countingA = UP;
    if (state == CALIBRATE && calibrate_state == CALIBRATE_ALPHA)
    {
        if (!digitalRead(PIN_SWITCH_A))
        {
            speedA(RETURN_SPEED);
            dir_a = dirA(DOWN_DIR);
            calibrate_state = RETURN_ALPHA;
            posA = POS_TO_ORIGIN_A;
        }
    }
    
}

ISR(TIMER3_COMPA_vect)
{
    if (countingB == UP)
    {
        countingB = DOWN;
        posB += dir_b * 2 - 1;
        if (state == CALIBRATE && calibrate_state == RETURN_BETA)
        {
            if (posB == 0)
            {
                calibrate_state = CALIBRATE_ALPHA;
                speedB(0);
                sleepA(0);
                speedA(CALIBRATE_SPEED);
                dir_a = dirA(UP_DIR);
            }
        }
        if (state == BASE)
        {
            if (posB >= LIMITS_B)
            {
                speedB(0);
                beta_state = RIGHT_LIMIT;
                posB = LIMITS_B;
                Serial1.write(REACH_RIGHT_LIMIT);
            }
            if (posB <= -LIMITS_B)
            {
                speedB(0);
                beta_state = LEFT_LIMIT;
                posB = -LIMITS_B;
                Serial1.write(REACH_LEFT_LIMIT);
            }
        }
        if (state == CENTER)
        {
            if (posB == 0)
            {
                speedB(0);
                beta_center_state = READY;
                if (alpha_center_state == READY && beta_center_state == READY)
                {
                    state = BASE;
                    beta_state = NONE_LIMIT;
                    alpha_state = NONE_LIMIT;
                    Serial1.write(CENTER_REACH);
                }
            }
        }
    }
}

ISR(TIMER3_OVF_vect)
{
    countingB = UP;
    if (state == CALIBRATE && calibrate_state == CALIBRATE_BETA)
    {
        if (!digitalRead(PIN_SWITCH_B))
        {
            speedB(RETURN_SPEED);
            dir_b = dirB(LEFT_DIR);
            calibrate_state = RETURN_BETA;
            posB = POS_TO_ORIGIN_B;
        }
    }
}
