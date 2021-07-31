// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

	@is_blackened
	M=0
	@FILL
	0;JMP
(POLL)
// Check if any key down
	@KBD
	D=M
	@TRY_BLACKEN
	D;JNE
// Tries to whiten if flag not set
	@color
	M=0
	@is_blackened
	D=M
	@FILL
	D;JNE
	@POLL
	0;JMP
// Tries to blacken if flag is set
(TRY_BLACKEN)
// Can only load 15b data so need to manufacture 0xFFFF
	D=0
	D=D-1
	@color
	M=D
	@is_blackened
	D=M
	@FILL
	D;JEQ
	@POLL
	0;JMP

// Fills screen
(FILL)
	@8192
	D=A
	@i
	M=D	
(LOOP)
	@i
	MD=M-1
	@END
	D;JLT
// Update screen
	@SCREEN
	D=A+D
	@temp
	M=D
	@color
	D=M
	@temp
	A=M
	M=D
	@LOOP
	0;JMP
(END)
// Flip flag to indicate screen was changed
	@is_blackened
	M=!M
	@POLL
	0;JMP
