"""
Created on April 24, 2013

@author: David Zemon

@summary: Simulate advanced pipeline optimization techniques including...
    1) Forwarding
    2) VLIW with multi-pipe
    3) Branch prediction

    Performance will be evaluated by comparing the total execution time (in clock cycles)
    of the newly generated advanced/optimized pipeline with that of the typical 5-stage
    (unforwarded) RISC pipeline. The algorithm used for the comparison is listed below.
"""

from copy import deepcopy
from traceback import print_exc
from BasicRISC import BasicRISC, RISC_Instr
import Globals


def loadRAM (filename, ram, Rn):
    f = open(filename, 'r')

    i = 0
    for line in f:
        if line[0] not in Globals.COMMENT_CHARS:
            line = line.replace(',', '')
            line = line.split()
            ram[i] = RISC_Instr(Rn, line[0], line[1:])
            i += 1


def printRAM (ram):
    for line in ram:
        if None != line:
            if type(line) == RISC_Instr:
                print str(ram.index(line)) + ":\t" + line.getStr()
            else:
                print str(ram.index(line)) + ":\t" + str(line)


def printDPDebug (datapath):
    printRAM(datapath.RAM)
    print datapath.Rn
    print "Exec's A: " + str(datapath.pipe.stages['e'].input["A"]) + "\tB: " + str(datapath.pipe.stages['e'].input["B"])
    print "Mem's A: " + str(datapath.pipe.stages['m'].input["A"]) + "\tB: " + str(datapath.pipe.stages['m'].input["B"])
    print "Write's input: " + str(datapath.pipe.stages['w'].inputBuf)
    if datapath.pipe.stages['w'].outputBuf["Valid"]:
        print "Write's output... Dest: " + datapath.pipe.stages['w'].outputBuf["Dest"].op + "\tValue: " + str(
            datapath.pipe.stages['w'].outputBuf["Value"])
    else:
        print "Write's output empty"


if __name__ == "__main__":
    print "Welcome!"
    Globals.basicRAM = deepcopy(Globals.RAM)

    basic = BasicRISC(Globals.basicRAM)
    Globals.INIT_INSTR = RISC_Instr(basic.Rn, "nop")
    basic.load()

    loadRAM("instructionList.asm", Globals.basicRAM, basic.Rn)

    printRAM(Globals.basicRAM)

    #noinspection PyBroadException
    try:
        print "\n#############\nFirst tick!!!\n#############"
        clock = 0
        basic.tick()
        clock += 1
        while not basic.done() and clock < 150:
            if Globals.DEBUG and not (clock % 5):
                print "\n##########\n" + str(clock) + ": Tick..."
            basic.tick()
            clock += 1
    except:
        print "\n!!!!!!!!!!!!!!!!!!!!!!!\n!!! Caught an error !!!\n!!!!!!!!!!!!!!!!!!!!!!!"
        print "Clock: " + str(clock)
        printDPDebug(basic)
        print_exc()
        exit(1)

    print "\nCompleted in " + str(clock) + " clock cycles!"
    printRAM(Globals.basicRAM)
    print basic.Rn
