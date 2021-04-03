# Simple 6502 Microprocessor Simulator in Python
#
# Copyright 2012 Steve Palmer, steve@stevewpalmer.com
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

################################
# 6502 Simulator class

import sys
import disassembler
import utilities
import array
import settings

class Simulator:

    # Bit masks for CPU flags
    DFLAG = 1
    IFLAG = 2
    CFLAG = 4
    ZFLAG = 8
    NFLAG = 16
    OFLAG = 32

    # Processor registers and memory
    _pc = 0
    _Acc = 0
    _X = 0
    _Y = 0
    _S = 0xFF
    _Flags = 0

    # Other flags
    _endpos = 0
    _trace = False
    _breaks = {}

    # Fixed size memory
    assert settings.MEMORY_SIZE < 0x10000
    _mem = array.array('B', [0] * settings.MEMORY_SIZE)

    # Copy the code into memory at offset BASE_PC
    def __init__(self, code):
        index = settings.BASE_PC
        for byt in code:
            self._mem[index] = byt
            index += 1
        self._endpos = index

    # Run the code from offset BASE_PC
    def run(self, trace):
        self._pc = settings.BASE_PC
        self._trace = trace
        dis = disassembler.Disassembler()
        while self._pc < self._endpos:
            if self._trace or self._pc in self._breaks:
                self._trace = True
                dis.disassemble_line(self._mem, self._pc)
                self.traceCPU()
                if not self.traceStep(dis):
                    return
            opcode = self._mem[self._pc]
            self._pc += 1
            self.execute[opcode](self)

    ################################
    # Trace - dump after each step

    def traceCPU(self):
        print ("PC:{0:04X} A:{1:02X} X:{2:02X} Y:{3:02X} SP:{4:04X} D{5} C{6} I{7} N{8} Z{9} O{10}".format(self._pc, self._Acc, self._X, self._Y, 0x100 + self._S, self.DFlag(), self.CFlag(), self.IFlag(), self.NFlag(), self.ZFlag(), self.OFlag()))

    def traceStep(self, dis):
        off = self._pc
        while True:
            global input
            try:
                input = raw_input
            except NameError:
                pass
            str = input("Step:")
            str = str.strip().lower()
            if str == "":
                break
            if str == "bl":
                for addr in self._breaks.keys():
                    print (hex(addr))
                continue
            if str.startswith("d"):
                try:
                    addr = int(str[1:], 16)
                    if addr in self._breaks:
                        del self._breaks[addr]
                    else:
                        print ("No breakpoint set at " + hex(addr))
                except:
                    print ("Invalid breakpoint")
                continue
            if str.startswith("b"):
                try:
                    addr = int(str[1:], 16)
                    self._breaks[addr] = 1
                except:
                    print ("Invalid breakpoint")
                continue
            if str == "q" or str == "quit":
                return False
            if str == "l" or str == "list":
                line = 0
                while line < 5 and off < len(self._mem):
                    off = dis.disassemble_line(self._mem, off)
                    line += 1
                continue
            if str == "r" or str == "restart":
                print ("Restarting...")
                self._pc = 0
                return True
            if str == "c" or str == "continue":
                self._trace = False
                return True
            if str == "h" or str == "help" or str == "?":
                print (" b addr      : set a breakpoint at addr")
                print (" bl          : list all breakpoints")
                print (" c, continue : run from current instruction")
                print (" d addr      : delete the breakpoint at addr")
                print (" l, list     : list next 5 instructions")
                print (" q, quit     : exit program")
                print (" r, restart  : restart program")
                print (" [Enter]     : step to next instruction")
                continue
            print ("Unknown command: " + str)
            continue
        return True

    ################################
    # Processor flag management

    def setFlagsFromOp(self, r):
        self.setZFlag(r == 0)
        self.setNFlag(r & 0x80)

    def setIFlag(self, r):
        if r:
            self._Flags |= self.IFLAG
        else:
            self._Flags &= ~self.IFLAG

    def setDFlag(self, r):
        if r:
            self._Flags |= self.DFLAG
        else:
            self._Flags &= ~self.DFLAG

    def setOFlag(self, r):
        if r:
            self._Flags |= self.OFLAG
        else:
            self._Flags &= ~self.OFLAG
        
    def setCFlag(self, r):
        if r:
            self._Flags |= self.CFLAG
        else:
            self._Flags &= ~self.CFLAG
        
    def setZFlag(self, r):
        if r:
            self._Flags |= self.ZFLAG
        else:
            self._Flags &= ~self.ZFLAG
        
    def setNFlag(self, r):
        if r:
            self._Flags |= self.NFLAG
        else:
            self._Flags &= ~self.NFLAG
        
    def DFlag(self):
        return 1 if (self._Flags & self.DFLAG) else 0
        
    def OFlag(self):
        return 1 if (self._Flags & self.OFLAG) else 0
        
    def CFlag(self):
        return 1 if (self._Flags & self.CFLAG) else 0
        
    def IFlag(self):
        return 1 if (self._Flags & self.IFLAG) else 0
        
    def ZFlag(self):
        return 1 if (self._Flags & self.ZFLAG) else 0
        
    def NFlag(self):
        return 1 if (self._Flags & self.NFLAG) else 0

    ################################
    # Execution utilities

    def validateAddress(self, p):
        if p < 0 or p >= settings.MEMORY_SIZE:
            print ("!Address reference overflow: ${0:04X}".format(p))
            sys.exit()
    
    def signExtend(self, r):
        return r if r < 0x80 else r - 0x100

    def storeMem8(self, off, v):
        p = (self._mem[self._pc] + off) & 0xFF
        self.validateAddress(p)
        self._mem[p] = v

    def storeMem16(self, off, v):
        p = self._mem[self._pc] + (0x100 * self._mem[self._pc + 1]) + off
        self.validateAddress(p)
        self._mem[p] = v
        
    def stackPush8(self, v):
        self._mem[0x100 + self._S] = v
        self._S -= 1
        
    def stackPush16(self, v):
        self._mem[0x100 + self._S] = v & 0xFF
        self._mem[0x100 + self._S - 1] = (v >> 8) & 0xFF
        self._S -= 2

    def stackPop8(self):
        self._S += 1
        return self._mem[0x100 + self._S]

    def stackPop16(self):
        self._S += 2
        return self._mem[0x100 + self._S] + (0x100 * self._mem[0x100 + self._S - 1])
        
    def storeMemIndexedIndirect(self, off, v):
        p = self._mem[self._pc]
        self.validateAddress(p)
        addr = self._mem[p + off] + (0x100 * self._mem[p + off + 1])
        self.validateAddress(addr)
        self._mem[addr] = v
        
    def storeMemIndirectIndexed(self, off, v):
        p = self._mem[self._pc]
        self.validateAddress(p)
        addr = self._mem[p, 0] + (0x100 * self._mem[p + 1])
        self.validateAddress(addr)
        self._mem[addr + off] = v
        
    def readMem8(self, off):
        p = (self._mem[self._pc] + off) & 0xFF
        self.validateAddress(p)
        return self._mem[p]
        
    def readMem16(self, off):
        p = self._mem[self._pc] + (0x100 * self._mem[self._pc + 1]) + off
        self.validateAddress(p)
        return self._mem[p]
        
    def readMemIndexedIndirect(self, off):
        p = self._mem[self._pc]
        self.validateAddress(p)
        addr = self._mem[p + off] + (0x100 * self._mem[p + off + 1])
        self.validateAddress(addr)
        return self._mem[addr]
        
    def readMemIndirectIndexed(self, off):
        p = self._mem[self._pc]
        self.validateAddress(p)
        addr = self._mem[p] + (0x100 * self._mem[p + 1])
        self.validateAddress(addr)
        return self._mem[addr + off]

    def addNumbers(self, a, b):
        tmp = a + b + (1 if self.CFlag() else 0)
        if not self.DFlag():
            self.setCFlag(tmp > 0xFF)
            self.setOFlag(a < 128 and b < 128 and tmp >= 128)
        else:
            if tmp & 0x0F > 0x09:
                tmp = tmp + 0x06
            if tmp & 0xF0 > 0x90:
                tmp = tmp + 0x60
            self.setCFlag(tmp > 0x99)
        return tmp & 0xFF
        
    def subNumbers(self, a, b):
        tmp = a - b - (0 if self.CFlag() else 1)
        if not self.DFlag():
            self.setCFlag(tmp <= 0xFF)
            self.setOFlag(a < 128 and b < 128 and tmp >= 128)
        else:
            if tmp & 0x0F > 0x09:
                tmp = tmp + 0x06
            if tmp & 0xF0 > 0x90:
                tmp = tmp + 0x60
            self.setCFlag(tmp > 0x99)
        return tmp & 0xFF

    ################################
    # Opcode emulation starts here

    def exeADCImm(self):
        self._Acc = self.addNumbers(self._Acc, self._mem[self._pc])
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeADCZPage(self):
        self._Acc = self.addNumbers(self._Acc, self.readMem8(0))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeADCZPageX(self):
        self._Acc = self.addNumbers(self._Acc, self.readMem8(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeADCAbs(self):
        self._Acc = self.addNumbers(self._Acc, self.readMem16(0))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeADCAbsX(self):
        self._Acc = self.addNumbers(self._Acc, self.readMem16(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeADCAbsY(self):
        self._Acc = self.addNumbers(self._Acc, self.readMem16(self._Y))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeADCIndX(self):
        self._Acc = self.addNumbers(self._Acc, self.readMemIndexedIndirect(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeADCIndY(self):
        self._Acc = self.addNumbers(self._Acc, self.readMemIndirectIndexed(self._Y))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeANDImm(self):
        self._Acc &= self._mem[self._pc]
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeANDZPage(self):
        self._Acc &= self.readMem8(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeANDZPageX(self):
        self._Acc &= self.readMem8(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeANDAbs(self):
        self._Acc &= self.readMem16(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeANDAbsX(self):
        self._Acc &= self.readMem16(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeANDAbsY(self):
        self._Acc &= self.readMem16(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeANDIndX(self):
        self._Acc &= self.readMemIndexedIndirect(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeANDIndY(self):
        self._Acc &= self.readMemIndirectIndexed(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeASLAcc(self):
        self.setCFlag(self._Acc & 0x80)
        self._Acc = (self._Acc << 1) & 0xFE
        self.setFlagsFromOp(self._Acc)

    def exeASLZPage(self):
        tmp = self.readMem8(0)
        self.setCFlag(tmp & 0x80)
        tmp = (tmp << 1) & 0xFE
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeASLZPageX(self):
        tmp = self.readMem8(self._X)
        self.setCFlag(tmp & 0x80)
        tmp = (tmp << 1) & 0xFE
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeASLAbs(self):
        tmp = self.readMem16(0)
        self.setCFlag(tmp & 0x80)
        tmp = (tmp << 1) & 0xFE
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeASLAbsX(self):
        tmp = self.readMem16(self._X)
        self.setCFlag(tmp & 0x80)
        tmp = (tmp << 1) & 0xFE
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2
        
    def exeBCC(self):
        if not self.CFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1
        
    def exeBCS(self):
        if self.CFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeBEQ(self):
        if self.ZFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1
            
    def exeBITZPage(self):
        tmp = self.readMem8(0) & self._Acc
        self.setZFlag(tmp == 0)
        self.setNFlag(tmp & 0x80)
        self.setOFlag(tmp & 0x40)
        self._pc += 1
            
    def exeBITAbs(self):
        tmp = self.readMem16(0) & self._Acc
        self.setZFlag(tmp == 0)
        self.setNFlag(tmp & 0x80)
        self.setOFlag(tmp & 0x40)
        self._pc += 2

    def exeBMI(self):
        if self.NFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeBNE(self):
        if not self.ZFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeBPL(self):
        if not self.NFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeBRK(self):
        print ("!BRK")
        self._trace = True

    def exeBVC(self):
        if not self.OFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeBVS(self):
        if self.OFlag():
            self._pc += self.signExtend(self._mem[self._pc])
        else:
            self._pc += 1

    def exeCLC(self):
        self.setCFlag(0)

    def exeCLD(self):
        self.setDFlag(0)

    def exeCLI(self):
        self.setIFlag(0)

    def exeCLV(self):
        self.setOFlag(0)

    def exeCMPImm(self):
        self.setZFlag(self._Acc == self._mem[self._pc])
        self.setCFlag(self._Acc >= self._mem[self._pc])
        self.setNFlag(self._Acc)
        self._pc += 1

    def exeCMPZPage(self):
        tmp = self.readMem8(0)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 1

    def exeCMPZPageX(self):
        tmp = self.readMem8(self._X)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 1

    def exeCMPAbs(self):
        tmp = self.readMem16(0)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 2

    def exeCMPAbsX(self):
        tmp = self.readMem16(self._X)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 2

    def exeCMPAbsY(self):
        tmp = self.readMem16(self._Y)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 2
        
    def exeCMPIndX(self):
        tmp = self.readMemIndexedIndirect(self._X)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 1
        
    def exeCMPIndY(self):
        tmp = self.readMemIndirectIndexed(self._Y)
        self.setZFlag(self._Acc == tmp)
        self.setCFlag(self._Acc >= tmp)
        self.setNFlag(self._Acc)
        self._pc += 1
        
    def exeCPXImm(self):
        self.setZFlag(self._X == self._mem[self._pc])
        self.setCFlag(self._X >= self._mem[self._pc])
        self.setNFlag(self._X)
        self._pc += 1
        
    def exeCPXZPage(self):
        tmp = self.readMem8(0)
        self.setZFlag(self._X == tmp)
        self.setCFlag(self._X >= tmp)
        self.setNFlag(self._X)
        self._pc += 1
        
    def exeCPXAbs(self):
        tmp = self.readMem16(0)
        self.setZFlag(self._X == tmp)
        self.setCFlag(self._X >= tmp)
        self.setNFlag(self._X)
        self._pc += 2

    def exeCPYImm(self):
        self.setZFlag(self._Y == self._mem[self._pc])
        self.setCFlag(self._Y >= self._mem[self._pc])
        self.setNFlag(self._Y)
        self._pc += 1
        
    def exeCPYZPage(self):
        tmp = self.readMem8(0)
        self.setZFlag(self._Y == tmp)
        self.setCFlag(self._Y >= tmp)
        self.setNFlag(self._Y)
        self._pc += 1
        
    def exeCPYAbs(self):
        tmp = self.readMem16(0)
        self.setZFlag(self._Y == tmp)
        self.setCFlag(self._Y >= tmp)
        self.setNFlag(self._Y)
        self._pc += 2
        
    def exeDECZPage(self):
        tmp = (self.readMem8(0) - 1) & 0xFF
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeDECZPageX(self):
        tmp = (self.readMem8(self._X) - 1) & 0xFF
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeDECAbs(self):
        tmp = (self.readMem16(0) - 1) & 0xFF
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeDECAbsX(self):
        tmp = (self.readMem16(self._X) - 1) & 0xFF
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeDEX(self):
        self._X -= 1
        self._X &= 0xFF
        self.setFlagsFromOp(self._X)

    def exeDEY(self):
        self._Y -= 1
        self._Y &= 0xFF
        self.setFlagsFromOp(self._Y)

    def exeEORImm(self):
        self._Acc ^= self._mem[self._pc]
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeEORZPage(self):
        self._Acc ^= self.readMem8(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeEORZPageX(self):
        self._Acc ^= self.readMem8(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeEORAbs(self):
        self._Acc ^= self.readMem16(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeEORAbsX(self):
        self._Acc ^= self.readMem16(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeEORAbsY(self):
        self._Acc ^= self.readMem16(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeEORIndX(self):
        self._Acc ^= self.readMemIndexedIndirect(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeEORIndY(self):
        self._Acc ^= self.readMemIndirectIndexed(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeINCZPage(self):
        tmp = (self.readMem8(0) + 1) & 0xFF
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeINCZPageX(self):
        tmp = (self.readMem8(self._X) + 1) & 0xFF
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeINCAbs(self):
        tmp = (self.readMem16(0) + 1) & 0xFF
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeINCAbsX(self):
        tmp = (self.readMem16(self._X) + 1) & 0xFF
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeINX(self):
        self._X += 1
        self._X &= 0xFF
        self.setFlagsFromOp(self._X)

    def exeINY(self):
        self._Y += 1
        self._Y &= 0xFF
        self.setFlagsFromOp(self._Y)
        
    def exeJMP(self):
        self._pc = (self._mem[self._pc + 1] * 0x100) + self._mem[self._pc]
        
    def exeJSR(self):
        self.stackPush16(self._pc + 2)
        self._pc = (self._mem[self._pc + 1] * 0x100) + self._mem[self._pc]

    def exeLDAImm(self):
        self._Acc = self._mem[self._pc]
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeLDAZPage(self):
        self._Acc = self.readMem8(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeLDAZPageX(self):
        self._Acc = self.readMem8(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeLDAAbs(self):
        self._Acc = self.readMem16(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeLDAAbsX(self):
        self._Acc = self.readMem16(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeLDAAbsY(self):
        self._Acc = self.readMem16(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeLDAIndX(self):
        self._Acc = self.readMemIndexedIndirect(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeLDAIndY(self):
        self._Acc = self.readMemIndirectIndexed(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeLDXImm(self):
        self._X = self._mem[self._pc]
        self.setFlagsFromOp(self._X)
        self._pc += 1

    def exeLDXZPage(self):
        self._X = self.readMem8(0)
        self.setFlagsFromOp(self._X)
        self._pc += 1

    def exeLDXZPageY(self):
        self._X = self.readMem8(self._Y)
        self.setFlagsFromOp(self._X)
        self._pc += 1

    def exeLDXAbs(self):
        self._X = self.readMem16(0)
        self.setFlagsFromOp(self._X)
        self._pc += 2

    def exeLDXAbsY(self):
        self._X = self.readMem16(self._Y)
        self.setFlagsFromOp(self._X)
        self._pc += 2

    def exeLDYImm(self):
        self._Y = self._mem[self._pc]
        self.setFlagsFromOp(self._Y)
        self._pc += 1

    def exeLDYZPage(self):
        self._Y = self.readMem8(0)
        self.setFlagsFromOp(self._Y)
        self._pc += 1

    def exeLDYZPageX(self):
        self._Y = self.readMem8(self._X)
        self.setFlagsFromOp(self._Y)
        self._pc += 1

    def exeLDYAbs(self):
        self._Y = self.readMem16(0)
        self.setFlagsFromOp(self._Y)
        self._pc += 2

    def exeLDYAbsX(self):
        self._Y = self.readMem16(self._X)
        self.setFlagsFromOp(self._Y)
        self._pc += 2

    def exeLSRAcc(self):
        self.setCFlag(self._Acc & 0x01)
        self._Acc = (self._Acc >> 1) & 0x7F
        self.setFlagsFromOp(self._Acc)

    def exeLSRZPage(self):
        tmp = self.readMem8(0)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1)
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeLSRZPageX(self):
        tmp = self.readMem8(self._X)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1)
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeLSRAbs(self):
        tmp = self.readMem16(0)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1)
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeLSRAbsX(self):
        tmp = self.readMem16(self._X)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1)
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeNOP(self):
        # Do nothing
        return

    def exeORAImm(self):
        self._Acc |= self._mem[self._pc]
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exeORAZPage(self):
        self._Acc |= self.readMem8(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exeORAZPageX(self):
        self._Acc |= self.readMem8(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exeORAAbs(self):
        self._Acc |= self.readMem16(0)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2
        
    def exeORAAbsX(self):
        self._Acc |= self.readMem16(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2
        
    def exeORAAbsY(self):
        self._Acc |= self.readMem8(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 2
        
    def exeORAIndX(self):
        self._Acc |= self.readMemIndexedIndirect(self._X)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exeORAIndY(self):
        self._Acc |= self.readMemIndirectIndexed(self._Y)
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exePHA(self):
        self.stackPush8(self._Acc)
        
    def exePHP(self):
        self.stackPush8(self._Flags)
        
    def exePHX(self):
        self.stackPush8(self._X)
        
    def exePHY(self):
        self.stackPush8(self._Y)

    def exePLA(self):
        self._Acc = self.stackPop8()
        self.setFlagsFromOp(self._Acc)
        
    def exePLP(self):
        self._Flags = self.stackPop8()
        
    def exePLX(self):
        self._X = self.stackPop8()
        
    def exePLY(self):
        self._Y = self.stackPop8()

    def exeROLAcc(self):
        tmpC = self.CFlag()
        self.setCFlag(self._Acc & 0x80)
        self._Acc = ((self._Acc << 1) | (0x1 if tmpC else 0)) & 0xFF
        self.setFlagsFromOp(self._Acc)

    def exeROLZPage(self):
        tmp = self.readMem8(0)
        tmpC = self.CFlag()
        self.setCFlag(tmp & 0x80)
        tmp = ((tmp << 1) | (0x1 if tmpC else 0)) & 0xFF
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeROLZPageX(self):
        tmp = self.readMem8(self._X)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x80)
        tmp = ((tmp << 1) | (0x01 if tmpC else 0)) & 0xFF
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeROLAbs(self):
        tmp = self.readMem16(0)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x80)
        tmp = ((tmp << 1) | (0x01 if tmpC else 0)) & 0xFF
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeROLAbsX(self):
        tmp = self.readMem16(self._X)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x80)
        tmp = ((tmp << 1) | (0x01 if tmpC else 0)) & 0xFF
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeRORAcc(self):
        tmpC = CFlag(self)
        self.setCFlag(self._Acc & 0x01)
        self._Acc = (self._Acc >> 1) | (0x80 if tmpC else 0)
        self.setFlagsFromOp(self._Acc)

    def exeRORZPage(self):
        tmp = self.readMem8(0)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1) | (0x80 if tmpC else 0)
        self.storeMem8(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeRORZPageX(self):
        tmp = self.readMem8(self._X)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1) | (0x80 if tmpC else 0)
        self.storeMem8(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 1

    def exeRORAbs(self):
        tmp = self.readMem16(0)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1) | (0x80 if tmpC else 0)
        self.storeMem16(0, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeRORAbsX(self):
        tmp = self.readMem16(self._X)
        tmpC = CFlag(self)
        self.setCFlag(tmp & 0x01)
        tmp = (tmp >> 1) | (0x80 if tmpC else 0)
        self.storeMem16(self._X, tmp)
        self.setFlagsFromOp(tmp)
        self._pc += 2

    def exeRTI(self):
        self._Flags = self.stackPop8()
        self._pc = self.stackPop16()

    def exeRTS(self):
        self._pc = self.stackPop16()
        
    def exeSBCImm(self):
        self._Acc = self.subNumbers(self._Acc, self._mem[self._pc])
        self.setFlagsFromOp(self._Acc)
        self._pc += 1
        
    def exeSBCZPage(self):
        self._Acc = self.subNumbers(self._Acc, self.readMem8(0))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeSBCZPageX(self):
        self._Acc = self.subNumbers(self._Acc, self.readMem8(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeSBCAbs(self):
        self._Acc = self.subNumbers(self._Acc, self.readMem16(0))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeSBCAbsX(self):
        self._Acc = self.subNumbers(self._Acc, self.readMem16(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeSBCAbsY(self):
        self._Acc = self.subNumbers(self._Acc, self.readMem16(self._Y))
        self.setFlagsFromOp(self._Acc)
        self._pc += 2

    def exeSBCIndX(self):
        self._Acc = self.subNumbers(self._Acc, self.readMemIndexedIndirect(self._X))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeSBCIndY(self):
        self._Acc = self.subNumbers(self._Acc, self.readMemIndirectIndexed(self._Y))
        self.setFlagsFromOp(self._Acc)
        self._pc += 1

    def exeSEC(self):
        self.setCFlag(1)

    def exeSED(self):
        self.setDFlag(1)

    def exeSEI(self):
        setIFlag(1)

    def exeSTAZPage(self):
        self.storeMem8(0, self._Acc)
        self._pc += 1

    def exeSTAZPageX(self):
        self.storeMem8(self._X, self._Acc)
        self._pc += 1
        
    def exeSTAAbs(self):
        self.storeMem16(0, self._Acc)
        self._pc += 2
        
    def exeSTAAbsX(self):
        self.storeMem16(self._X, self._Acc)
        self._pc += 2
        
    def exeSTAAbsY(self):
        self.storeMem16(self._Y, self._Acc)
        self._pc += 2
        
    def exeSTAIndX(self):
        self.storeMemIndexedIndirect(self._X, self._Acc)
        self._pc += 1
        
    def exeSTAIndY(self):
        self.storeMemIndirectIndexed(self._Y, self._Acc)
        self._pc += 1

    def exeSTXZPage(self):
        self.storeMem8(0, self._X)
        self._pc += 1
        
    def exeSTXZPageY(self):
        self.storeMem8(self._Y, self._X)
        self._pc += 1
        
    def exeSTXAbs(self):
        self.storeMem16(0, self._X)
        self._pc += 2

    def exeSTYZPage(self):
        self.storeMem8(0, self._Y)
        self._pc += 1
        
    def exeSTYZPageX(self):
        self.storeMem8(self._X, self._Y)
        self._pc += 1
        
    def exeSTYAbs(self):
        self.storeMem16(0, self._Y)
        self._pc += 2

    def exeSYS(self):
        code = self._mem[self._pc]
        if code == 0:
            self._Acc = ord(utilities.getch())
        elif code == 1:
            sys.stdout.write(chr(self._Acc))
        self._pc += 1
        
    def exeTAX(self):
        self._X = self._Acc
        self.setFlagsFromOp(self._X)

    def exeTAY(self):
        self._Y = self._Acc
        self.setFlagsFromOp(self._Y)

    def exeTSX(self):
        self._X = self._S
        self.setFlagsFromOp(self._X)

    def exeTXA(self):
        self._Acc = self._X
        self.setFlagsFromOp(self._Acc)

    def exeTXS(self):
        self._S = self._X

    def exeTYA(self):
        self._Acc = self._Y
        self.setFlagsFromOp(self._Acc)
        
    ################################
    # Execution set

    execute = {
        0x00: exeBRK,
        0x01: exeORAIndX,
        0x05: exeORAZPage,
        0x06: exeASLZPage,
        0x08: exePHP,
        0x09: exeORAImm,
        0x0A: exeASLAcc,
        0x0D: exeORAAbs,
        0x0E: exeASLAbs,
        0x10: exeBPL,
        0x11: exeORAIndY,
        0x15: exeORAZPageX,
        0x16: exeASLZPageX,
        0x18: exeCLC,
        0x19: exeORAAbsY,
        0x1D: exeORAAbsX,
        0x1E: exeASLAbsX,
        0x20: exeJSR,
        0x21: exeANDIndX,
        0x24: exeBITZPage,
        0x25: exeANDZPage,
        0x26: exeROLZPage,
        0x28: exePLP,
        0x29: exeANDImm,
        0x2A: exeROLAcc,
        0x2C: exeBITAbs,
        0x2D: exeANDAbs,
        0x2E: exeROLAbs,
        0x30: exeBMI,
        0x31: exeANDIndY,
        0x35: exeANDZPageX,
        0x36: exeROLZPageX,
        0x38: exeSEC,
        0x39: exeANDAbsY,
        0x3D: exeANDAbsX,
        0x3E: exeROLAbsX,
        0x40: exeRTI,
        0x41: exeEORIndX,
        0x45: exeEORZPage,
        0x46: exeLSRZPage,
        0x48: exePHA,
        0x49: exeEORImm,
        0x4A: exeLSRAcc,
        0x4C: exeJMP,
        0x4D: exeEORAbs,
        0x4E: exeLSRAbs,
        0x50: exeBVC,
        0x51: exeEORIndY,
        0x55: exeEORZPageX,
        0x56: exeLSRZPageX,
        0x58: exeCLI,
        0x59: exeEORAbsY,
        0x5A: exePHY,
        0x5D: exeEORAbsX,
        0x5E: exeLSRAbsX,
        0x60: exeRTS,
        0x61: exeADCIndX,
        0x65: exeADCZPage,
        0x66: exeRORZPage,
        0x68: exePLA,
        0x69: exeADCImm,
        0x6A: exeRORAcc,
        0x6D: exeADCAbs,
        0x6E: exeRORAbs,
        0x70: exeBVS,
        0x71: exeADCIndY,
        0x75: exeADCZPageX,
        0x76: exeRORZPageX,
        0x78: exeSEI,
        0x79: exeADCAbsY,
        0x7A: exePLY,
        0x7D: exeADCAbsX,
        0x7E: exeRORAbsX,
        0x81: exeSTAIndX,
        0x84: exeSTYZPage,
        0x85: exeSTAZPage,
        0x86: exeSTXZPage,
        0x88: exeDEY,
        0x8A: exeTXA,
        0x8C: exeSTYAbs,
        0x8D: exeSTAAbs,
        0x8E: exeSTXAbs,
        0x90: exeBCC,
        0x91: exeSTAIndY,
        0x94: exeSTYZPageX,
        0x95: exeSTAZPageX,
        0x96: exeSTXZPageY,
        0x98: exeTYA,
        0x99: exeSTAAbsY,
        0x9A: exeTXS,
        0x9D: exeSTAAbsX,
        0xA0: exeLDYImm,
        0xA1: exeLDAIndX,
        0xA2: exeLDXImm,
        0xA4: exeLDYZPage,
        0xA5: exeLDAZPage,
        0xA6: exeLDXZPage,
        0xA8: exeTAY,
        0xA9: exeLDAImm,
        0xAA: exeTAX,
        0xAC: exeLDYAbs,
        0xAD: exeLDAAbs,
        0xAE: exeLDXAbs,
        0xB0: exeBCS,
        0xB1: exeLDAIndY,
        0xB4: exeLDYZPageX,
        0xB5: exeLDAZPageX,
        0xB6: exeLDXZPageY,
        0xB8: exeCLV,
        0xB9: exeLDAAbsY,
        0xBA: exeTSX,
        0xBC: exeLDYAbsX,
        0xBD: exeLDAAbsX,
        0xBE: exeLDXAbsY,
        0xC0: exeCPYImm,
        0xC1: exeCMPIndX,
        0xC4: exeCPYZPage,
        0xC5: exeCMPZPage,
        0xC6: exeDECZPage,
        0xC8: exeINY,
        0xC9: exeCMPImm,
        0xCA: exeDEX,
        0xCC: exeCPYAbs,
        0xCD: exeCMPAbs,
        0xCE: exeDECAbs,
        0xD0: exeBNE,
        0xD1: exeCMPIndY,
        0xD5: exeCMPZPageX,
        0xD6: exeDECZPageX,
        0xD8: exeCLD,
        0xD9: exeCMPAbsY,
        0xDA: exePHX,
        0xDD: exeCMPAbsX,
        0xDE: exeDECAbsX,
        0xE0: exeCPXImm,
        0xE1: exeSBCIndX,
        0xE4: exeCPXZPage,
        0xE5: exeSBCZPage,
        0xE6: exeINCZPage,
        0xE8: exeINX,
        0xE9: exeSBCImm,
        0xEA: exeNOP,
        0xEC: exeCPXAbs,
        0xED: exeSBCAbs,
        0xEE: exeINCAbs,
        0xF0: exeBEQ,
        0xF1: exeSBCIndY,
        0xF5: exeSBCZPageX,
        0xF6: exeINCZPageX,
        0xF8: exeSED,
        0xF9: exeSBCAbsY,
        0xFA: exePLX,
        0xFD: exeSBCAbsX,
        0xFE: exeINCAbsX,
        0xFF: exeSYS
        }
