module riscv_cpu (
  input Clk,
  input [3:0] Switch,
  output [7:0] Led_Out,
  output Uart_Tx,
  input  Uart_Rx
	);

	//reg clk50 = 1'b0;
	//always @(posedge Clk)
	//		clk50 <= ~clk50;

	//wire clk;
	//BUFGCTRL bufg_i (
	//		.I0(clk50),
	//		.CE0(1'b1),
	//		.S0(1'b1),
	//		.O(clk)
	//);

	wire [7:0] soc_led;

	attosoc soc_i(
			.clk(Clk),
			.reset(Switch[0]),
			.led(Led_Out),
			.ser_tx(Uart_Tx),
			.ser_rx(Uart_Rx)
	);

	//generate
	//		genvar i;
	//		for (i = 0; i < 8; i = i+1)
	//		begin : LedConnect
	//				assign Led_Out[i] = soc_led[i];
	//		end
	//endgenerate

endmodule
