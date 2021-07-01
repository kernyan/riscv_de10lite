#! /bin/bash -e

if [ ! -d build ]; then
  mkdir build;
fi

cd build

riscv-none-embed-gcc -Os -march=rv32i -mabi=ilp32 -nostdlib ../src/main.c
#riscv-none-embed-objdump -d a.out
riscv-none-embed-objcopy -O binary a.out a.asm
#hexdump -C a.asm
python3 -c "import struct; dat=open('a.asm', 'rb').read(); print('\n'.join(['%08x' % c for c in struct.unpack('I'*(len(dat)//4), dat)]));" > firmware.hex

cp firmware.hex ../src/firmware.hex
cd ..

