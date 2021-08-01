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

ENTRY = 0
MOFF = 0xFFFFFFFF
rname = ['x0', 'ra', 'sp', 'gp', 'tp'] + ['t%s' % i for i in [0,1,2]] \
  + ['s0', 's1'] + ['a%s' % i for i in range(8)] + ['s%s' % i for i in range(2, 12)] \
  + ['t%s' % i for i in [3,4,5,6]] + ['pc']

RAM = b'\x00' * 0x3000

def Debug():
    if reg['pc'] == 0x800001c8:
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
    if self.ops == Ops.JAL:
        cur = reg['pc']
        reg['pc'] += self.imm_j
        reg[rname[rd]] = cur + 4
    elif self.ops == Ops.JALR:
        cur = reg['pc']
        reg['pc'] = (reg[rname[rs1]] + self.imm_i) & 0xFFFFFFFE
        reg[rname[rd]] = cur + 4
    elif self.ops == Ops.OP_IMM:
        if self.funct3() == Funct3.ADDI:
            if self.imm_i == 0 and rname[rd] == 'x0' and rname[rs1] == 'x0':
                pass
            elif rs1 == 0:
                reg[rname[rd]] = self.imm_i
            else:
                reg[rname[rd]] = (reg[rname[rs1]] + self.imm_i) & 0xFFFFFFFF
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLLI:
            reg[rname[rd]] = (reg[rname[rs1]] << self.bits(24,20)) & 0xFFFFFFFF
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLTI:
            reg[rname[rd]] = 1 if (Signed(reg[rname[rs1]]) < Signed(self.imm_i)) else 0
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLTIU:
            reg[rname[rd]] = 1 if (reg[rname[rs1]] < self.imm_i) else 0
            reg['pc'] += 4
        elif self.funct3() == Funct3.SRAI:
            if self.bits(30,30): # SRAI
                sb = reg[rname[rs1]] >> 31
                out = (reg[rname[rs1]] >> self.bits(24,20)) 
                out |= ((0xFFFFFFFF * sb) << (31 - self.bits(24,20))) & 0xFFFFFFFF
                reg[rname[rd]] = out
            else: #SRLI
                reg[rname[rd]] = (reg[rname[rs1]] >> self.bits(24,20))
            reg['pc'] += 4
        elif self.funct3() == Funct3.ANDI:
            reg[rname[rd]] = reg[rname[rs1]] & self.imm_i
            reg['pc'] += 4
        elif self.funct3() == Funct3.ORI:
            reg[rname[rd]] = reg[rname[rs1]] | self.imm_i
            reg['pc'] += 4
        elif self.funct3() == Funct3.XORI:
            if Signed(self.imm_i) == -1:
                reg[rname[rd]] = ~reg[rname[rs1]]
            else:
                reg[rname[rd]] = reg[rname[rs1]] ^ self.imm_i
            reg['pc'] += 4
        else:
            panic('Write {!r} Funct3: {!r}'.format(self.ops, self.funct3()))
    elif self.ops == Ops.AUIPC:
        reg[rname[rd]] = (self.imm_u + reg['pc']) & 0xFFFFFFFF
        reg['pc'] += 4
    elif self.ops == Ops.LOAD:
        src = (reg[rname[rs1]] + self.imm_i) & 0xFFFFFFFF
        if self.funct3() == Funct3.LH:
            reg[rname[rd]] = se(load(src) & 0xFFFF, 15)
            reg['pc'] += 4
        elif self.funct3() == Funct3.LB:
            reg[rname[rd]] = se(load(src) & 0xFF, 7)
            reg['pc'] += 4
        elif self.funct3() == Funct3.LW:
            reg[rname[rd]] = load(src)
            reg['pc'] += 4
        elif self.funct3() == Funct3.LHU:
            reg[rname[rd]] = load(src) & 0xFFFF
            reg['pc'] += 4
        elif self.funct3() == Funct3.LBU:
            reg[rname[rd]] = load(src) & 0xFF
            reg['pc'] += 4
        else:
            panic('%r %r unimplemented' % (self.ops, self.funct3()))
    elif self.ops == Ops.STORE:
        src = (reg[rname[rs1]] + self.imm_s) & 0xFFFFFFFF
        if self.funct3() == Funct3.SH:
            store(src, struct.pack('H', reg[rname[rs2]] & 0xFFFF))
            reg['pc'] += 4
        elif self.funct3() == Funct3.SB:
            store(src, struct.pack('B', reg[rname[rs2]] & 0xFF))
            reg['pc'] += 4
        elif self.funct3() == Funct3.SW:
            store(src, struct.pack('I', reg[rname[rs2]]))
            reg['pc'] += 4
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
        reg['pc'] += 4
    elif self.ops == Ops.BRANCH:
        Branch = False
        if self.funct3() == Funct3.BNE:
            if reg[rname[rs1]] != reg[rname[rs2]]:
                Branch = True
        elif self.funct3() == Funct3.BEQ:
            if reg[rname[rs1]] == reg[rname[rs2]]:
                Branch = True
        elif self.funct3() == Funct3.BLT:
            if Signed(reg[rname[rs1]]) < Signed(reg[rname[rs2]]):
                Branch = True
        elif self.funct3() == Funct3.BLTU:
            if reg[rname[rs1]] < reg[rname[rs2]]:
                Branch = True
        elif self.funct3() == Funct3.BGE:
            if Signed(reg[rname[rs1]]) >= Signed(reg[rname[rs2]]):
                Branch = True
        elif self.funct3() == Funct3.BGEU:
            if reg[rname[rs1]] >= reg[rname[rs2]]:
                Branch = True
        else:
            panic('Branch {!r} not implemented'.format(self.funct3()))

        if Branch:
            reg['pc'] = (reg['pc'] + self.imm_b) & 0xFFFFFFFF
        else:
            reg['pc'] += 4
    elif self.ops == Ops.LUI:
        reg[rname[rd]] = self.imm_u
        reg['pc'] += 4
    elif self.ops == Ops.MISC_MEM:
        # ignore as no memory reordering in emulation
        reg['pc'] += 4
    elif self.ops == Ops.OP:
        if self.funct3() == Funct3.XOR:
            if rname[rd] != 'x0': # not specified in spec?
                reg[rname[rd]] = reg[rname[rs1]] ^ reg[rname[rs2]]
            reg['pc'] += 4
        elif self.funct3() == Funct3.ADD:
            if self.ins >> 30: # SUB
                reg[rname[rd]] = (reg[rname[rs1]] - reg[rname[rs2]]) & 0xFFFFFFFF
            else: # ADD
                reg[rname[rd]] = (reg[rname[rs1]] + reg[rname[rs2]]) & 0xFFFFFFFF
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLL:
            reg[rname[rd]] = (reg[rname[rs1]] << (reg[rname[rs2]] & 0x1F)) & 0xFFFFFFFF
            reg['pc'] += 4
        elif self.funct3() == Funct3.SRL:
            if self.bits(30,30): # SRA
                pos = (reg[rname[rs2]] & 0x1F)
                out = reg[rname[rs1]] >> pos
                if reg[rname[rs1]] >> 31:
                    out |= (0xFFFFFFFF << (31 - pos)) & 0xFFFFFFFF
                reg[rname[rd]] = out
                reg['pc'] += 4
            else:
                reg[rname[rd]] = reg[rname[rs1]] >> (reg[rname[rs2]] & 0x1F)
                reg['pc'] += 4
        elif self.funct3() == Funct3.AND:
            reg[rname[rd]] = reg[rname[rs1]] & reg[rname[rs2]]
            reg['pc'] += 4
        elif self.funct3() == Funct3.XOR:
            reg[rname[rd]] = reg[rname[rs1]] ^ reg[rname[rs2]]
            reg['pc'] += 4
        elif self.funct3() == Funct3.OR:
            reg[rname[rd]] = reg[rname[rs1]] | reg[rname[rs2]]
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLT:
            reg[rname[rd]] = 1 if (Signed(reg[rname[rs1]]) < Signed(reg[rname[rs2]])) else 0
            reg['pc'] += 4
        elif self.funct3() == Funct3.SLTU:
            if rname[rs1] == 'x0':
                reg[rname[rd]] = 1 if reg[rname[rs2]] else 0
            else:
                reg[rname[rd]] = 1 if (reg[rname[rs1]] < reg[rname[rs2]]) else 0
            reg['pc'] += 4
        else:
            panic('Write Ops.OP %r' % self.funct3())
    else:
        panic('Write opcode %r' % self.ops)
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
