// top

`default_nettype none

//`define SIM 

module riscv_cpu (
  input Clk,
  input [3:0] Switch,
  output [9:0] Led_Out,
  output Uart_Tx,
  input  Uart_Rx
	);

reg Clk50 = 1'b0;
reg ResetInput = 1'b1;

`ifdef SIM
initial begin
  #5 Clk50 = ~Clk50;
  #5 Clk50 = ~Clk50;
  #5 ResetInput = ~ResetInput;
  forever #1 Clk50 = ~Clk50;
end
`else
always@(posedge Clk)
  Clk50 <= ~Clk50;
`endif

reg ClkDiv = 1'b0;
//reg [21:0] Ctr = 22'b0; // 50 Mhz / 2 ^ 23 ~ 6 Hz
reg [16:0] Ctr = 17'b0; // 50 Mhz / 2 ^ 18 ~ 190 Hz
//reg [3:0] Ctr = 4'b0; // 50 Mhz / 2 ^ 18 ~ 190 Hz

always@(posedge Clk50) begin
  { ClkDiv, Ctr } <= Ctr + 1'b1;
  end

riscv_i cpu_i(
    .clk   (ClkDiv),
    .reset (Switch[0]),
    .reset (ResetInput),
    .led   (Led_Out),
    .ser_tx(Uart_Tx),
    .ser_rx(Uart_Rx)
  );

endmodule
