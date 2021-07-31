// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

	@0
	D=M
	@i
	M=D // i=R0
	@2
	M=0 // R2=0
(LOOP)
	@i
	MD=M-1
	@END
	D;JLT // for i in 0...R0
	@1
	D=M
	@2
	M=D+M // R2 += R1
	@LOOP
	0;JMP
(END)
	@END
	0;JMP