'''
@author: David Zemon

@summary: Provide datapath components common to all RISC machines, regardless of
        optimization level
'''

from copy import copy
import Globals


class FuncUnit:
    '''
    @summary: Parent class for all functional units; Values are calculated and then stored
            in an output buffer known as "output" in the __init__ parameters
    '''

    def __init__ (self, output):
        '''
        @summary: Create a new functional unit and store values in the output dictionary

        @param output: dict consisting of {"A": ..., "B": ...}; See individual implementations
                    for what A and B are used for
        '''
        self.delay = None;
        self.ops = []
        self.output = output
        self.getName()

    def load (self, op, ops = []):
        print "Calling FuncUnit.load()! Illegal! Must call child class!"
        exit(1)

    def getDelay (self):
        return self.curDelay

    def tick (self):
        self.delay -= 1
        if 0 == self.delay:
            self.writeResult()

    def ding (self):
        # If the functional unit is done computing, go "DING!"
        if 0 == self.delay:
            if Globals.DEBUG:
                print "\tFU completed\n\t\tMem's A = " + str(self.output["A"]) + "\n\t\tMem's B = " + str(
                    self.output["B"])
            return True
        # Else do nothing :(
        else:
            return False


class IntFU(FuncUnit):
    def getName (self):
        self.name = "Integer"

    def load (self, op, ops = []):
        self.operation = copy(op)
        self.ops = copy(ops)
        if self.operation in (Globals.MATH_INSTRS + Globals.LOGIC_INSTRS + Globals.SHIFT_INSTRS):
            self.delay = Globals.INTEGER_DELAY
        else:
            self.delay = Globals.MISC_DELAY

        if Globals.DEBUG:
            print "\tInteger FU running " + self.operation + ':'
            for op in self.ops:
                print "\t\top: " + str(op)

    def writeResult (self):
        if "add" == self.operation:
            self.output["A"] = int(self.ops[0] + self.ops[1])
        elif "sub" == self.operation:
            self.output["A"] = int(self.ops[0] - self.ops[1])
        elif "mul" == self.operation:
            self.output["A"] = int(self.ops[0] * self.ops[1])
        elif "div" == self.operation:
            self.output["A"] = int(self.ops[0] / self.ops[1])
            self.output["B"] = int(self.ops[0] % self.ops[1])
        elif "or" == self.operation:
            self.output["A"] = int(self.ops[0] | self.ops[1])
        elif "and" == self.operation:
            self.output["A"] = int(self.ops[0] & self.ops[1])
        elif "nand" == self.operation:
            self.output["A"] = int(~(self.ops[0] & self.ops[1]))
        elif "xor" == self.operation:
            self.output["A"] = int(self.ops[0] ^ self.ops[1])
        elif "neg" == self.operation:
            self.output["A"] = int(~self.ops[0])
        elif "shl" == self.operation:
            self.output["A"] = int(self.ops[0] << 1)
        elif "shr" == self.operation:
            self.output["A"] = int(self.ops[0] >> 1)
        elif "ljmp" == self.operation:
            self.output["A"] = 0
            self.output["B"] = self.ops[0]
        elif "sjmp" == self.operation:
            self.output["A"] = 0
            self.output["B"] = self.ops[0] + self.ops[1]
        elif self.operation in Globals.CND_JMP_INSTRS:
            if "djnz" == self.operation:
                self.ops[0] -= 1
            self.output["A"] = self.ops[0]
            self.output["B"] = self.ops[1]
        elif "mov" == self.operation:
            self.output["A"] = self.ops[0]
            self.output["B"] = self.ops[1]
        else:
            raise Exception("Unknown operation entered functional unit! " + self.operation)


class FltFU(FuncUnit):
    def getName (self):
        self.name = "Floating point"

    def load (self, op, ops = []):
        self.operation = copy(op)
        self.ops = copy(ops)
        if self.operation in Globals.MOV_INSTRS:
            self.delay = Globals.MISC_DELAY
        else:
            self.delay = Globals.FLOATING_POINT_DELAY

    def writeResult (self):
        if "add" == self.operation:
            self.output["A"] = float(self.ops[0] + self.ops[1])
        elif "sub" == self.operation:
            self.output["A"] = float(self.ops[0] - self.ops[1])
        elif "mul" == self.operation:
            self.output["A"] = float(self.ops[0] * self.ops[1])
        elif "div" == self.operation:
            self.output["A"] = float(self.ops[0] / self.ops[1])
        elif self.operation in Globals.MOV_INSTRS:
            self.output["A"] = self.ops[0]
            self.output["B"] = self.ops[1]
        else:
            raise Exception("Unknown operation entered functional unit! " + self.operation)


class RISC_Instr(object):
    '''
    @summary: Container for RISC-like instruction & operands

    Available instructions:
        - nop
        - add, sub, mul, div
        - or, and, nand, xor
        - shl, shr
        - mov
        - sjmp, ljmp, jz, djnz
    '''

    def __init__ (self, Rn, instr, ops = []):
        # Save the register file
        self.Rn = Rn

        # Store the instruction name
        self.instr = instr

        # Store the operands
        self.ops = []
        for op in ops:
            self.ops.append(FlexibleOp(self.Rn, op))

    def __getitem__ (self, opNum):
        return self.ops[opNum]

    def getOps (self):
        return self.ops

    def getSrcOps (self):
        if self.instr in (Globals.MOV_INSTRS + Globals.MATH_INSTRS + Globals.LOGIC_INSTRS + Globals.SHIFT_INSTRS):
            ops = []
            for op in self.ops:
                if 0 != self.ops.index(op) and '#' != op.op[0]:
                    ops.append(op)
                if 0 == self.ops.index(op) and '@' == op.op[0]:
                    ops.append(op)
            return ops
        elif self.instr in Globals.CND_JMP_INSTRS:
            return [self.ops[0]]
        else:
            return []

    def numOps (self):
        return len(self.ops)

    def getFU (self, FUs):
        '''
        @summary: If 'F' exists anywhere in the operands of an instruction, it is a floating
                point instruction and the floating point functional unit should be returned;
                This can be modified later to differentiate between more FUs like shift FUs,
                register move FUs, etc
        '''

        for op in self.ops:
            if 'F' in op.op:
                return FUs["FLT"]

        return FUs["INT"]

    def writeResult (self):
        '''
        @summary: Determine if the instruction should write back to the register file
        '''
        if Globals.DEBUG and "nop" != self.instr:
            print "\tDetermining if instruction modifies register file:"
            print "\t\tInstr: " + self.instr + "\n\t\tDest operand: " + self.ops[0].op

        if self.instr in (Globals.MATH_INSTRS + Globals.LOGIC_INSTRS + Globals.SHIFT_INSTRS + ["djnz", "mov"]):
            if 'F' == self.ops[0].op[0] or 'R' == self.ops[0].op[0]:
                return True

        return False

    def getStr (self):
        ops = []
        for op in self.ops:
            ops.append(op.op)
        return str(self.instr) + ' ' + ", ".join(ops)

    def getSrcOpVal (self, srcOp):
        if "nop" == self.instr:
            return None

        if srcOp in [0, 1, 2]:
            # Handle jump and move instructions
            if self.instr in Globals.JUMP_INSTRS:
                if 0 == srcOp or (1 == srcOp and (self.instr in Globals.CND_JMP_INSTRS)):
                    return self.ops[srcOp].getVal()
                else:
                    return None
            elif "mov" == self.instr:
                if self.ops[srcOp].isLdStrOp():
                    return self.ops[srcOp].getAddress()
                else:
                    return self.ops[srcOp].getVal()
            # Handle everything else
            else:
                if 0 == srcOp:
                    raise Exception("Range error: 0 is not a source operand for the " + self.instr + " instruction")
                elif 1 == srcOp or (2 == srcOp and (self.instr in Globals.TRIPLE_OPERANDS)):
                    return self.ops[srcOp].getVal()
                else:
                    return None
        else:
            raise Exception(
                "Range error: RISC_Intr.getSrcOpVal() does not support operand requests other than 0, 1, and 2")


class FlexibleOp:
    def __init__ (self, Rn, op):
        self.op = op
        self.Rn = Rn

    def getVal (self):
        # Case 1) Register file operand
        if ('R' == self.op[0]) or ('F' == self.op[0]):
            return self.Rn[self.op]
        # Case 2) Indirect addressing
        elif ('@' == self.op[0]):
            return Globals.basicRAM[self.Rn[self.op]]
        # Case 3) Immediate addressing
        elif '#' == self.op[0]:
            if '.' in self.op:
                return float(self.op[1:])
            else:
                return int(self.op[1:])
        # Case 4) Direct addressing
        else:
            return Globals.basicRAM[int(self.op)]

    def setVal (self, value):
        '''
        @summary: Decode the address of an operand and write 'value' to that address
        '''

        if None == value:
            raise Exception("Attempting to write 'None' as destination value")

        # Case 1) Register file operand
        if ('R' == self.op[0]) or ('F' == self.op[0]):
            self.Rn[self.op] = value
        # Case 2) Indirect addressing
        elif ('@' == self.op[0]):
            Globals.basicRAM[self.Rn[self.op[1:]]] = value
        # Case 3) Direct addressing
        else:
            Globals.basicRAM[self.op] = value

    def isLdStrOp (self):
        if ('R' == self.op[0]) or ('F' == self.op[0]) or ('#' == self.op[0]):
            return False
        else:
            return True

    def getAddress (self):
        # Throw an error if the operand is not indirect or direct
        if not self.isLdStrOp():
            raise Exception("Requested address from operand that is not a RAM address")

        if '@' == self.op[0]:
            return self.Rn[self.op[1:]]
        else:
            return int(self.op)


if __name__ == "__main__":
    raise Exception("Cannot call this file directly")
