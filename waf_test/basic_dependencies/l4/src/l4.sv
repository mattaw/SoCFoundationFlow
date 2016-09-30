module add_one_l4 (
);

logic [15:0] a;
logic [15:0] b;


add_one_l3 a3 (
    .a(a),
    .b(b)
);

endmodule

