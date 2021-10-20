## riscv_de10lite
riscv uart implementation on de10 lite FPGA board

### background
Part of project to build cpu chip to run [KernOS](https://github.com/kernyan/KernOS)

## python emulation
1. a [python riscv emulator](py_cpu/cpu.py) is first done to "extract" requirements for verilog implementation

## FPGA components
1. [uart](src/simpleuart.v)  
2. [riscv cpu](src/riscv.v)
3. [firmware](src/main.c)

## pins
1. uart receive  - PIN_V10 GPIO[0]
2. uart transmit - PIN_W10 GPIO[1]

## workflow
1. Compile using riscv toolchain src/main.c into firmware.hex
2. Compile using quartus toolchain riscv_cpu.v into riscv_cpu.sof
3. Program using quartus across jtag into de10_lite board

## compile
```bash
scripts/go.sh
```
## limitations
1. doesn't support floating point instructions
2. doesn't support unaligned load/stores

## todo
1. reimplement uart module

## reference
1. [geohot/tinygrad](https://github.com/geohot/tinygrad/tree/master/accel/fpga)
