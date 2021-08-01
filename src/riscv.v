// cpu

//`define CPU

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

`define MEM_SIZE 2055

reg [31:0] mem[0:`MEM_SIZE];
integer i;

initial 
begin
  $readmemh("tests/rv32ui-p-fence_i.dat", mem); 

  for(i=0; i <= `MEM_SIZE; i = i + 1)
    $display("Memory [%0d] = %08x", i, mem[i]);
  
  #1000 $finish;
end

`ifdef CPU
always @(posedge clk)
begin
  $display("%d", $time);
end
`endif

endmodule
