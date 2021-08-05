// top

//`define SIM

`ifdef SIM

module riscv_cpu (
  input [3:0] Switch,
  output [7:0] Led_Out,
  output Uart_Tx,
  input  Uart_Rx
	);

wire [7:0] soc_led;
reg Clk;

riscv_i cpu_i(
    .clk(Clk),
    .reset(Switch[0]),
    .led(Led_Out),
    .ser_tx(Uart_Tx),
    .ser_rx(Uart_Rx)
);

initial
begin
  Clk = 1'b0;
  forever #10 Clk = ~Clk;
end

`else

module riscv_cpu (
  input Clk,
  input [3:0] Switch,
  output [7:0] Led_Out,
  output Uart_Tx,
  input  Uart_Rx
	);

wire [7:0] soc_led;

riscv_i cpu_i(
    .clk(Clk),
    .reset(Switch[0]),
    .led(Led_Out),
    .ser_tx(Uart_Tx),
    .ser_rx(Uart_Rx)
);

`endif

endmodule
