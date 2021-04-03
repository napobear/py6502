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
# 6502 Disassembler class

import settings

class Disassembler:

    # Disassemble all the code to the console
    def disassemble(self, code):
        self._code = code
        self._pc = 0
        while self._pc < len(self._code):
            self.disassemble_one()

    # Disassemble one instruction in code[] at pc offset            
    def disassemble_line(self, code, pc):
        self._code = code
        self._pc = pc
        self.disassemble_one()
        return self._pc
        
    def disassemble_one(self):
        opcode = self._code[self._pc]
        self._pc += 1
        if opcode in self.opcodes:
            args = self.opcodes[opcode]
            assert len(args) == 2
            args[1](self, args[0])
        else:
            self.outputNone(".BYTE " + hex(opcode))

    ################################
    # Output

    def signExtend(self, r):
        return r if r < 0x80 else r - 0x100

    def num8(self):
        return self._code[self._pc]

    def num16(self):
        if self._pc + 1 >= len(self._code):
            return 0
        return self._code[self._pc] + (0x100 * self._code[self._pc + 1])

    def output(self, size, str):
        str_out = []
        off = self._pc - 1   # Opcode is at PC-1 when we get here
        end = len(self._code)
        str_out.append("{0:04X}: ".format(off + settings.BASE_PC))
        str_out.append("{0:02X} ".format(self._code[off]))
        str_out.append("{0:02X} ".format(self._code[off + 1]) if size > 0 and off + 1 < end else "   ")
        str_out.append("{0:02X} ".format(self._code[off + 2]) if size > 1 and off + 2 < end else "   ")
        str_out.append(str)
        print (''.join(str_out))
        self._pc += size

    def outputNone(self, str):
        self.output(0, str)

    def outputImm(self, str):
        self.output(1, "{0} #${1:02X}".format(str, self.num8()))

    def outputZPage(self, str):
        self.output(1, "{0} ${1:02X}".format(str, self.num8()))

    def outputZPageX(self, str):
        self.output(1, "{0} ${1:02X},X".format(str, self.num8()))

    def outputZPageY(self, str):
        self.output(1, "{0} ${1:02X},Y".format(str, self.num8()))

    def outputAbs(self, str):
        self.output(2, "{0} ${1:04X}".format(str, self.num16()))

    def outputAbsX(self, str):
        self.output(2, "{0} ${1:04X},X".format(str, self.num16()))

    def outputAbsY(self, str):
        self.output(2, "{0} ${1:04X},Y".format(str, self.num16()))

    def outputIndX(self, str):
        self.output(1, "{0} (${1:02X},X)".format(str, self.num8()))

    def outputIndY(self, str):
        self.output(1, "{0} (${1:02X}),Y".format(str, self.num8()))
        
    def outputBranch(self, str):
        self.output(1, "{0} {1:04X}".format(str, self._pc + self.signExtend(self.num8())))
        
    def outputJump(self, str):
        self.output(2, "{0} {1:04X}".format(str, self.num16()))
        
    ################################
    # List of opcodes

    opcodes = {
        0x00: ("BRK", outputNone),
        0x01: ("ORA", outputIndX),
        0x05: ("ORA", outputZPage),
        0x06: ("ASL", outputZPage),
        0x08: ("PHP", outputNone),
        0x09: ("ORA", outputImm),
        0x0A: ("LDY", outputImm),
        0x0D: ("ORA", outputAbs),
        0x0E: ("ASL", outputAbs),
        0x10: ("BPL", outputBranch),
        0x11: ("ORA", outputIndY),
        0x15: ("ORA", outputZPageX),
        0x16: ("ASL", outputZPageX),
        0x18: ("CLC", outputNone),
        0x19: ("ORA", outputAbsY),
        0x1D: ("ORA", outputAbsX),
        0x1E: ("ASL", outputAbsX),
        0x20: ("JSR", outputJump),
        0x21: ("AND", outputIndX),
        0x24: ("BIT", outputZPage),
        0x25: ("AND", outputZPage),
        0x26: ("ROL", outputZPage),
        0x28: ("PLP", outputNone),
        0x29: ("AND", outputImm),
        0x2A: ("ROL", outputNone),
        0x2C: ("BIT", outputAbs),
        0x2D: ("AND", outputAbs),
        0x2E: ("ROL", outputAbs),
        0x30: ("BMI", outputBranch),
        0x31: ("AND", outputIndY),
        0x35: ("AND", outputZPageX),
        0x36: ("ROL", outputZPageX),
        0x38: ("SEC", outputNone),
        0x39: ("AND", outputAbsY),
        0x3D: ("AND", outputAbsX),
        0x3E: ("ROL", outputAbsX),
        0x40: ("RTI", outputNone),
        0x41: ("EOR", outputIndX),
        0x45: ("EOR", outputZPage),
        0x46: ("LSR", outputZPage),
        0x48: ("PHA", outputNone),
        0x49: ("EOR", outputImm),
        0x4A: ("LSR", outputNone),
        0x4C: ("JMP", outputJump),
        0x4D: ("EOR", outputAbs),
        0x4E: ("LSR", outputAbs),
        0x50: ("BVC", outputBranch),
        0x51: ("EOR", outputIndY),
        0x55: ("EOR", outputZPageX),
        0x56: ("LSR", outputZPageX),
        0x58: ("CLI", outputNone),
        0x59: ("EOR", outputAbsY),
        0x5A: ("PHY", outputNone),
        0x5D: ("EOR", outputAbsX),
        0x5E: ("LSR", outputAbsX),
        0x60: ("RTS", outputNone),
        0x61: ("ADC", outputIndX),
        0x65: ("ADC", outputZPage),
        0x66: ("ROR", outputZPage),
        0x68: ("PLA", outputNone),
        0x69: ("ADC", outputImm),
        0x6A: ("ROR", outputNone),
        0x6D: ("ADC", outputAbs),
        0x6E: ("ROR", outputAbs),
        0x70: ("BVS", outputBranch),
        0x71: ("ADC", outputIndY),
        0x75: ("ADC", outputZPageX),
        0x76: ("ROR", outputZPageX),
        0x78: ("SEI", outputNone),
        0x79: ("ADC", outputAbsY),
        0x7A: ("PLY", outputNone),
        0x7D: ("ADC", outputAbsX),
        0x7E: ("ROR", outputAbsX),
        0x81: ("STA", outputIndX),
        0x84: ("STY", outputZPage),
        0x85: ("STA", outputZPage),
        0x86: ("STX", outputZPage),
        0x88: ("DEY", outputNone),
        0x8A: ("TXA", outputNone),
        0x8C: ("STY", outputAbs),
        0x8D: ("STA", outputAbs),
        0x8E: ("STX", outputAbs),
        0x90: ("BCC", outputBranch),
        0x91: ("STA", outputIndY),
        0x94: ("STY", outputZPageX),
        0x95: ("STA", outputZPageX),
        0x96: ("STX", outputZPageY),
        0x98: ("TYA", outputNone),
        0x99: ("STA", outputAbsY),
        0x9A: ("TXS", outputNone),
        0x9D: ("STA", outputAbsX),
        0xA0: ("LDY", outputImm),
        0xA1: ("LDA", outputIndX),
        0xA2: ("LDX", outputImm),
        0xA4: ("LDY", outputZPage),
        0xA5: ("LDA", outputZPage),
        0xA6: ("LDX", outputZPage),
        0xA8: ("TAY", outputNone),
        0xA9: ("LDA", outputImm),
        0xAA: ("TAX", outputNone),
        0xAC: ("LDY", outputAbs),
        0xAD: ("LDA", outputAbs),
        0xAE: ("LDX", outputAbs),
        0xB0: ("BCS", outputBranch),
        0xB1: ("LDA", outputIndY),
        0xB4: ("LDY", outputZPageX),
        0xB5: ("LDA", outputZPageX),
        0xB6: ("LDX", outputZPageY),
        0xB8: ("CLV", outputNone),
        0xB9: ("LDA", outputAbsY),
        0xBA: ("TSX", outputNone),
        0xBC: ("LDY", outputAbsX),
        0xBD: ("LDA", outputAbsX),
        0xBE: ("LDX", outputAbsY),
        0xC0: ("CPY", outputImm),
        0xC1: ("CMP", outputIndX),
        0xC4: ("CPY", outputZPage),
        0xC5: ("CMP", outputZPage),
        0xC6: ("DEC", outputZPage),
        0xC8: ("INY", outputNone),
        0xC9: ("CMP", outputImm),
        0xCA: ("DEX", outputNone),
        0xCC: ("CPY", outputAbs),
        0xCD: ("CMP", outputAbs),
        0xCE: ("DEC", outputAbs),
        0xD0: ("BNE", outputBranch),
        0xD1: ("CMP", outputIndY),
        0xD5: ("CMP", outputZPageX),
        0xD6: ("DEC", outputZPageX),
        0xD8: ("CLD", outputNone),
        0xD9: ("CMP", outputAbsY),
        0xDA: ("PHX", outputNone),
        0xDD: ("CMP", outputAbsX),
        0xDE: ("DEC", outputAbsX),
        0xE0: ("CPX", outputImm),
        0xE1: ("SBC", outputIndX),
        0xE4: ("CPX", outputZPage),
        0xE5: ("SBC", outputZPage),
        0xE6: ("INC", outputZPage),
        0xE8: ("INX", outputNone),
        0xE9: ("SBC", outputImm),
        0xEA: ("NOP", outputNone),
        0xEC: ("CPX", outputAbs),
        0xED: ("SBC", outputAbs),
        0xEE: ("INC", outputAbs),
        0xF0: ("BEQ", outputBranch),
        0xF1: ("SBC", outputIndY),
        0xF5: ("SBC", outputZPageX),
        0xF6: ("INC", outputZPageX),
        0xF8: ("SED", outputNone),
        0xF9: ("SBC", outputAbsY),
        0xFA: ("PLX", outputNone),
        0xFD: ("SBC", outputAbsX),
        0xFE: ("INC", outputAbsX),
        0xFF: (".SYS", outputImm)
        }
