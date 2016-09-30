module add_one_l4 (
    input [15:0 ] a,
    output [15:0]  b
);

add_one_l3 a3 (
    .a(a),
    .b(b)
);

endmodule

