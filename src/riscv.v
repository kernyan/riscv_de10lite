// cpu

`define CPU

module riscv_i (
  input clk,
  input reset,
  output reg [7:0] led,
  input ser_rx,
  output ser_tx
  );

/*
Strategy
1. read memory
2. fetch
3. decode
4. execute
5. store
*/

localparam MEMSIZE = 2055;
localparam ENTRY   = 'h8000_0000;

reg [31:0] mem[0:MEMSIZE];
reg [31:0] PC;

function [31:0] idx(input [31:0] addr);
begin
idx = (addr - ENTRY) >> 2;
end
endfunction

initial 
begin
  $readmemh("tests/rv32ui-p-fence_i.dat", mem); 
  PC = ENTRY;
  #1000 $finish;
end

`ifdef CPU
always @(posedge clk)
begin
  $display("%d %08x %08x", $time, PC, mem[idx(PC)]);
  PC += 4;
end
`endif

endmodule
