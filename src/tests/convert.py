#! /usr/bin/env python3

import glob
import struct

from elftools.elf.elffile import ELFFile

Out = []

def add_pad(text, data):
  pad_size = ((data.header.sh_addr - text.header.sh_addr)//4) - len(Out)
  for i in range(pad_size):
    Out.append('00000000')

def add_section(sec):
  global Out
  dat = sec.data()
  for i in range(len(dat)//4):
    Out.append('{:08x}'.format(struct.unpack('<I', dat[i*4:i*4+4])[0]))
  

if __name__ == '__main__':
  for F in glob.glob('raw/rv32ui-p-*'):
    dat = ELFFile(open(F,'rb'))
    section_text = dat.get_section_by_name('.text.init')
    add_section(section_text)

    if section_data := dat.get_section_by_name('.data'):
      add_pad(section_text, section_data)
      add_section(section_data)

    with open(F.split('/')[-1] + '.dat', 'w') as f:
      f.write('\n'.join(Out))
      Out = []
