"""
@author: David Zemon

@summary: Provide necessary components to create a scoreboard type pipeline
"""

from copy import deepcopy, copy
import Globals
from UniversalComponents import FltFU, IntFU


class ScoreboardPipe:
    """
    @summary: Contains the read ops, execute, and write stages of a pipe utilizing a scoreboard
    """

    def __init__ (self, Rn, ram, FUs):
        self.Rn = Rn
        self.RAM = ram
        self.result = {'A': None, 'B': None}
        self.FUs = FUs
        self.busy = False
        self.IR = copy(Globals.INIT_INSTR)
        self.stage = None

    def issue (self, instr):
        self.IR = copy(instr)
        self.stage = 'I'

    def tick (self):
        # If the pipe is unused, return
        if None == self.stage:
            return

        # If the the stage is waiting on opperands
        elif 'R' == self.stage:
            # Check the opperands
            if self.readOpsCheck():
                # And if they're available, find an available functional unit
                for FU in self.FUs[self.IR.getFU()]:
                    # Check if the FU is busy...
                    if not FU["busy"]:
                        # Operands and functional unit available! Load 'er up!
                        FU["FU"].load(self.IR.instr, self.getSrcValues())
                        FU["busy"] = True
                        self.runningFU = FU
                        self.stage = 'E'
                        return
        # Else check if the instruction is currently executing
        elif 'E' == self.stage:
            self.runningFU.tick()
            if self.runningFU.ding():
                self.stage = 'W'
                return
        # Finally, check if the instruction can write its result
        elif 'W' == self.stage:
            # TODO: Need to make jumps happen

            # If the instruction doesn't write or if WAR hazards are satisfied
            if self.IR.instr in Globals.NO_WRITE or self.writeCheck():
                if self.IR.instr not in Globals.NO_WRITE:
                    self.IR[0].setVal(self.runningFU["result"]["A"])
                self.runningFU["busy"] = False
                self.runningFU = None
                self.stage = None

    def readOpsCheck (self):
        """
        @summary: Are all source operands availabe for reading?
        """
        raise Exception("Need to implement ScoreboardPipe.readOpsCheck()")

    def getSrcValues (self):
        retVal = {'A': None, 'B': None}

        # Handle jumps
        if self.IR.instr in Globals.JUMP_INSTRS:
            if "sjmp" == self.IR.instr:
                retVal = {'A': self.IR.getSrcOpVal(0), 'B': self.parent.PC}
            elif "djnz" == self.IR.instr:
                retVal = {'A': self.IR.getSrcOpVal(0), 'B': self.parent.PC + self.IR.getSrcOpVal(1)}
            else:
                retVal = {'A': self.IR.getSrcOpVal(0), 'B': self.IR.getSrcOpVal(1)}
        # Followed by moves...
        elif "mov" == self.IR.instr:
            if self.IR.ops[0].isLdStrOp():
                retVal['A'] = self.IR.getSrcOpVal(0)
            retVal['B'] = self.IR.getSrcOpVal(1)
        # And finally, everything else
        else:
            retVal = {'A': self.IR.getSrcOpVal(1), 'B': self.IR.getSrcOpVal(2)}

        return retVal


class ScoreboardRISC:
    """
    @summary: A simple example of a RISC pipeline using the scoreboard technique
    """

    def __init__ (self, ram):
        self.RAM = ram
        self.Rn = deepcopy(Globals.DEFAULT_REG_FILE)
        self.PC = 0
        self.instrPipes = []

        # Create a sample of each functional unit
        fltFU = {"result": {'A': None, 'B': None}, "busy": False}
        intFU = {"result": {'A': None, 'B': None}, "busy": False}
        fltFU["FU"] = FltFU(fltFU["result"])
        intFU["FU"] = IntFU(intFU["result"])

        # Copy the samples to create numerous functional units
        self.FUs = {"FLT": [fltFU] * Globals.FLT_PIPES, "INT": [intFU] * Globals.INT_PIPES}

    def tick (self):
        for pipe in self.instrPipes:
            pipe.tick()
        nextInstr = self.RAM[self.PC]
        if self.checkIssue(next):
            self.instrPipes.append(ScoreboardPipe(self.Rn, self.RAM, self.FUs))
            self.PC += 1

    def checkIssue (self, instr):
        """
        @summary: Instruction may issue IFF there are no WAW, or structural hazards

        @return: Returns True if the instruction can issue, false otherwise
        """

        # Check for WAW
        # If the instruction doesn't write, there can be no WAW
        if instr.instr not in Globals.NO_WRITE:
            # Check the instructions in each pipe
            for pipe in self.instrPipes:
                # If the destination operands match, stall
                if pipe.instr.getDest() == instr.getDest():
                    return True

        # Check for structural hazard
        neededFU = instr.getFU()


if __name__ == "__main__":
    raise Exception("Cannot call this file directly")
