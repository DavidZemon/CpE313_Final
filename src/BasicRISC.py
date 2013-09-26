"""
@author: David Zemon

@summary: Provide necessary components to create a basic, un-optimized RISC pipeline
"""

from copy import deepcopy, copy
import Globals
from UniversalComponents import FltFU, IntFU, RISC_Instr


class StageFetch:
    """
    @summary: Fetch stage of the RISC pipeline
    """

    def __init__ (self, parent, decode):
        self.parent = parent
        self.decode = decode
        self.PC = 0

    def tick (self, stall = False):
        # Load next instruction
        if False == stall and Globals.basicRAM[self.PC]:
            if Globals.basicRAM[self.PC]:
                self.decode.IR = copy(Globals.basicRAM[self.PC])
            self.PC += 1  # Increment the program counter
            return
            # Or stall...
        self.decode.IR = RISC_Instr(self.parent.Rn, "nop")


class StageDecode:
    """
    @summary: Decode stage of the RISC pipeline
    """

    def __init__ (self, parent, execute):
        self.parent = parent
        self.execute = execute
        self.IR = copy(Globals.INIT_INSTR)

    def tick (self):
        # Handle jumps
        if self.IR.instr in Globals.JUMP_INSTRS:
            if "sjmp" == self.IR.instr:
                self.execute.input = {"A": self.IR.getSrcOpVal(0), "B": self.parent.stages['f'].PC}
            elif "djnz" == self.IR.instr:
                self.execute.input = {"A": self.IR.getSrcOpVal(0),
                                      "B": self.parent.stages['f'].PC + self.IR.getSrcOpVal(1)}
            else:
                self.execute.input = {"A": self.IR.getSrcOpVal(0), "B": self.IR.getSrcOpVal(1)}
        # Followed by moves...
        elif "mov" == self.IR.instr:
            if self.IR.ops[0].isLdStrOp():
                self.execute.input["A"] = self.IR.getSrcOpVal(0)
            self.execute.input["B"] = self.IR.getSrcOpVal(1)
        # And finally, everything else
        else:
            self.execute.input = {"A": self.IR.getSrcOpVal(1), "B": self.IR.getSrcOpVal(2)}

        self.execute.IR = copy(self.IR)


class StageExecute:
    """
    @summary: Execute stage of the RISC pipeline
    """

    def __init__ (self, memory, fetch):
        self.memory = memory
        self.fetch = fetch  # need to be able to clear out the decode instruction if a jump is taken
        self.IR = copy(Globals.INIT_INSTR)
        self.funcUnits = {"INT": IntFU(self.memory.input), "FLT": FltFU(self.memory.input)}
        self.runningFU = None
        self.input = {"A": None, "B": None}

    def tick (self):
        if Globals.DEBUG:
            print "\tA: " + str(self.input["A"]) + "\n\tB: " + str(self.input["B"])

        # If a functional unit is no longer running, determine which FU should be loaded with the next instruction
        if (None == self.runningFU) and ("nop" != self.IR.instr):
            self.runningFU = self.IR.getFU(self.funcUnits)
            self.runningFU.load(self.IR.instr, [self.input["A"], self.input["B"]])

        # If a functional unit is currently running, give it another tick
        if self.runningFU:
            # Functional unit *is* running...
            self.runningFU.tick()  # Give it a clock cycle

            # Is it done yet?
            if self.runningFU.ding():
                # Yep!
                # Did it compute a jump and, if conditional, was the condition true?
                if self.IR.instr in Globals.JUMP_INSTRS and self.branchCheck():
                    # Yep! Let's reload the PC and delete the instruction in decode
                    if Globals.DEBUG:
                        print "\tTaking jump!!!"
                    self.fetch.PC = self.memory.input["B"]
                    self.fetch.decode.IR = copy(Globals.INIT_INSTR)
                self.runningFU = None
            # Functional unit still running
            else:
                # push nop into memory stage until the FU is done
                self.memory.IR = copy(Globals.INIT_INSTR)
                return

        # Functional unit is empty, push instruction into memory stage
        self.memory.IR = copy(self.IR)

    def branchCheck (self):
        if self.IR.instr in Globals.UCND_JMP_INSTRS:
            return True
        elif "jz" == self.IR.instr and 0 == self.memory.input["A"]:
            return True
        elif "djnz" == self.IR.instr and 0 != self.memory.input["A"]:
            return True
        else:
            return False

    def clear (self):
        self.IR = copy(Globals.INIT_INSTR)
        self.input["A"] = None
        self.input["B"] = None


class StageMemory:
    """
    @summary: Memory stage of the RISC pipeline
    """

    def __init__ (self, write, ram):
        self.write = write
        self.IR = copy(Globals.INIT_INSTR)
        self.RAM = ram
        self.input = {"A": None, "B": None}

    def tick (self):
        if Globals.DEBUG:
            print "\tA: " + str(self.input["A"])
            print "\tB: " + str(self.input["B"])

        if "mov" == self.IR.instr:
            if self.IR[0].isLdStrOp():
                self.RAM[self.input["A"]] = self.input["B"]
                return
            elif self.IR[1].isLdStrOp():
                self.write.inputBuf = self.RAM[self.input["B"]]
                return
            else:
                self.write.inputBuf = self.input["B"]
        else:
            self.write.inputBuf = self.input["A"]

        # Push instruction into write stage
        self.write.IR = copy(self.IR)

    def clear (self):
        self.input["A"] = None
        self.input["B"] = None
        self.IR = copy(Globals.INIT_INSTR)


class StageWrite:
    """
    @summary: Write stage of the RISC pipeline
    """

    def __init__ (self):
        self.IR = copy(Globals.INIT_INSTR)
        self.inputBuf = None
        self.outputBuf = {"Valid": False, "Value": None}

    def tick (self):
        # Stage the destination value until after decode has completed
        if Globals.DEBUG:
            print "\tInputBuf: " + str(self.inputBuf)

        if self.IR.writeResult():
            self.outputBuf["Valid"] = True
            self.outputBuf["Dest"] = copy(self.IR[0])
            self.outputBuf["Value"] = self.inputBuf
        else:
            self.outputBuf["Valid"] = False

    def clear (self):
        self.IR = copy(Globals.INIT_INSTR)
        self.inputBuf = None


class RISCPipe:
    """
    @summary: A simple, unforwarded, RISC pipe
    """

    def __init__ (self, Rn, ram):
        self.Rn = Rn
        self.stages = {}
        self.stages['w'] = StageWrite()
        self.stages['m'] = StageMemory(self.stages['w'], ram)
        self.stages['e'] = StageExecute(self.stages['m'], None)
        self.stages['d'] = StageDecode(self, self.stages['e'])
        self.stages['f'] = StageFetch(self, self.stages['d'])

        # Connect execute to decode and fetch
        self.stages['e'].fetch = self.stages['f']

    def tick (self):
        """
        @summary: This function will simulate one tick of the clock cycle. Work will be done
            "backwards", starting with the write stage and moving toward fetch, otherwise
            the current status of each stage would be lost as we moved forward

        @param instr: Type must be RISC_Instr and should represent the next instruction
            for the pipe to execute
        """

        # Give a tick to write, memory and execute - these can not be stalled
        # because the basic RISC has only RAW and only decode does register reads
        for stage in ['w', 'm', 'e']:
            if Globals.DEBUG:
                print Globals.STAGE_NAMES[stage]
            self.stages[stage].tick()
            if Globals.DEBUG:
                print "\tInstr: " + self.stages[stage].IR.instr
                for op in self.stages[stage].IR.getOps():
                    print "\t\top: " + op.op

            if 'e' == stage and self.stages['e'].runningFU:
                if Globals.DEBUG:
                    print "Waiting on " + self.stages['e'].runningFU.name + "..."
                    # Allow the write stage to modify the register file if needed
                self.stages['m'].clear()
                self.writeOutBuf()
                return

        # Check if decode should be stalled (does w, m, or e contain a RAW hazard?)
        if self.stall():
            if Globals.DEBUG:
                print "!!! Stalling \"" + self.stages['d'].IR.getStr() + "\" due to RAW..."
            self.stages['e'].clear()
            self.writeOutBuf()
            return

        if Globals.DEBUG:
            print "\n" + Globals.STAGE_NAMES['d']
        self.stages['d'].tick()
        if Globals.DEBUG:
            print "\tInstr: " + self.stages['d'].IR.instr
            for op in self.stages['d'].IR.getOps():
                print "\t\top: " + op.op
        self.writeOutBuf()  # If we finished running decode, allow the write stage to modify the register file

        if Globals.DEBUG:
            print "\n" + Globals.STAGE_NAMES['f']
            print "\tPC: " + str(self.stages['f'].PC)
        self.stages['f'].tick()

    def writeOutBuf (self):
        if Globals.DEBUG:
            print '\t' + str(self.stages['w'].outputBuf)

        if self.stages['w'].outputBuf["Valid"]:
            if Globals.DEBUG:
                print "Writing to register file!"
                print "\tDest: " + self.stages['w'].outputBuf["Dest"].op
                print "\tValue: " + str(self.stages['w'].outputBuf["Value"])

            self.stages['w'].outputBuf["Dest"].setVal(self.stages['w'].outputBuf["Value"])

    def stall (self):
        """
        @summary: Return a boolean description for whether or not the pipe should insert
                a stall after decode
        """
        dependInstr = copy(self.stages['d'].IR)
        if Globals.DEBUG:
            print "\tSTALL CHECK"
            print "\t\tDependent instruction: " + dependInstr.getStr()

        # If the dependent instruction does not read any operands, there can be no stall
        if dependInstr.instr in Globals.NO_READ:
            return False
        else:
            dependOps = dependInstr.getSrcOps()
            if [] == dependOps:
                return False

        # Check the instructions exiting memory and execute
        for stage in ['w', 'm']:
            # Save the instruction from each stage - it will be used more than once
            independInstr = copy(self.stages[stage].IR)
            if Globals.DEBUG:
                print "\t\t" + Globals.STAGE_NAMES[stage] + " received: " + independInstr.getStr()

            # Ensure that the independent instruction has the possibility to write
            if independInstr.instr not in Globals.NO_WRITE:
                # For each operand in the in the dependent instruction...
                for dependOp in dependOps:
                    # Check if it will be overwritten by another instruction further down the pipe
                    if independInstr[0].op in dependOp.op:
                        return True

        # Finally, check the instruction exiting the write stage
        if Globals.DEBUG:
            if self.stages['w'].outputBuf["Valid"]:
                print "\t\tWrite is writing to: " + self.stages['w'].outputBuf["Dest"].op
            else:
                print "\t\tWrite is not writing"

        for dependOp in dependOps:
            if self.stages['w'].outputBuf["Valid"] and (self.stages['w'].outputBuf["Dest"].op in dependOp.op):
                return True

        # All tests passed - no stall necessary
        return False

    def done (self):
        """
        @summary: Determine if algorithm has completed runtime

        @return: Returns 0 upon success (complete) or 1 for failure (incomplete)
        """

        for stage in self.stages:
            if 'f' != stage and "nop" != self.stages[stage].IR.instr:
                return 0

        return 1


class BasicRISC:
    """
    @summary: A basic, unforwarded, RISC datapath architecture capable of simulating
        simple instruction execution
    """

    def __init__ (self, ram):
        self.RAM = ram
        self.Rn = deepcopy(Globals.DEFAULT_REG_FILE)
        self.pipe = RISCPipe(self.Rn, self.RAM)

    def load (self):
        """
        @summary: Load all stages with the initial instruction (nop)
        """
        for stage in self.pipe.stages:
            if 'f' is not stage:
                self.pipe.stages[stage].IR = copy(Globals.INIT_INSTR)

    def tick (self):
        """
        @summary: This function will simulate one tick of the clock cycle and can be
                continuously called to simulate a running processor
        """
        self.pipe.tick()

    def done (self):
        return self.pipe.done()


if __name__ == "__main__":
    raise Exception("Cannot call this file directly")
