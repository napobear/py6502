; Testing filling 10 memory locations with the
; values from 0 to 9

; Now with labels

START   = 0
END     = 10

        LDX #START
FOO:    TXA
        STA $10,X
        INX
        CPX #END
        BNE FOO
