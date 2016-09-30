module add_one_l3 (
    input [15:0 ] a,
    output [15:0]  b
);

add_one_l2 a2 (
    .a(a),
    .b(b)
);

logic [15:0] c;
logic [15:0] d;

add_one_l2_5 a2_5 (
    .a(c),
    .b(d)
);
endmodule

