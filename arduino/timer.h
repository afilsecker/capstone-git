#ifndef TIMER
#define TIMER

#define F_CPU      16000000UL
#define U_MAX      500
#define V_MAX      5
#define STEPS      6400
#define TOP        0xFFFFUL
#define COUNT_DOWN 50000000UL

void setup_timer_1(void);

unsigned long int calcular_count_up(int u);

unsigned short int calcular_next_OCR1x(unsigned short int current_pos, unsigned long int count_up);

unsigned short int calcular_n_vueltas(unsigned short int current_pos, unsigned long int count_up);

#endif