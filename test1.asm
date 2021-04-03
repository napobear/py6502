; This is a comment
   ;So is this.

 LDY #$DF
 STY $23
 LDY #0
 LDY $23
 LDA #$34
 ROL
 TAX
 LDA #$90
 ADC #$10
 ORA #1
 PHA
 LDA #0
 PLA
 SEC
 SED
 