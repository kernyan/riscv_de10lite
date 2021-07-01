#include <stdint.h>
#define reg_leds (*(volatile uint32_t*)0x02000000)
#define reg_uart_clkdiv (*(volatile uint32_t*)0x02000004)
#define reg_uart_data (*(volatile uint32_t*)0x02000008)

// using macro to avoid function call, since stack isn't set up
#define DELAY(i)              \
  asm ("lui t0, 0x100\n"      \
       "lop"#i":"             \
       "addi t0,t0,-0x1\n"    \
       "bne t0,zero,lop"#i"\n"\
       ::);


int main() {
  // 50 mhz clock / 115200 = 434
  reg_uart_clkdiv = 434;
  while (1) {
    DELAY(1)
    reg_uart_data = 'h';
    DELAY(2)
    reg_uart_data = 'e';
    DELAY(3)
    reg_uart_data = 'l';
    DELAY(4)
    reg_uart_data = 'l';
    DELAY(5)
    reg_uart_data = 'o';
  }
}

