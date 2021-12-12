FILENAME = main
FILENAME2 = timer
PORT = /dev/ttyUSB0
DEVICE = atmega328p
PROGRAMER = arduino
BAUD = 115200
COMPILE = avr-gcc -Wall -Os -mmcu=${DEVICE}

default: compile upload clean

compile:
	${COMPILE} -c ${FILENAME}.c -o ${FILENAME}.o
	${COMPILE} -c ${FILENAME2}.c -o ${FILENAME2}.o
	${COMPILE} -o ${FILENAME}.elf ${FILENAME}.o ${FILENAME2}.o
	avr-objcopy -j .text -j .data -O ihex ${FILENAME}.elf ${FILENAME}.hex
	avr-size --format=avr --mcu=${DEVICE} ${FILENAME}.elf

upload:
	avrdude -v -p ${DEVICE} -c ${PROGRAMER} -P ${PORT} -b ${BAUD} -U flash:w:${FILENAME}.hex:i

clean:
	rm *.o
	rm *.elf
	rm *.hex