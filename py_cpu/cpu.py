#! /usr/bin/env python3

import glob
from elftools.elf.elffile import ELFFile
import struct
from enum import Enum

ENTRY = 0
PC = 0
REG = [0]*33
rname = ['x0', 'ra', 'sp', 'gp', 'tp'] + ['t%s' % i for i in [0,1,2]] \
  + ['s0', 's1'] + ['a%s' % i for i in range(8)] + ['s%s' % i for i in range(2, 12)] \
  + ['t%s' % i for i in [3,4,5,6]] + ['pc']

def OffSet(addr):
  return addr - ENTRY

class Rom:
  def __init__(self):
    self.dat = {}

  def __getitem__(self, key):
    if OffSet(key) > len(self.dat) or OffSet(key) < 0:
      raise Exception("Address out of range %08x" % key)
    return self.dat[OffSet(key)]

  def __setitem__(self, key, value):
    self.dat[key] = value

class Ops(Enum):
  INVALID = 0b0
  JAL = 0b1101111

class CPU:
  def bits(self, s, e):
    return (self.ins >> e) & ((1 << (s - e + 1)) - 1)
    
  def __init__(self):
    self.ins = 0
    self.ops = Ops(0)
    self.cont = True

  def decode(self):
    print(bin(self.bits(6,0)))
    self.ops = Ops(self.bits(6,0))
    print('%r' % self.ops)

  def execute(self):
    pass
    
  def step(self):
    self.ins = rom[PC]
    self.decode()
    self.execute()
    return self.cont

rom = Rom()
cpu = CPU()

def dump():
  out = []
  for i in range(len(REG)):
    out += '%3s: %08x ' % (rname[i], REG[i])
    if (i + 1) % 4 == 0:
      out += '\n'
  print(''.join(out))
 
if __name__ == '__main__':
  for i in glob.glob('riscv-tests/isa/rv32ui-p-*'):
    if i.endswith('.dump'):
      continue
    print("File %s" % i)
    EFile=ELFFile(open(i,'rb'))
    dat = EFile.get_section_by_name('.text.init').data()
    for i in range(len(dat)//4):
      rom[i] = struct.unpack('<I', dat[i*4:i*4+4])[0]
    ENTRY = PC = int(EFile.header['e_entry'])

    dump()

    while cpu.step():
      pass

    exit(0)  # only process 1st file for now
