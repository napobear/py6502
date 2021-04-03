#!/usr/bin/env python
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
#
# Usage:
#  python py6502.py -a <asmfile>
#    assembles the 6502 assembler source file and outputs to <asmfile>.out. The output is basic
#    JSON format for portability and is really only intended to be consumed by py6502.
#
#  python py6502.py -d <outfile>
#    disassembles the output file produced by the assembler step.
#
#  python py6502.py -x <outfile>
#    simulates the output file produces by the assembler step and dumps the contents of the registers
#    and flags at the end.
#
#  python py6502.py -t <outfile>
#    traces the execution of the output file produced by the assembler. This allows you to follow the
#    simulation and examine the register and flag states at each step. Enter 'h' at the prompt to see
#    the list of commands available during tracing.
#
#  python py6502.py -h
#    displays the help page. The other command line options are documented here so I've not bothered
#    to repeat them here.
#
#  Technical Note:
#    This is pretty bare bones, basic, and most certainly has bugs. I wrote this as a quick and dirty
#    project to both teach myself Python and to educate my son the fundamentals of how processors
#    work. The original code was extended and cleaned up sufficiently to be able to run the microchess
#    program with minor edits.
#
#    For simulation purposes, the instruction set includes a .sys directive that allows input and output
#    from and to the console:
#        .SYS #0     ...  waits for a character to be entered and returns it in the accumulator
#        .SYS #1     ...  echoes the character in the accumulator to the console
#    With this you should be able to adapt microchess or other programs to run in the simulator. I have
#    not included this in the package for copyright purposes.
#
#    I developed and tested this on both a Mac OSX and Windows running python3 but I've tested the
#    the same code with python2 and it should work fine with both.
#
#  History:
#    1.0: Original
#    1.01: Support EHBASIC syntax.

import os
import sys
import argparse
import json
import simulator
import assembler
import disassembler

################################
# Main program

app_version = "1.01"

parser = argparse.ArgumentParser(usage="%(prog)s option filename", description="6502 Assembler/Disassembler/Simulator")
parser.add_argument("-a", "--assemble", action="store_true", dest="assemble", default=False, help="assemble the code in FILE")
parser.add_argument("-d", "--disassemble", action="store_true", dest="disassemble", default=False, help="disassemble the code in FILE")
parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", default=False, help="quiet mode")
parser.add_argument("-t", "--trace", action="store_true", dest="trace", default=False, help="trace the code in FILE")
parser.add_argument("-x", "--execute", action="store_true", dest="execute", default=False, help="execute the code in FILE")
parser.add_argument("-v", "--version", action="version", version="%(prog)s " + app_version)
parser.add_argument("filename")
args = parser.parse_args()

infile = args.filename

if args.assemble:
    if not args.quiet:
        print ("Assembling...")
    assembler = assembler.Assembler(infile)
    code = assembler.assemble()
    
    if assembler.errorcount() > 0:
        sys.exit()

    outfile = infile + ".out"
    f = open(outfile, "w")
    json.dump(code, f)
    f.close()

    infile = outfile
        
if args.disassemble:
    if not args.quiet:
        print ("Disassembling...")
    try:
        f = open(infile, "r")
        code = json.load(f)
        f.close()
    except:
        print ("Error: Could not decode input file: " + infile)
        sys.exit()

    disassembler = disassembler.Disassembler()
    disassembler.disassemble(code)

if args.execute or args.trace:
    try:
        f = open(infile, "r")
        code = json.load(f)
        f.close()
    except:
        print ("Error: Could not decode input file: " + infile)
        sys.exit()

    if not args.quiet:
        print ("Executing...")
    action = simulator.Simulator(code)
    action.run(args.trace)

    if not args.quiet:
        print ("Execution Completed")
        print ("Processor state at end of execution:")
        print ("\nRegisters:")
        print ("  A = {0:02X}".format(action._Acc))
        print ("  X = {0:02X}".format(action._X))
        print ("  Y = {0:02X}".format(action._Y))
        print (" SP = {0:02X}".format(action._S))
        print ("Flags:")
        print (" D{0} : C{1} : I{2} : N{3} : Z{4} : O{5}".format(action.DFlag(), action.CFlag(), action.IFlag(), action.NFlag(), action.ZFlag(), action.OFlag()))
