#include "timer.h"
#include <avr/io.h>

void setup_timer_1(void)
{
    TCCR1B |= (1 << CS12) | (0 << CS11) | (1 << CS10);  // set prescaler to 1024
    TIMSK1 |= (1 << OCIE1A);                            // enable compare match interrupt
    TIMSK1 |= (1 << TOIE1);                             // overflow interrupt
}

unsigned long int calcular_count_up(int u)
{
    // calcula el count_up segun un u en [1, U_MAX]
    unsigned long int fcpu = F_CPU;
    unsigned long int vmax = V_MAX;
    unsigned long int steps = STEPS;
    unsigned long int umax = U_MAX;
    return fcpu / ((u * vmax * steps) / umax);
}

unsigned short int calcular_next_OCR1x(unsigned short int current_pos, unsigned long int count_up)
{
    // calcula el proximo stop dentro de [1, TOP] segun la posicion de timer actual y el numero de count_up's
    unsigned long int big_aux = current_pos + count_up;
    unsigned short int next_OCR1x = big_aux % TOP;
    return next_OCR1x;
}

unsigned short int calcular_n_vueltas(unsigned short int current_pos, unsigned long int count_up)
{
    unsigned long int big_aux = current_pos + count_up;
    unsigned short int n_vueltas = big_aux / TOP;
    return n_vueltas;
}
