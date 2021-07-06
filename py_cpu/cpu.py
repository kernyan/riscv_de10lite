#! /usr/bin/env python3

import glob
from elftools.elf.elffile import ELFFile
import struct
from enum import Enum

ENTRY = 0
rname = ['x0', 'ra', 'sp', 'gp', 'tp'] + ['t%s' % i for i in [0,1,2]] \
  + ['s0', 's1'] + ['a%s' % i for i in range(8)] + ['s%s' % i for i in range(2, 12)] \
  + ['t%s' % i for i in [3,4,5,6]] + ['pc']

class Reg:
    def __init__(self):
        self.reg = [0]*33

    def __getitem__(self, key):
        return self.reg[rname.index(key)]

    def __setitem__(self, key, value):
        self.reg[rname.index(key)] = value

    def __len__(self):
        return len(self.reg)

def OffSet(addr):
  return (addr - ENTRY) // 4

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
  ADDI = 0b0010011

class CPU:
        
  def __init__(self):
    self.ins = 0
    self.ops = Ops(0)
    self.cont = True
    self.imm_r = 0

  def bits(self, s, e):
    return (self.ins >> e) & ((1 << (s - e + 1)) - 1)

  def decode(self):
    self.imm_r = (self.bits(30,21) << 1) | (self.bits(20,20) << 11) \
                | (self.bits(19,12) << 12) | (self.bits(31,31) << 20)
    
    print('opcode: %s' % bin(self.bits(6,0)))
    self.ops = Ops(self.bits(6,0))

  def execute(self):

    if self.ops == Ops.JAL:
        print('%r' % self.ops)
        reg['pc'] += self.imm_r
        rd = self.bits(11,7)
        reg[rname[rd]] = reg['pc'] + 4
        dump()
    else:
        raise Exception('Write %r' % self.ops)
    pass
    
  def step(self):
    self.ins = rom[reg['pc']]
    print('ins: %08x' % self.ins)
    self.decode()
    self.execute()
    return self.cont

rom = Rom()
cpu = CPU()
reg = Reg()

def dump():
  out = []
  for i in range(len(reg)):
    out += '%3s: %08x ' % (rname[i], reg[rname[i]])
    if (i + 1) % 4 == 0:
      out += '\n'
  print(''.join(out))
 
if __name__ == '__main__':
  for i in glob.glob('../../riscv-tests/isa/rv32ui-p-*'):
    if i.endswith('.dump'):
      continue
    print("File %s" % i)
    EFile=ELFFile(open(i,'rb'))
    dat = EFile.get_section_by_name('.text.init').data()
    for i in range(len(dat)//4):
      rom[i] = struct.unpack('<I', dat[i*4:i*4+4])[0]
    ENTRY = reg['pc'] = int(EFile.header['e_entry'])

    while cpu.step():
      pass

    exit(0)  # only process 1st file for now
