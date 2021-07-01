# riscv_de10lite
riscv uart implementation on de10 lite

## Background
Part of project to build cpu chip to run [KernOS](https://github.com/kernyan/KernOS)

## Board
FPGA: de10 lite

## Components
uart
riscv [picosov](https://github.com/cliffordwolf/picorv32)

## pins
uart receive  - PIN_V10 GPIO[0]
uart transmit - PIN_W10 GPIO[1]

## Workflow
1. Compile using riscv toolchain src/main.c into firmware.hex
2. Compile using quartus toolchain riscv_cpu.v into riscv_cpu.sof
3. Program using quartus across jtag into de10_lite board

## Compile
```bash
./go.sh
```
