`include "defaults.vh"

module add_define (
    input [15:0 ] a,
    output [15:0]  b
);

assign b = a + `INCREMENT;


endmodule

 
