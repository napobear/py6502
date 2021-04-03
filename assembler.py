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
# 6502 Assembler class

import settings

class Assembler:

    _filename = None
    _line = None
    _linenum = 0
    _errors = None
    _ptr = 0
    _code = []
    _pass = 0
    _labels = {}
    _base = 0

    _value = 0
    _str = None
    _oldtoken = None

    # Tokens
    EOL = 0
    INT = 1
    MNEMONIC = 2
    LABEL = 3
    HASH = 4
    COMMA = 5
    LPAREN = 6
    RPAREN = 7
    AREG = 8
    XREG = 9
    YREG = 10
    COLON = 11
    EQU = 12
    STAR = 13
    STRING = 14
    PLUS = 15
    MINUS = 16
    LARROW = 17
    RARROW = 18
    LSQUARE = 19
    RSQUARE = 20

    def __init__(self, filename):
        self._filename = filename
        
    def assemble(self):
        for self._pass in (1, 2):
            self._linenum = 0
            self._errors = 0
            self._code = []
            self._base = settings.BASE_PC
            
            f = open(self._filename, 'r')
            for self._line in f:
                self._linenum += 1
                self._ptr = 0
                self._oldtoken = None
                token = self.gettoken()
                while token != self.EOL:
                    if token == self.LABEL:
                        label = self._str
                        token = self.gettoken()
                        if token == self.EQU:
                            value = self.expression(0, 65535)
                            if value != None:
                                self._labels[label] = value
                            break
                        self._labels[label] = self._base + len(self._code)
                        if token == self.COLON:
                            token = self.gettoken()
                        continue
                    elif token == self.STAR:
                        # This is supposed to set the address at which the
                        # code is assembled. Not much point right now so ignore it.
                        break
                    elif token == self.MNEMONIC:
                        self.instructions[self._str.upper()](self)
                        break
                    else:
                        self.error ("Syntax Error")
                        break
            f.close()
        return self._code
    
    def errorcount(self):
        return self._errors
    
    def error(self, str):
        if self._pass == 2:
            print ("PY6502: {0} ({1}) : error: {2}".format(self._filename, self._linenum, str))
            self._errors += 1

    ################################
    # Parse instruction operands

    def getnumber(self, base):
        value = 0
        size = 0
        ch = self._line[self._ptr]
        while self._ptr < len(self._line):
            ch = self._line[self._ptr]
            if ch.isdigit():
                value = (value * base) + ord(ch) - 48
            elif ch >= 'A' and ch <= 'F' and base == 16:
                value = (value * base) + (ord(ch) - 65) + 10
            elif ch >= 'a' and ch <= 'f' and base == 16:
                value = (value * base) + (ord(ch) - 97) + 10
            else:
                break
            self._ptr += 1
            size += 1
        if size == 0:
            self.error ("Missing value")
            return None
        return value

    # Push the specified token back into a 1-item deep stack so that
    # gettoken returns that next time. Used for lookahead.
    def pushtoken(self, token):
        self._oldtoken = token

    def gettoken(self):
        if self._oldtoken != None:
            token = self._oldtoken
            self._oldtoken = None
            return token
        if self._ptr >= len(self._line):
            return self.EOL
        ch = self._line[self._ptr]
        while ch.isspace():
            self._ptr += 1
            if self._ptr == len(self._line):
                return self.EOL
            ch = self._line[self._ptr]
        if ch == '\'':
            self._ptr += 1
            if self._ptr < len(self._line):
                self._value = ord(self._line[self._ptr])
                self._ptr += 1
                if self._ptr == len(self._line):
                    self.error ("Unexpected end of line")
                elif self._line[self._ptr] != '\'':
                    self.error ("Missing '")
                else:
                    self._ptr += 1
            return self.INT
        if ch == '"':
            self._ptr += 1
            str_list = []
            while self._ptr < len(self._line) and self._line[self._ptr] != '"':
                str_list.append(self._line[self._ptr])
                self._ptr += 1
            if self._ptr == len(self._line):
                self.error ("Unexpected end of line")
            else:
                self._str = ''.join(str_list)
                self._ptr += 1
            return self.STRING
        if ch == ';':
            self._ptr = len(self._line)
            return self.EOL
        if ch == '#':
            self._ptr += 1
            return self.HASH
        if ch == '(':
            self._ptr += 1
            return self.LPAREN
        if ch == ')':
            self._ptr += 1
            return self.RPAREN
        if ch == ',':
            self._ptr += 1
            return self.COMMA
        if ch == '+':
            self._ptr += 1
            return self.PLUS
        if ch == '-':
            self._ptr += 1
            return self.MINUS
        if ch == '=':
            self._ptr += 1
            return self.EQU
        if ch == '*':
            self._ptr += 1
            return self.STAR
        if ch == ':':
            self._ptr += 1
            return self.COLON
        if ch == '<':
            self._ptr += 1
            return self.LARROW
        if ch == '>':
            self._ptr += 1
            return self.RARROW
        if ch == '[':
            self._ptr += 1
            return self.LSQUARE
        if ch == ']':
            self._ptr += 1
            return self.RSQUARE
        if ch == '$':
            self._ptr += 1
            self._value = self.getnumber(16)
            return self.INT
        if ch.isdigit():
            self._value = self.getnumber(10)
            return self.INT
        if ch.isalpha() or ch == '.':
            str_list = []
            while ch.isalnum() or ch == '.' or ch == '_':
                str_list.append(ch)
                self._ptr += 1
                if self._ptr == len(self._line):
                    break
                ch = self._line[self._ptr]
            self._str = ''.join(str_list)
            if self._str.upper() in self.instructions:
                return self.MNEMONIC
            if self._str == "A" or self._str == "a":
                return self.AREG
            if self._str == "X" or self._str == "x":
                return self.XREG
            if self._str == "Y" or self._str == "y":
                return self.YREG
            return self.LABEL
        self.error ("Unexpected character")
        return self.EOL

    def parsenumber(self):
        neg = 1
        value = None
        token = self.gettoken()
        if token == self.STAR:
            return settings.BASE_PC + len(self._code)
        if token == self.LSQUARE:
            value = self.parseop1()
            if self.gettoken() != self.RSQUARE:
                self.error("Missing ]")
            return value
        if token == self.LARROW:
            value = self.parsenumber()
            return value & 0xFF if value != None else value
        if token == self.RARROW:
            value = self.parsenumber()
            return (value >> 8) & 0xFF if value != None else value
        if token == self.MINUS:
            token = self.gettoken()
            neg = -1
        if token == self.PLUS:
            token = self.gettoken()
            neg = 1
        if token == self.LABEL:
            if self._str in self._labels:
                value = self._labels[self._str]
                token = self.INT
            elif self._pass == 1:
                value = 0x100
            else:
                self.error ("Undefined label: " + self._str)
        elif token == self.INT and self._value != None:
            value = self._value
        elif token == self.STRING and len(self._str) == 1:
            value = ord(self._str[0])
        else:
            self.error ("Value expected")
        return value if value == None else value * neg

    # Parse multiplication operator
    def parseop2(self):
        value = self.parsenumber()
        while value != None:
            token = self.gettoken()
            if token == self.STAR:
                value2 = self.parsenumber()
                if value2 == None:
                    break
                value = value * value2
                continue
            self.pushtoken(token)
            break
        return value

    # Parse addition and subtraction operators
    def parseop1(self):
        value = self.parseop2()
        while value != None:
            token = self.gettoken()
            if token == self.PLUS:
                value2 = self.parseop2()
                if value2 == None:
                    break
                value = value + value2
                continue
            if token == self.MINUS:
                value2 = self.parseop2()
                if value2 == None:
                    break
                value = value - value2
                continue
            self.pushtoken(token)
            break
        return value
            
    def expression(self, min, max):
        value = self.parseop1()
        if value != None and (value < min or value > max):
            self.error("Value out of range")
            return None
        return value
            
    def literal(self):
        return self.expression(-128, 255)

    def address(self):
        return self.expression(0, 65535)

    def relative(self):
        return self.expression(-128, 127)

    def operand(self):
        v = { 'type': None, 'value': None }
        token = self.gettoken()
        if token == self.HASH:
            v['type'] = 'Imm'
            v['value'] = self.literal()
        elif token == self.AREG:
            v['type'] = 'Acc'
        elif token == self.LPAREN:
            value = self.address()
            v['value'] = value
            token = self.gettoken()
            if token == self.RPAREN:
                token = self.gettoken()
                if token != self.COMMA:
                    self.pushtoken(token)
                    v['type'] = 'Ind'
                else:
                    if self.gettoken() != self.YREG:
                        self.error ("Y expected")
                    else:
                        if value <= 0xFF:
                            v['type'] = 'IndY'
                        else:
                            self.error ("Value out of range")
            elif token == self.COMMA:
                if self.gettoken() != self.XREG:
                    self.error ("X expected")
                else:
                    if value <= 0xFF:
                        v['type'] = 'IndX'
                    else:
                        self.error ("Value out of range")
                if self.gettoken() != self.RPAREN:
                    self.error (") expected")
            else:
                self.error ("Syntax error")
        elif token == self.LABEL:
            token = self.INT
            if self._str in self._labels:
                self._value = self._labels[self._str]
            elif self._pass == 1:
                self._value = 0x100
            else:
                self.error ("Undefined label: " + self._str)
        if token == self.INT:
            v['value'] = self._value
            if self.gettoken() != self.COMMA:
                v['type'] = 'ZPage' if self._value <= 0xFF else 'Abs'
            else:
                token = self.gettoken()
                if token == self.XREG:
                    v['type'] = 'ZPageX' if self._value <= 0xFF else 'AbsX'
                elif token == self.YREG:
                    v['type'] = 'ZPageY' if self._value <= 0xFF else 'AbsY'
                else:
                    self.error ("Unknown address syntax")
        return v

    def no_operand(self):
        v = self.operand()
        if v['type'] != None:
            self.error ("Operand specified where no operand expected")
            return False
        return True

    ################################
    # Instruction set handlers

    def fnADC(self):
        self.storeCode(0x69, 0x65, 0x75, None, 0x6D, 0x7D, 0x79, 0x61, 0x71, None)

    def fnAND(self):
        self.storeCode(0x29, 0x25, 0x35, None, 0x2D, 0x3D, 0x39, 0x21, 0x31, None)

    def fnASL(self):
        self.storeCode(None, 0x06, 0x16, None, 0x0E, 0x1E, None, None, None, 0xA)

    def fnBCC(self):
        self.storeBranch(0x90)

    def fnBCS(self):
        self.storeBranch(0xB0)

    def fnBEQ(self):
        self.storeBranch(0xF0)
        
    def fnBIT(self):
        self.storeCode(None, 0x24, None, None, 0x2C, None, None, None, None, None)

    def fnBMI(self):
        self.storeBranch(0x30)

    def fnBNE(self):
        self.storeBranch(0xD0)

    def fnBPL(self):
        self.storeBranch(0x10)

    def fnBRK(self):
        if self.no_operand():
            self._code.append(0x00)

    def fnBVC(self):
        self.storeBranch(0x50)

    def fnBVS(self):
        self.storeBranch(0x70)

    def fnCLC(self):
        if self.no_operand():
            self._code.append(0x18)

    def fnCLD(self):
        if self.no_operand():
            self._code.append(0xD8)

    def fnCLI(self):
        if self.no_operand():
            self._code.append(0x58)

    def fnCLV(self):
        if self.no_operand():
            self._code.append(0xB8)
        
    def fnCMP(self):
        self.storeCode(0xC9, 0xC5, 0xD5, None, 0xCD, 0xDD, 0xD9, 0xC1, 0xD1, None)
        
    def fnCPX(self):
        self.storeCode(0xE0, 0xE4, None, None, 0xEC, None, None, None, None, None)
        
    def fnCPY(self):
        self.storeCode(0xC0, 0xC4, None, None, 0xCC, None, None, None, None, None)
        
    def fnDEC(self):
        self.storeCode(None, 0xC6, 0xD6, None, 0xCE, 0xDE, None, None, None, None)

    def fnDEX(self):
        if self.no_operand():
            self._code.append(0xCA)

    def fnDEY(self):
        if self.no_operand():
            self._code.append(0x88)
        
    def fnEOR(self):
        self.storeCode(0x49, 0x45, 0x55, None, 0x4D, 0x5D, 0x59, 0x41, 0x51, None)
        
    def fnINC(self):
        self.storeCode(None, 0xE6, 0xF6, None, 0xEE, 0xFE, None, None, None, None)

    def fnINX(self):
        if self.no_operand():
            self._code.append(0xE8)

    def fnINY(self):
        if self.no_operand():
            self._code.append(0xC8)

    def fnJMP(self):
        v = self.operand()
        if v['value'] != None:
            if v['type'] == 'Abs' or v['type'] == 'ZPage':
                self._code.append(0x4C)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            elif v['type'] == 'Ind':
                self._code.append(0x6C)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            else:
                self.error ("Addressing mode not allowed for instruction")

    def fnJSR(self):
        v = self.operand()
        if v['value'] != None:
            if v['type'] == 'Abs' or v['type'] == 'ZPage':
                self._code.append(0x20)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            else:
                self.error ("Addressing mode not allowed for instruction")
        
    def fnLDA(self):
        self.storeCode(0xA9, 0xA5, 0xB5, None, 0xAD, 0xBD, 0xB9, 0xA1, 0xB1, None)

    def fnLDX(self):
        self.storeCode(0xA2, 0xA6, None, 0xB6, 0xAE, None, 0xBE, None, None, None)

    def fnLDY(self):
        self.storeCode(0xA0, 0xA4, 0xB4, None, 0xAC, 0xBC, None, None, None, None)

    def fnLSR(self):
        self.storeCode(None, 0x46, 0x56, None, 0x4E, 0x5E, None, None, None, 0x4A)

    def fnNOP(self):
        if self.no_operand():
            self._code.append(0xEA)

    def fnORA(self):
        self.storeCode(0x09, 0x05, 0x15, None, 0x0D, 0x1D, 0x19, 0x01, 0x11, None)

    def fnPHA(self):
        if self.no_operand():
            self._code.append(0x48)

    def fnPHP(self):
        if self.no_operand():
            self._code.append(0x08)

    def fnPHX(self):
        if self.no_operand():
            self._code.append(0xDA)

    def fnPHY(self):
        if self.no_operand():
            self._code.append(0x5A)

    def fnPLA(self):
        if self.no_operand():
            self._code.append(0x68)

    def fnPLP(self):
        if self.no_operand():
            self._code.append(0x28)

    def fnPLX(self):
        if self.no_operand():
            self._code.append(0xFA)

    def fnPLY(self):
        if self.no_operand():
            self._code.append(0x7A)

    def fnROL(self):
        self.storeCode(None, 0x26, 0x36, None, 0x2E, 0x3E, None, None, None, 0x2A)

    def fnROR(self):
        self.storeCode(None, 0x66, 0x76, None, 0x6E, 0x7E, None, None, None, 0x6A)

    def fnRTI(self):
        if self.no_operand():
            self._code.append(0x40)

    def fnRTS(self):
        if self.no_operand():
            self._code.append(0x60)

    def fnSBC(self):
        self.storeCode(0xE9, 0xE5, 0xF5, None, 0xED, 0xFD, 0xF9, 0xE1, 0xF1, None)

    def fnSEC(self):
        if self.no_operand():
            self._code.append(0x38)

    def fnSED(self):
        if self.no_operand():
            self._code.append(0xF8)

    def fnSEI(self):
        if self.no_operand():
            self._code.append(0x78)

    def fnSTA(self):
        self.storeCode(None, 0x85, 0x95, None, 0x8D, 0x9D, 0x99, 0x81, 0x91, None)

    def fnSTX(self):
        self.storeCode(None, 0x86, None, 0x96, 0x8E, None, None, None, None, None)

    def fnSTY(self):
        self.storeCode(None, 0x84, 0x94, None, 0x8C, None, None, None, None, None)

    def fnTAX(self):
        if self.no_operand():
            self._code.append(0xAA)

    def fnTAY(self):
        if self.no_operand():
            self._code.append(0xA8)

    def fnTSX(self):
        if self.no_operand():
            self._code.append(0xBA)

    def fnTXA(self):
        if self.no_operand():
            self._code.append(0x8A)

    def fnTXS(self):
        if self.no_operand():
            self._code.append(0x9A)

    def fnTYA(self):
        if self.no_operand():
            self._code.append(0x98)

    def fnSYS(self):
        self.storeCode(0xFF, None, None, None, None, None, None, None, None, None)

    def fnBYTE(self):
        token = self.gettoken()
        while token == self.INT or token == self.STRING:
            if token == self.INT:
                if self._value > 0xFF:
                    self.error ("Byte value expected")
                self._code.append(self._value & 0xFF)
            elif token == self.STRING:
                for ch in self._str:
                    self._code.append(ord(ch))
            if self.gettoken() != self.COMMA:
                break
            token = self.gettoken()

    def fnWORD(self):
        token = self.gettoken()
        while token == self.INT:
            self._code.append(self._value & 0xFF)
            self._code.append((self._value >> 8) & 0xFF)
            if self.gettoken() != self.COMMA:
                break
            token = self.gettoken()

    def storeCode(self, imm, zpage, zpagex, zpagey, abs, absx, absy, indx, indy, acc):
        v = self.operand()
        if v['type'] == None or v['type'] == 'Acc' and acc != None:
            self._code.append(acc)
        else:
            if v['type'] == 'ZPageX' and zpagex == None and absx != None:
                v['type'] = 'AbsX'
            if v['type'] == 'ZPageY' and zpagey == None and absy != None:
                v['type'] = 'AbsY'
            if v['type'] == 'Imm' and imm != None:
                self._code.append(imm)
                self._code.append(v['value'])
            elif v['type'] == 'ZPage' and zpage != None:
                self._code.append(zpage)
                self._code.append(v['value'])
            elif v['type'] == 'ZPageX' and zpagex != None:
                self._code.append(zpagex)
                self._code.append(v['value'])
            elif v['type'] == 'ZPageY' and zpagey != None:
                self._code.append(zpagey)
                self._code.append(v['value'])
            elif v['type'] == 'Abs' and abs != None:
                self._code.append(abs)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            elif v['type'] == 'AbsX' and absx != None:
                self._code.append(absx)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            elif v['type'] == 'AbsY' and absy != None:
                self._code.append(absy)
                self._code.append(v['value'] & 0xFF)
                self._code.append((v['value'] >> 8) & 0xFF)
            elif v['type'] == 'IndX' and indx != None:
                self._code.append(indx)
                self._code.append(v['value'])
            elif v['type'] == 'IndY' and indy != None:
                self._code.append(indy)
                self._code.append(v['value'])
            else:
                self.error ("Addressing mode not allowed for instruction")

    def storeBranch(self, op):
        token = self.gettoken()
        if token == self.INT:
            self._code.append(op)
            self._code.append(self._value & 0xFF)
        elif token == self.LABEL:
            if self._str in self._labels:
                value = self._labels[self._str]
            elif self._pass == 1:
                value = 0
            else:
                self.error ("Undefined label: " + self._str)
            self._code.append(op)
            self._code.append(((value - self._base) - len(self._code)) & 0xFF)
        else:
            self.error ("Label expected")

    ################################
    # Full 6502 mnemonic set

    instructions = {
        'ADC': fnADC,
        'AND': fnAND,
        'ASL': fnASL,
        'BCC': fnBCC,
        'BCS': fnBCS,
        'BEQ': fnBEQ,
        'BIT': fnBIT,
        'BMI': fnBMI,
        'BNE': fnBNE,
        'BPL': fnBPL,
        'BRK': fnBRK,
        'BVC': fnBVC,
        'BVS': fnBVS,
        'CLC': fnCLC,
        'CLD': fnCLD,
        'CLI': fnCLI,
        'CLV': fnCLV,
        'CMP': fnCMP,
        'CPX': fnCPX,
        'CPY': fnCPY,
        'DEC': fnDEC,
        'DEX': fnDEX,
        'DEY': fnDEY,
        'EOR': fnEOR,
        'INC': fnINC,
        'INX': fnINX,
        'INY': fnINY,
        'JMP': fnJMP,
        'JSR': fnJSR,
        'LDA': fnLDA,
        'LDX': fnLDX,
        'LDY': fnLDY,
        'LSR': fnLSR,
        'NOP': fnNOP,
        'ORA': fnORA,
        'PHA': fnPHA,
        'PHP': fnPHP,
        'PHX': fnPHX,
        'PHY': fnPHY,
        'PLA': fnPLA,
        'PLP': fnPLP,
        'PLX': fnPLX,
        'PLY': fnPLY,
        'ROL': fnROL,
        'ROR': fnROR,
        'RTI': fnRTI,
        'RTS': fnRTS,
        'SBC': fnSBC,
        'SEC': fnSEC,
        'SED': fnSED,
        'SEI': fnSEI,
        'STA': fnSTA,
        'STX': fnSTX,
        'STY': fnSTY,
        'TAX': fnTAX,
        'TAY': fnTAY,
        'TSX': fnTSX,
        'TXA': fnTXA,
        'TXS': fnTXS,
        'TYA': fnTYA,
        '.BYTE': fnBYTE,
        '.WORD': fnWORD,
        '.SYS': fnSYS
        }
