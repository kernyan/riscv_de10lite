module riscv_cpu (
  input Clk,
  input [3:0] Switch,
  output [7:0] Led_Out,
  output Uart_Tx,
  input  Uart_Rx
	);

	wire [7:0] soc_led;

	attosoc soc_i(
			.clk(Clk),
			.reset(Switch[0]),
			.led(Led_Out),
			.ser_tx(Uart_Tx),
			.ser_rx(Uart_Rx)
	);

endmodule
