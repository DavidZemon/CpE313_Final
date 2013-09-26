DEBUG = True

basicRAM = None

COMMENT_CHARS = ['#']

RAM_SIZE = 256
RAM = [None] * RAM_SIZE

DEFAULT_REG_FILE = {"R0": None, "R1": None, "R2": None, "R3": None, "F0": None, "F1": None, "F2": None, "F3": None}
REVERSE_STAGE_ORDER = ['w', 'm', 'e', 'd', 'f']
STAGE_NAMES = {'f': "FETCH", 'd': "DECODE", 'e': "EXECUTE", 'm': "MEMORY", 'w': "WRITE"}
INIT_INSTR = None

# Instruction categories
MOV_INSTRS = ["mov"]
MATH_INSTRS = ["add", "sub", "mul", "div"]
LOGIC_INSTRS = ["or", "and", "nand", "xor"]
SHIFT_INSTRS = ["shl", "shr"]
UCND_JMP_INSTRS = ["sjmp", "ljmp"]
CND_JMP_INSTRS = ["jz", "djnz"]
JUMP_INSTRS = UCND_JMP_INSTRS + CND_JMP_INSTRS

# Miscellaneous instruction thing-a-ma-jigs
DOUBLE_OPERANDS = MOV_INSTRS + SHIFT_INSTRS
TRIPLE_OPERANDS = MATH_INSTRS + LOGIC_INSTRS
MULTI_OPERANDS = DOUBLE_OPERANDS + TRIPLE_OPERANDS
NO_WRITE = ["nop", "jz"] + UCND_JMP_INSTRS
NO_READ = ["nop"] + UCND_JMP_INSTRS

# Functional Unit Constants
INTEGER_DELAY = 2
FLOATING_POINT_DELAY = 5
MISC_DELAY = 1
FLT_PIPES = 1
INT_PIPES = 3

if __name__ == "__main__":
    raise Exception("Cannot call this file directly")