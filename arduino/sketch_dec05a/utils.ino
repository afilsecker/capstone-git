void show_timerA(void)
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
