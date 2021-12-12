#define STEP_MOTOR_A 0

#define SUBIDA true
#define BAJADA false

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdbool.h>

#include "timer.h"

unsigned short int next_OCR1A;          // el valor que se le dará a OCR1A en un flanco de bajada
unsigned short int n_saltos_A;          // numero de saltos al timer hasta que se ejecute el flanco
unsigned short int u = 1;               // el valor de la entrada, se coloca un valor arbitrario en [1, U_MAX] al inicio
unsigned long int count_up_A;           // numero de ciclos de timer hasta que se realice un flanco de subida
unsigned short int contador_vueltas_A;  // para contar las vueltas que pasan
bool dir_A;                             // SUBIDA o BAJADA. indica si lo proximo sera un flanco de subida o bajada

void setup(void)
{
    setup_timer_1();
    DDRB |= (1 << STEP_MOTOR_A);                       // set led to output
    PORTB &= (0 << STEP_MOTOR_A);                      // led off
    OCR1A = 1;                                        // compare match
    dir_A = SUBIDA;                                   // el proximo cambio es un flanco de subida
    count_up_A = calcular_count_up(u);                // calculamos el count_up segun vel arbitraria que seteamos al principio
    n_vueltas_A = calcular_n_vueltas(0, count_up_A);  // iniciamos en 0
    contador_vueltas_A = 0;                           // iniciamos en 0
    sei();                                            // enable global interrupt
}

int main(void)
{
    setup();    // setup things
    while (1);  // dummy cycle
    return 1;   // return just because
}

ISR(TIMER1_COMPA_vect)
{
    if(dir_A == SUBIDA)
    {
        if(contador_vueltas_A >= n_vueltas_A)
        {
            contador_vueltas_A = 0;                               // reset contador
            PORTB |= (1 << STEP_MOTOR_A);                         // led on
            next_OCR1A = calcular_next_OCR1x(OCR1A, count_up_A);  // calculamos donde parar la prox vez
            n_vueltas_A = calcular_n_vueltas(OCR1A, count_up_A);  // calculamos las vueltas que tendremos que dar
            OCR1A = calcular_next_OCR1x(OCR1A, COUNT_DOWN);       // calculamos la posicion para el flanco de bajada
            dir_A = BAJADA;                                       // el prox flanco es de bajada
        }
        else
        {
            contador_vueltas_A = contador_vueltas_A + 1;  // aumentamos en 1 el contador de vueltas
        }
    }
    if(dir_A == BAJADA)
    {
        PORTB &= (0 << STEP_MOTOR_A);  // led off
        OCR1A = next_OCR1A;           // colocamos el stop en la posicion calculada antes
        dir_A = SUBIDA;               // ahora vamos subiendo
    }
}

ISR(TIMER1_OVF_vect)
{
    contador_vueltas_A = contador_vueltas_A + 1;
}
