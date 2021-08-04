// cpu

`define CPU
`define DEBUG

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

reg [31:0] ins;
reg [31:0] imm_i;
reg [31:0] imm_s;
reg [31:0] imm_b;
reg [31:0] imm_u;
reg [31:0] imm_j;

initial 
begin
  $readmemh("tests/rv32ui-p-fence_i.dat", mem); 
  PC = ENTRY;
  #1000 $finish;
end

`ifdef CPU
always @(posedge clk)
begin
  // fetch
  ins = mem[idx(PC)];

  // decode

  imm_i = { { 20{ins[31]}}, ins[31:20] };
  imm_s = { { 20{ins[31]}}, ins[31:25], ins[11:7] };
  imm_b = { { 21{ins[31]}}, ins[ 7: 7], ins[30:25], ins[11: 8], 1'b0 };
  imm_u = { ins[31:12], 12'b0 };
  imm_j = { { 12{ins[31]}}, ins[19:12], ins[20:20], ins[30:21], 1'b0 };


  // execute

  // store

  // debugging information
  `ifdef DEBUG
  $display("PC   : %08x OP: %08x", PC, ins);
  $display("imm_i: %08x", imm_i);
  $display("imm_s: %08x", imm_s);
  $display("imm_b: %08x", imm_b);
  $display("imm_u: %08x", imm_u);
  $display("imm_j: %08x\n", imm_j);
  `endif

  PC += 4;

end
`endif

endmodule























