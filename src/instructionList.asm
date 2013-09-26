# File: insturctionList.asm
# Author: David Zemon
# Purpose: Provide a brief set of instructions to evaluate pipeline optimization effectiveness
#
# NOTE: No blank lines are allowed - any line that is not a valid instruction must begin with '#'
#
mov R0, #128
mov R1, #2
div R2, R0, R1
sjmp #2
nop
mov F0, #66.6
mov F1, #99.9
mov @R0, #0
add R0, R0, #1
mov @R0, #1
add R0, R0, #1
mov @R0, #2
add R0, R0, #1
mov @R0, #3
mov R1, #4
add R2, R1, R0
mul R3, R2, R1
# Begin floating point instructions
mov F0, #2.5
mov F1, #5
mov R3, #100
mov R3, #20
mul F2, F1, F0
mov F0, #2.5
mov F1, #5
mul F2, F0, F1
mov R0, #10
nop
mov R0, #11
mov @R0, #20
sjmp #8
mov @R0, #777
nop
nop
nop
nop
nop
nop
nop
mov R0, #0
mov R1, #666
mov @R0, R1
mov R1, #64
mov R0, #8
mov @R1, R0
add R1, R1, #1
djnz R0, #-3
