
module dual_uart (
    input logic clk, // The master clock for this module
    input logic rst, // Synchronous reset.
    input logic port_select // Select which UART is connected
    input logic rx, // Incoming serial line
    output logic tx, // Outgoing serial line
    input logic transmit, // Signal to transmit
    input logic [7:0] tx_byte, // Byte to transmit
    output logic received, // Indicated that a byte has been received.
    output logic [7:0] rx_byte, // Byte received
    output logic is_receiving, // Low when receive line is idle.
    output logic is_transmitting, // Low when transmit line is idle.
    output logic recv_error // Indicates error in receiving packet.
    );
   
    logic [1:0] rx_i; // Incoming serial line
    logic [1:0] tx_i; // Outgoing serial line
    logic [1:0] transmit_i; // Signal to transmit
    logic [1:0][7:0] tx_byte_i; // Byte to transmit
    logic [1:0] received_i; // Indicated that a byte has been received.
    logic [1:0][7:0] rx_byte_i; // Byte received
    logic [1:0] is_receiving_i; // Low when receive line is idle.
    logic [1:0] is_transmitting_i; // Low when transmit line is idle.
    logic [1:0] recv_error_i;// Indicates error in receiving packet.

assign rx_i[0] = (port_select) ? 1'b0 : rx;
assign rx_i[1] = (!port_select) ? 1'b0 : rx;
assign transmit_i[0] = (port_select) ? 1'b0 : transmit;
assign transmit_i[1] = (!port_select) ? 1'b0 : transmit;
assign tx_byte_i[0] = (port_select) ? 1'b0 : tx_byte;
assign tx_byte_i[1] = (!port_select) ? 1'b0 : tx_byte;

assign tx = (port_select) ? tx_i[1] : tx_i[0];
assign received = (port_select) ? received_i[1] : received_i[0];
assign rx_byte = (port_select) ? rx_byte_i[1] : rx_byte_i[0];
assign is_receiving = (port_select) ? is_receiving_i[1] : is_receiving_i[0];
assign is_transmitting = (port_select) ? is_transmitting_i[1] : is_transmitting_i[0];
assign recv_error = (port_select) ? recv_error_i[1] : recv_error_i[0];


uart uart_0 (
    .clk,
    .rst,
    .rx(rx[0]),
    .tx(tx[0]),
    .transmit(transmit[0]),
    .tx_byte(tx_byte[0]),
    .received(received[0]),
    .rx_byte(rx_byte[0]),
    .is_receiving(is_receiving[0]),
    .is_transmitting(is_transmitting[0]),
    .recv_error(recv_error[0]),
    .port_select(port_select[0]) );
    
uart uart_1 (
    .clk,
    .rst,
    .rx(rx[1]),
    .tx(tx[1]),
    .transmit(transmit[1]),
    .tx_byte(tx_byte[1]),
    .received(received[1]),
    .rx_byte(rx_byte[1]),
    .is_receiving(is_receiving[1]),
    .is_transmitting(is_transmitting[1]),
    .recv_error(recv_error[1]),
    .port_select(port_select[1]) );
 
