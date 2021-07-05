#! /usr/bin/env python3

import glob
from elftools.elf.elffile import ELFFile
import struct

ROM_SIZE = 2000
memory = []
ENTRY = 0

if __name__ == '__main__':
	for i in glob.glob('riscv-tests/isa/rv32ui-p-add'):
		if i.endswith('.dump'):
			continue
		print("File %s" % i)
		File = ELFFile(open(i, 'rb'))
		for j in File.iter_sections():
			if j.name == '.text.init':
				print('Open section %s' % j.name)
				memory = j.data()
		memory = [struct.unpack('<I', memory[i*4:i*4+4])[0] for i in range(len(memory)//4)]
		#print(['%#08x' % x for x in memory[0:10]])
		ENTRY = int(File.header['e_entry'])
		#print('Entry %#08x' % ENTRY)

		
		exit(0)
