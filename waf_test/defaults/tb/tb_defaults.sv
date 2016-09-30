`timescale 1ns / 10ps

`include "defaults.vh"
`include "tb_defaults.vh"
`define RESOURCES "../defaults/resources"

module tb_defaults;

    integer fd;
    string file_str;
    const string file_name = {`RESOURCES,"/defaults.txt"};
    //string file_name;
    
    initial begin
        //$value$plusargs ("RESOURCES=%s", file_name);
        //file_name = {file_name, "/defaults.txt"};
        fd = $fopen (file_name, "r");
        if (fd == 0) begin
            $display ("%6dns Default TB: Failed to open default file %s for reading!",
                $time, file_name);
            $stop; 
        end else begin
            $display ("%6dns Default TB: Opened default file %s for reading.",
                $time, file_name);
            $fscanf(fd, "%s", file_str);
            if (file_str != "Defaults") begin
                $display ("%6dns Default TB: Failed to Read String \"Defaults\". Read \"%s\" instead", $time, file_str);
                $stop;
            end else begin
                $display ("%6dns Default TB: Read String \"%s\"",
                    $time, file_str);
            end
        end
    end

    logic [15:0] out;
    logic [15:0] out_n_incr2;
    reg [15:0] in;

    add_define dut (
        .b(out),
        .a(in)
    );

    assign out_n_incr2 = out + `INCREMENT2;

    initial begin
        in = 14;
       
        if (out_n_incr2 != 16) begin
            $display ("%6dns Default TB: Something went wrong. Got %d instead of 16.", $time, out_n_incr2);
            $stop;
        end else begin
            $display ("%6dns Default TB: Got 16 as expected.", $time);
            $stop(0);
        end
    end

endmodule

 
