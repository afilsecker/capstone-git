#include <avr/io.h>

#define TIMER_1_A_OUT 5
#define TIMER_3_A_OUT 6


#define TOP 65535

void simple_start_timers(void)
{
    setup_timer_1();
    setup_timer_3();
    set_speed_timer_1(255);
    set_speed_timer_3(1);
}

void setup_timer_1(void)
{
    TCCR1A = 0;
    TCCR1B = 0;
    TCCR1C = 0;
    DDRB |= (1 << TIMER_1_A_OUT);                       // set port output
    TCCR1A |= (1 << COM1A1) | (1 << COM1A0);            // set when counting up, clear when counting down
    TCCR1B |= (1 << WGM13);                             // PWM, Phase and Frequency Correct, TOP at ICR1
    TIMSK1 |= (1 << TOIE1) | (1 << OCIE1A);                             // interrupt when BOTTOM (usefull for counting steps)
}

void setup_timer_3(void)
{
    TCCR3A = 0;
    TCCR3B = 0;
    TCCR3C = 0;
    DDRC |= (1 << TIMER_3_A_OUT);                       // set port output
    TCCR3A |= (1 << COM3A1) | (1 << COM3A0);            // set when counting up, clear when counting down
    TCCR3B |= (1 << WGM33);                             // PWM, Phase and Frequency Correct, TOP at ICR3
    TIMSK3 |= (1 << TOIE3) | (1 << OCIE3A);                             // interrupt when BOTTOM (usefull for counting steps)
}

void set_speed_timer_1(uint8_t u)
{
    
    if (u == 0)  // in case we want to stop the motors
    {
        TCCR1B = 0;  // stop timer
        TCCR1B |= (1 << WGM13);                             // PWM, Phase and Frequency Correct, TOP at ICR1
    }
    else
    {
        TCCR1B |= (0 << CS12) | (0 << CS11) | (1 << CS10);     // prescaler = 1
        ICR1 = get_count(u);                                   // set top value timer
        OCR1A = ICR1 / 2;                                      // set duty cycle always 50%
    }
    
}

void set_speed_timer_3(uint8_t u)
{
    if (u == 0)  // in case we want to stop the motors
    {
        TCCR3B = 0;              // stop timer
        TCCR3B |= (1 << WGM13);  // PWM, Phase and Frequency Correct, TOP at ICR1
        // TCNT3 = 0;
        countingB = UP;
    }
    else
    {
        TCCR3B |= (0 << CS32) | (0 << CS31) | (1 << CS30);     // prescaler = 1
        ICR3 = get_count(u);                                   // set top value timer
        OCR3A = ICR3 / 2;                                      // set duty cycle always 50%
    }
}

uint16_t get_count(uint8_t u)
{
    uint16_t counts[256] = {
                 0, 54323, 46516, 40671, 36131, 32502, 29536, 27066, 24978, 23188, 21638, 20282, 19086, 18023, 17072, 16217,
    15443, 14740, 14098, 13509, 12968, 12468, 12006, 11577, 11177, 10804, 10455, 10127,  9820,  9531,  9258,  9001,
     8757,  8527,  8308,  8100,  7902,  7714,  7534,  7363,  7199,  7042,  6892,  6749,  6611,  6478,  6351,  6229,
     6111,  5998,  5889,  5784,  5682,  5584,  5489,  5398,  5309,  5224,  5141,  5060,  4982,  4907,  4833,  4762,
     4693,  4626,  4561,  4498,  4436,  4376,  4318,  4261,  4205,  4151,  4099,  4048,  3998,  3949,  3901,  3855,
     3809,  3765,  3722,  3679,  3638,  3598,  3558,  3519,  3481,  3444,  3408,  3373,  3338,  3304,  3270,  3238,
     3206,  3174,  3143,  3113,  3083,  3054,  3026,  2998,  2970,  2943,  2917,  2891,  2865,  2840,  2815,  2791,
     2767,  2743,  2720,  2698,  2675,  2653,  2632,  2611,  2590,  2569,  2549,  2529,  2509,  2490,  2471,  2452,
     2434,  2416,  2398,  2380,  2363,  2346,  2329,  2312,  2296,  2280,  2264,  2248,  2232,  2217,  2202,  2187,
     2172,  2158,  2144,  2130,  2116,  2102,  2088,  2075,  2062,  2049,  2036,  2023,  2010,  1998,  1986,  1974,
     1962,  1950,  1938,  1927,  1915,  1904,  1893,  1882,  1871,  1860,  1850,  1839,  1829,  1818,  1808,  1798,
     1788,  1778,  1769,  1759,  1749,  1740,  1731,  1722,  1712,  1703,  1694,  1686,  1677,  1668,  1660,  1651,
     1643,  1635,  1626,  1618,  1610,  1602,  1594,  1586,  1579,  1571,  1563,  1556,  1548,  1541,  1534,  1527,
     1519,  1512,  1505,  1498,  1491,  1485,  1478,  1471,  1464,  1458,  1451,  1445,  1438,  1432,  1426,  1419,
     1413,  1407,  1401,  1395,  1389,  1383,  1377,  1371,  1365,  1360,  1354,  1348,  1343,  1337,  1332,  1326,
     1321,  1315,  1310,  1305,  1300,  1294,  1289,  1284,  1279,  1274,  1269,  1264,  1259,  1254,  1249,  1245
    };
    return counts[u];
}

void show_timer1(void)
{
    Serial.print("TCCR1A: ");
    Serial.print(TCCR1A);
    Serial.print(", TCCR1B: ");
    Serial.print(TCCR1B);
    Serial.print(", TCCR1C: ");
    Serial.print(TCCR1C);
    Serial.print(", TIMSK1: ");
    Serial.print(TIMSK1);
    Serial.print(", OCR1A: ");
    Serial.print(OCR1A);
    Serial.print(", ICR1: ");
    Serial.print(ICR1);
    Serial.println();
}

void show_timer3(void)
{
    Serial.print("TCCR3A: ");
    Serial.print(TCCR3A);
    Serial.print(", TCCR3B: ");
    Serial.print(TCCR3B);
    Serial.print(", TCCR3C: ");
    Serial.print(TCCR3C);
    Serial.print(", TIMSK3: ");
    Serial.print(TIMSK3);
    Serial.print(", OCR3A: ");
    Serial.print(OCR3A);
    Serial.print(", ICR3: ");
    Serial.print(ICR3);
    Serial.println();
}
