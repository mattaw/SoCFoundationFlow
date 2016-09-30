
`timescale 1ns / 10ps

`include "defaults.vh"
`include "tb_defaults.vh"

module foo;

    logic [15:0] out;
    logic [15:0] out_n_incr2;
    reg [15:0] in;

    add_one_l4 dut (
        .b(out),
        .a(in)
    );

    assign out_n_incr2 = out + `INCREMENT2;

    initial begin
        #1;
        in = 14;
        #1;

        if (out_n_incr2 != 17) begin
            $display ("%6dns Default TB: Something went wrong. Got %d instead of 16.", $time, out_n_incr2);
            $stop;
        end else begin
            $display ("%6dns Default TB: Got 16 as expected.", $time);
            $stop(0);
        end
    end

endmodule


