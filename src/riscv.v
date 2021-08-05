// cpu

`define CPU
//`define DEBUG

module riscv_i (
  input clk,
  input reset,
  output reg [7:0] led,
  input ser_rx,
  output ser_tx
  );

localparam MEMSIZE = 2055;
localparam ENTRY   = 'h8000_0000;

reg [31:0] mem[0:MEMSIZE];

reg [31:0] PC;
reg [31:0] rgs[0:31];

reg [31:0] ins;
reg [ 6:0] op;
reg [ 2:0] fun3;
reg [31:0] imm_i;
reg [31:0] imm_s;
reg [31:0] imm_b;
reg [31:0] imm_u;
reg [31:0] imm_j;

reg [ 4:0] rd;
reg [ 4:0] rs1;
reg [ 4:0] rs2;

// working reg

reg [31:0] x;
reg [31:0] y;
reg alt;
reg [2:0] byte_idx;
reg [31:0] out;
reg success;
reg fail;

function [31:0] idx(input [31:0] addr);
begin
  idx = (addr - ENTRY) >> 2;
end
endfunction

function [31:0] extend(
  input [ 2:0] fun3_in,
  input [31:0] val_in,
  input [ 1:0] mod_in
  );
reg [ 1:0] mod;
reg [31:0] word;
reg [ 2:0] size;
begin
  if (mod_in == 2'b0)
    word = val_in;
  else if (mod_in == 2'b10)
    word = { 16'b0,  val_in[31:16] };
  else if (mod_in == 2'b1)
    word = {  8'b0,  val_in[31: 8] };
  else
    word = { 24'b0,  val_in[31:24] };

  case (fun3_in)
  3'b000: extend = { {25{word[ 7]}}, word[ 6:0] }; // LB
  3'b001: extend = { {17{word[15]}}, word[14:0] }; // LH
  3'b010: extend = word;                           // LW
  3'b100: extend = { 24'b0, word[ 7:0] };          // LBU
  3'b101: extend = { 16'b0, word[15:0] };          // LHU
  endcase
end
endfunction

task store(
  input [ 2:0] fun3_in,
  input [31:0] val_in,
  input [ 1:0] mod_in,
  output [31:0] mem_out
  );
begin
  case (fun3_in)
  3'b000: mem_out[mod_in*8+7-:8] = val_in[ 7:0];
  3'b001: mem_out[15:0] = val_in[15:0];
  3'b010: mem_out = val_in;
  endcase
end
endtask

function [31:0] arith(
  input [ 2:0] fun3_in,
  input [31:0] x_in,
  input [31:0] y_in,
  input alt_in
  );
begin
  case (fun3_in)
  3'b000:  // ADD
    if (alt_in)
      arith = x_in - y_in;
    else
      arith = x_in + y_in;
  3'b001:  // SLL
    arith = x << y[4:0];
  3'b010: // SLT
    arith = $signed(x) < $signed(y);
  3'b011: // SLTU
    arith = x < y;
  3'b100: // XOR
    arith = x ^ y;
  3'b101: // SRL, SRA
    if (alt_in)
      arith = $signed(x) >>> y;
    else
      arith = x >> y;
  3'b110: // OR
    arith = x | y;
  3'b111: // AND
    arith = x & y;
  endcase
end
endfunction

integer i;

initial 
begin
  $readmemh("tests/rv32ui-p-and.dat", mem);
  PC = ENTRY;

  for (i = 0; i < 32; i += 1)
    rgs[i] = 32'b0;
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

  op    = ins[ 6: 0];
  fun3  = ins[14:12];
  rd    = ins[11: 7];
  rs1   = ins[19:15];
  rs2   = ins[24:20];

  // execute

  case (op)
    7'b001_0111: x = PC;
    7'b110_0011: x = PC;
    7'b110_1111: x = PC;
    default    : x = rgs[rs1];
  endcase

  case (op)
    7'b000_0011: y = imm_i;    // load
    7'b010_0011: y = imm_s;    // store
    7'b001_0011: y = imm_i;    // op_imm
    7'b011_0011: y = rgs[rs2]; // op
    7'b001_0111: y = imm_u;    // auipc
    7'b011_0111: y = imm_u;    // lui
    7'b110_0011: y = imm_b;    // branch
    7'b110_0111: y = imm_i;    // jalr
    7'b110_1111: y = imm_j;    // jal
    7'b111_0011: y = imm_i;    // system
    7'b000_1111: y = 32'b0;    // misc_mem
  endcase

  case (op)
    7'b001_0011: // op_imm
      if (fun3 == 3'b101)    // SRL
        alt = 1'b1 & ins[30];
    7'b011_0011: // op
      case (fun3)
        3'b101: alt = 1'b1 & ins[30]; // SRL
        3'b0  : alt = 1'b1 & ins[30]; // ADD
      endcase
    default:
      alt = 1'b0;
  endcase

  byte_idx = arith(3'b0, x, y, alt) % 4;
    
  case (op)
    7'b000_0011: out = extend(fun3, mem[idx(arith(3'b0, x, y, alt))]   , byte_idx); // load
    7'b010_0011: store(fun3, rgs[rs2], mem[idx(arith(3'b0, x, y, alt))], byte_idx); // store
    7'b001_0011: out = arith(fun3, x, y, alt);  // op_imm
    7'b011_0011: out = arith(fun3, x, y, alt);  // op
    7'b001_0111: out = arith(3'b0, x, y, alt);  // auipc
    7'b011_0111: out = arith(3'b0, 32'b0, y, alt); // lui
    7'b110_0011: out = arith(3'b0, x, y, alt);  // branch
    7'b110_0111: out = arith(3'b0, x, y, alt) & 32'hfffffffe; // jalr
    7'b110_1111: out = arith(3'b0, x, y, alt);  // jal
    7'b111_0011:                                // system
      if (ins == 32'hc0001073) // hack to match test exit condition
        success = 1'b1;
      else if (fun3 == 3'b0 && rgs[3] > 1)      // hack to match test fail condition (gp reg)
        fail = 1'b0;
    7'b000_1111:;                               // misc_mem
  endcase

  // store

  if (rd != 5'b0)
    case (op)
      7'b000_0011: rgs[rd] = out; // load
      7'b001_0011: rgs[rd] = out; // op_imm
      7'b011_0011: rgs[rd] = out; // op
      7'b001_0111: rgs[rd] = out; // auipc
      7'b011_0111: rgs[rd] = out; // lui
      7'b110_0111: rgs[rd] = PC + 4; // jalr
      7'b110_1111: rgs[rd] = PC + 4; // jal
    endcase

  // debugging information
  `ifdef DEBUG
  $display("PC   : %08x OP: %08x", PC, ins);
  $display("imm_i: %08x", imm_i);
  $display("imm_s: %08x", imm_s);
  $display("imm_b: %08x", imm_b);
  $display("imm_u: %08x", imm_u);
  $display("imm_j: %08x", imm_j);
  $display("   x0: %08x", rgs[0]);
  $display("   a0: %08x", rgs[10]);
  $display("   ra: %08x", rgs[1]);
  $display("   sp: %08x", rgs[2]);
  $display("   a4: %08x", rgs[14]);
  $display("   a5: %08x", rgs[15]);
  $display("   t2: %08x", rgs[27]);
  $display("   t4: %08x", rgs[29]);
  $display("    x: %08x", x);
  $display("    y: %08x", y);
  $display("  out: %08x\n", out);
  `endif

  // jump

  case (op)
    7'b110_1111: // JAL
      PC = out;
    7'b110_0111: // JALR
      PC = out;
    7'b110_0011: // BRANCH
      case (fun3)
      3'b000: if (rgs[rs1] == rgs[rs2])                   PC = out; else PC += 4; // BEQ
      3'b001: if (rgs[rs1] != rgs[rs2])                   PC = out; else PC += 4; // BNE
      3'b100: if ($signed(rgs[rs1])  < $signed(rgs[rs2])) PC = out; else PC += 4; // BLT
      3'b101: if ($signed(rgs[rs1]) >= $signed(rgs[rs2])) PC = out; else PC += 4; // BGE
      3'b110: if (rgs[rs1]  < rgs[rs2])                   PC = out; else PC += 4; // BLTU
      3'b111: if (rgs[rs1] >= rgs[rs2])                   PC = out; else PC += 4; // BGEU
      endcase
    default:
      PC += 4;
  endcase

  if (success)
    begin
    $display("Success");
    $finish;
    end
  else if (fail)
    begin
    $display("Failed");
    $finish;
    end
end
`endif

endmodule
