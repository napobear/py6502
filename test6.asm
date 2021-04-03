; Test subroutines

	LDX #0
LOOP:
	JSR INCX
	CPX #10
	BNE LOOP
	JMP ENDIT
INCX: INX
	RTS
ENDIT: NOP

	