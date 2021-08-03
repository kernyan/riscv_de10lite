#! /usr/bin/env python3

import glob
from elftools.elf.elffile import ELFFile
import struct
from enum import Enum
import pdb

DEBUG = False

def printd(str):
    if DEBUG:
        print(str)

def Dumping():
  Debug()
  if reg['pc'] > 0x800001d0:
    dump()

ENTRY = 0
MOFF = 0xFFFFFFFF
rname = ['x0', 'ra', 'sp', 'gp', 'tp'] + ['t%s' % i for i in [0,1,2]] \
  + ['s0', 's1'] + ['a%s' % i for i in range(8)] + ['s%s' % i for i in range(2, 12)] \
  + ['t%s' % i for i in [3,4,5,6]] + ['pc']

RAM = b'\x00' * 0x3000

def Debug():
    if reg['pc'] == 0x800001dc:
      pdb.set_trace()

def load(addr):
    addr -= MOFF
    return struct.unpack("<I", RAM[addr:addr+4])[0]

def store(addr, val):
    global RAM
    addr -= MOFF
    RAM = RAM[:addr] + val + RAM[addr+len(val):]

class Reg:
    def __init__(self):
        self.reg = [0]*33

    def __getitem__(self, key):
        return self.reg[rname.index(key)]

    def __setitem__(self, key, value):
        if key == 'x0':
            return
        self.reg[rname.index(key)] = value

    def __len__(self):
        return len(self.reg)

def OffSet(addr):
  return (addr - ENTRY) // 4

class Rom:
  def __init__(self):
    self.dat = {}

  def __getitem__(self, key):
    if key >= MOFF:
        return load(key)
    elif OffSet(key) > len(self.dat) or OffSet(key) < 0:
      panic("Address out of range %08x" % key)
    return self.dat[OffSet(key)]

  def __setitem__(self, key, value):
    if key < 0:
        panic("Writing to mem through register %08x %08x" % (key, value))
    else:
        self.dat[key] = value

class Ops(Enum):
  INVALID  = 0b0
  LOAD     = 0b0000011
  STORE    = 0b0100011
  OP_IMM   = 0b0010011
  OP       = 0b0110011
  AUIPC    = 0b0010111
  LUI      = 0b0110111
  BRANCH   = 0b1100011
  JALR     = 0b1100111
  JAL      = 0b1101111
  SYSTEM   = 0b1110011
  MISC_MEM = 0b0001111

class Funct3(Enum):

  # Ops.OP_IMM
  ADDI  = 0b000
  SLLI  = 0b001
  SLTI  = 0b010
  SLTIU = 0b011
  XORI  = 0b100
  SRLI  = SRAI = 0b101
  ORI   = 0b110
  ANDI  = 0b111

  # Ops.OP
  ADD  = SUB = 0b000
  SLL  = 0b001
  SLT  = 0b010
  SLTU = 0b011
  XOR  = 0b100
  SRL  = SRA = 0b101
  OR   = 0b110
  AND  = 0b111

  # Ops.BRANCH
  BEQ  = 0b000
  BNE  = 0b001
  BLT  = 0b100
  BGE  = 0b101
  BLTU = 0b110
  BGEU = 0b111

  # Ops.LOAD
  LB  = 0b000 # byte
  LH  = 0b001 # 2 byte
  LW  = 0b010 # 4 byte
  LBU = 0b100
  LHU = 0b101

  # Ops.STORE
  SB = 0b000
  SH = 0b001
  SW = 0b010

  # Ops.SYSTEM redefition of Funct3 bits
  ECALL  = 0b000
  CSRRW  = 0b001
  CSRRS  = 0b010
  CSRRC  = 0b011
  CSRRWI = 0b101
  CSRRSI = 0b110
  CSRRCI = 0b111

def panic(msg):
    dump()
    raise Exception(msg)

def se(brange, size):
    if brange & (1 << size):
        return (1 << 32) - ((1 << (size + 1)) - brange)
    return brange

def arith(Op, x, y, alt):
  ret = 0
  if Op == Funct3.ADD:
    ret = x - y if alt else x + y
  elif Op == Funct3.SLL:
    ret = x << (y & 0x1F)
  elif Op == Funct3.SLT:
    ret = Signed(x) < Signed(y)
  elif Op == Funct3.SLTU:
    ret = x < y
  elif Op == Funct3.XOR:
    ret = x ^ y
  elif Op == Funct3.SRL: # Ops.SRA if alt
    y = y & 0x1F
    ret = ((x >> y) | ((0xFFFFFFFF * (x >> 31)) << (31 - y))) if alt else (x >> y)
  elif Op == Funct3.OR:
    ret = x | y
  elif Op == Funct3.AND:
    ret = x & y
  else:
    panic('Unhandled case in arith %r' % Op)
  return ret & 0xFFFFFFFF
 

def BranchOp(Op, x, y):
  return (Op == Funct3.BNE and x != y) or \
     (Op == Funct3.BEQ and x == y) or \
     (Op == Funct3.BLT and Signed(x) < Signed(y)) or \
     (Op == Funct3.BLTU and x < y) or \
     (Op == Funct3.BGE and Signed(x) >= Signed(y)) or \
     (Op == Funct3.BGEU and x >= y)

def extend(Op, val):
    ret = 0
    if Op== Funct3.LH:
        ret = se(val & 0xFFFF, 15)
    elif Op== Funct3.LB:
        ret = se(val & 0xFF, 7)
    elif Op== Funct3.LW:
        ret = val
    elif Op== Funct3.LHU:
        ret = val & 0xFFFF
    elif Op== Funct3.LBU:
        ret = val & 0xFF
    else:
        panic('Unhandled case in extend %r' % Op)
    return ret

class CPU:
  def __init__(self):
    self.ins = 0
    self.ops = Ops(0)
    self.imm_i = 0
    self.imm_s = 0
    self.imm_b = 0
    self.imm_u = 0
    self.imm_j = 0

  def funct3(self):
    try:
        return Funct3(self.bits(14,12))
    except:
        dump()
        print('{:03b} not implemented'.format(self.bits(14,12)))
        exit(0)

  def bits(self, s, e, lshift = 0):
    return ((self.ins >> e) & ((1 << (s - e + 1)) - 1)) << lshift

  def rd(self, pos = 0):
    return self.bits(11, 7)

  def rs1(self):
    return self.bits(19, 15)

  def rs2(self):
    return self.bits(24, 20)

  def fetch(self):
    self.ins = rom[reg['pc']]

  def decode(self):
    try:
        self.ops = Ops(self.bits(6,0))
    except:
        dump()
        print('Invalid opcode {:07b}'.format(self.bits(6,0)))
        exit(0)
    self.imm_i = se(self.bits(31,20),11)
    self.imm_s = se(self.bits(31,25,5)|self.bits(11,7),11)
    self.imm_b = se(self.bits(31,31,12)|self.bits(7,7,11)|self.bits(30,25,5)|self.bits(11,8,1),12)
    self.imm_u = self.bits(31,12,12)
    self.imm_j = se(self.bits(31,31,20)|self.bits(19,12,12)|self.bits(20,20,11)|self.bits(30,21,1),19)
    printd('add: %08x ins: %08x rd: %3s opcode: %r' % (reg['pc'], self.ins, rname[self.rd()], self.ops))

  def execute(self):
    rd = self.rd()
    rs1 = self.rs1()
    rs2 = self.rs2()

    x = reg['pc'] if self.ops in [Ops.JAL, Ops.AUIPC, Ops.BRANCH] else reg[rname[rs1]]
    y = {Ops.OP_IMM   : self.imm_i,
         Ops.LOAD     : self.imm_i,
         Ops.SYSTEM   : self.imm_i,
         Ops.JALR     : self.imm_i,
         Ops.JAL      : self.imm_j,
         Ops.LUI      : self.imm_u,
         Ops.AUIPC    : self.imm_u,
         Ops.STORE    : self.imm_s,
         Ops.BRANCH   : self.imm_b,
         Ops.OP       : reg[rname[rs2]],
         Ops.MISC_MEM : 0}[self.ops]

    to_branch = self.ops in [Ops.JAL, Ops.JALR] or (self.ops == Ops.BRANCH and BranchOp(self.funct3(), reg[rname[rs1]], reg[rname[rs2]]))

    alt = self.bits(30,30) and \
          ((self.ops in [Ops.OP_IMM, Ops.OP] and self.funct3() == Funct3.SRL) \
          or (self.ops == Ops.OP and self.funct3() == Funct3.ADD))

    write_back = self.ops in \
        [Ops.JAL,
        Ops.JALR,
        Ops.OP_IMM,
        Ops.OP,
        Ops.AUIPC,
        Ops.LOAD,
        Ops.LUI]

    out = 0

    if self.ops == Ops.JAL:
        out = arith(Funct3.ADD, x, y, alt)
    elif self.ops == Ops.JALR:
        out = arith(Funct3.ADD, x, y, alt) & 0xFFFFFFFE
    elif self.ops == Ops.OP_IMM:
        out = arith(self.funct3(), x, y, alt)
    elif self.ops == Ops.AUIPC:
        out = arith(Funct3.ADD, x, y, alt)
    elif self.ops == Ops.LOAD:
        out = extend(self.funct3(), load(arith(Funct3.ADD, x, y, alt)))
    elif self.ops == Ops.STORE:
        src = (reg[rname[rs1]] + self.imm_s) & 0xFFFFFFFF
        if self.funct3() == Funct3.SH:
            store(src, struct.pack('H', reg[rname[rs2]] & 0xFFFF))
        elif self.funct3() == Funct3.SB:
            store(src, struct.pack('B', reg[rname[rs2]] & 0xFF))
        elif self.funct3() == Funct3.SW:
            store(src, struct.pack('I', reg[rname[rs2]]))
        else:
            panic('%r %r unimplemented' % (self.ops, self.funct3()))
    elif self.ops == Ops.SYSTEM:
        if self.funct3() == Funct3.ECALL:
            if reg['gp'] > 1:
                panic('Test %i failed' % reg['gp'])
        elif self.funct3() == Funct3.CSRRW and self.imm_i == (1<<32)-1024: # hack to match inst c0001073
            return False # test succeed
        else:
            # CSR not implemented
            pass
    elif self.ops == Ops.BRANCH:
        out = arith(Funct3.ADD, x, y, alt)
    elif self.ops == Ops.LUI:
        out = arith(Funct3.ADD, 0, y, alt)
    elif self.ops == Ops.MISC_MEM:
        # ignore as no memory reordering in emulation
        pass
    elif self.ops == Ops.OP:
        out = arith(self.funct3(), x, y, alt)
    else:
        panic('Write opcode %r' % self.ops)

    if write_back:
      reg[rname[rd]] = (reg['pc'] + 4) if self.ops in [Ops.JAL, Ops.JALR] else out

    if to_branch:
      reg['pc'] = out
    else:
      reg['pc'] += 4

    #Dumping()
    return True
    
  def step(self):
    self.fetch()
    self.decode()
    return self.execute()

rom = Rom()
cpu = CPU()
reg = Reg()

def Signed(val):
    if val >> 31:
        return -((1 << 32) - val)
    return val

def dump():
  out = []
  for i in range(len(reg)):
    out += '%3s: %08x ' % (rname[i], reg[rname[i]])
    if (i + 1) % 8 == 0:
      out += '\n'
  print(''.join(out))
  print('Instruction: {0:032b}'.format(cpu.ins))

if __name__ == '__main__':
  for i in sorted(glob.glob('../../riscv-tests/isa/rv32ui-p-*')):
    if i.endswith('.dump'):
      continue
    print("File %s" % i)
    EFile=ELFFile(open(i,'rb'))

    dat = EFile.get_section_by_name('.text.init').data()
    for i in range(len(dat)//4):
      rom[i] = struct.unpack('<I', dat[i*4:i*4+4])[0]

    if EFile.get_section_by_name('.data'):
        mdat = EFile.get_section_by_name('.data').data()
        MOFF = EFile.get_section_by_name('.data').header.sh_addr
        for i in range(len(mdat)//4):
          store(i*4+MOFF, mdat[i*4:i*4+4])

    ENTRY = reg['pc'] = int(EFile.header['e_entry'])

    while cpu.step():
      pass

    #exit(0)  # only process 1st file for now
