// cpu
`default_nettype none

`define CPU
//`define DEBUG

module m_branch(
  input wire clk,
  input wire [2:0] fun3,
  input wire [31:0] left,
  input wire [31:0] right,
  output reg branch_out
  );

always@(posedge clk)
begin
  case (fun3)
    3'b000:  branch_out <= left == right;
    3'b001:  branch_out <= left != right;
    3'b100:  branch_out <= $signed(left) <  $signed(right);
    3'b101:  branch_out <= $signed(left) >= $signed(right);
    3'b110:  branch_out <= left <  right;
    3'b111:  branch_out <= left >= right;
    default: branch_out <= 1'b0;
  endcase
end

endmodule

//module m_store(
//  input wire clk,
//  input wire [ 2:0] fun3,
//  input wire [31:0] val,
//  input wire [ 1:0] mod,
//  output reg [31:0] mem_out
//  );
//
//always@(posedge clk)
//begin
//  case (fun3)
//  3'b000:  mem_out[mod*8+7-:8] <= val[ 7:0];
//  3'b001:  mem_out[15:0]       <= val[15:0];
//  3'b010:  mem_out             <= val;
//  default: mem_out             <= 32'b0;
//  endcase
//end
//
//endmodule

module m_arith(
  input  wire clk,
  output reg  [31:0] out,
  input  wire [ 2:0] fun3,
  input  wire [31:0] left,
  input  wire [31:0] right,
  input  wire alt
  );

always@(posedge clk)
begin
  case (fun3)
  3'b000:  // ADD
    out <= (alt) ? left - right : left + right;
  3'b001:  // SLL
    out <= left << right[4:0];
  3'b010: // SLT
    out <= $signed(left) < $signed(right);
  3'b011: // SLTU
    out <= left < right;
  3'b100: // XOR
    out <= left ^ right;
  3'b101: // SRL, SRA
    out <= (alt) ? $signed(left) >>> right : left >> right;
  3'b110: // OR
    out <= left | right;
  3'b111: // AND
    out <= left & right;
  default:
    out <= 32'b0;
  endcase
end

endmodule

module riscv_i (
  input clk,
  input reset,
  output reg [9:0] led,
  input ser_rx,
  output ser_tx
  );

localparam MEMSIZE = 4095;
localparam ENTRY   = 'h8000_0000;

localparam LOAD     = 7'b000_0011;
localparam OP_IMM   = 7'b001_0011;
localparam OP       = 7'b011_0011;
localparam AUIPC    = 7'b001_0111;
localparam LUI      = 7'b011_0111;
localparam JALR     = 7'b110_0111;
localparam JAL      = 7'b110_1111;
localparam STORE    = 7'b010_0011;
localparam BRANCH   = 7'b110_0011;
localparam SYSTEM   = 7'b111_0011;
localparam MISC_MEM = 7'b000_1111;

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

reg [4:0] step;

wire [31:0] store_reg;
wire        branch_reg;
wire [31:0] arith0;
wire [31:0] arith3;
wire [31:0] arithlui;
//wire [31:0] index;
reg [31:0] x;
reg [31:0] y;
reg alt;
reg [31:0] out;
reg success = 1'b0;
reg fail;

//function [31:0] idx(input [31:0] addr);
//begin
//  idx = (addr - ENTRY) >> 2;
//end
//endfunction

//assign index = (arith0 - ENTRY) >> 2;

//function [31:0] extend(
//  input [ 2:0] fun3_in,
//  input [31:0] val_in,
//  input [ 1:0] mod_in
//  );
//reg [ 1:0] mod;
//reg [31:0] word;
//reg [ 2:0] size;
//begin
//  if (mod_in == 2'b0)
//    word = val_in;
//  else if (mod_in == 2'b10)
//    word = { 16'b0,  val_in[31:16] };
//  else if (mod_in == 2'b1)
//    word = {  8'b0,  val_in[31: 8] };
//  else
//    word = { 24'b0,  val_in[31:24] };
//
//  case (fun3_in)
//  3'b000: extend  = { {25{word[ 7]}}, word[ 6:0] }; // LB
//  3'b001: extend  = { {17{word[15]}}, word[14:0] }; // LH
//  3'b010: extend  = word;                           // LW
//  3'b100: extend  = { 24'b0, word[ 7:0] };          // LBU
//  3'b101: extend  = { 16'b0, word[15:0] };          // LHU
//  default: extend = 32'b0;
//  endcase
//  extend = 32'b0;
//end
//endfunction

m_arith  arith_m1 (.clk(clk), .out(arith0),   .fun3(3'b0), .left(x),     .right(y), .alt(alt));
m_arith  arith_m2 (.clk(clk), .out(arith3),   .fun3(fun3), .left(x),     .right(y), .alt(alt));
m_arith  arith_m3 (.clk(clk), .out(arithlui), .fun3(3'b0), .left(32'b0), .right(y), .alt(alt));
//m_store  store_1  (.clk(clk), .fun3(fun3),    .val(rgs[rs2]), .mod(arith0[1:0]), .mem_out(store_reg));
m_branch branch_1 (.clk(clk), .fun3(fun3),    .left(rgs[rs1]), .right(rgs[rs2]), .branch_out(branch_reg));

integer i;

initial 
begin
  $readmemh("tests/rv32ui-p-addi.dat", mem);

  for (i = 0; i < 32; i = i + 1)
    rgs[i] <= 32'b0;
end

`ifdef CPU
always @(posedge clk)
begin

  if (reset)
  begin
    PC   <= ENTRY;
    step <= 5'b0;
  end

  // fetch

  if (~step[0])
  begin
    ins  <= mem[(PC - ENTRY) >> 2];
    step <= 5'b1;
  end

  // decode

  if (step[0])
  begin

    $display("step 1: PC  %h ins %h", PC, ins);

    imm_i <= { { 20{ins[31]}}, ins[31:20] };
    imm_s <= { { 20{ins[31]}}, ins[31:25], ins[11:7] };
    imm_b <= { { 20{ins[31]}}, ins[ 7: 7], ins[30:25], ins[11: 8], 1'b0 };
    imm_u <= { ins[31:12], 12'b0 };
    imm_j <= { { 12{ins[31]}}, ins[19:12], ins[20:20], ins[30:21], 1'b0 };

    op    <= ins[ 6: 0];
    fun3  <= ins[14:12];
    rd    <= ins[11: 7];
    rs1   <= ins[19:15];
    rs2   <= ins[24:20];

    step <= step << 1;
  end

  // execute

  if (step[1])
  begin

    $display("step 2: op  %08b fn3 %08b  rd %08d rs1 %08d rs2 %08d", op, fun3, rd, rs1, rs2);

    case (op)
      OP_IMM  : x <= PC;      // op_imm
      BRANCH  : x <= PC;      // branch
      JAL     : x <= PC;      // jal
      default : x <= rgs[rs1];
    endcase

    case (op)
      LOAD    : y <= imm_i;    // load
      STORE   : y <= imm_s;    // store
      OP_IMM  : y <= imm_i;    // op_imm
      OP      : y <= rgs[rs2]; // op
      AUIPC   : y <= imm_u;    // auipc
      LUI     : y <= imm_u;    // lui
      BRANCH  : y <= imm_b;    // branch
      JALR    : y <= imm_i;    // jalr
      JAL     : y <= imm_j;    // jal
      SYSTEM  : y <= imm_i;    // system
      MISC_MEM: y <= 32'b0;    // misc_mem
      default : y <= 32'b0;
    endcase

    case (op)
      7'b001_0011: // op_imm
        if (fun3 == 3'b101)    // SRL
          alt <= 1'b1 & ins[30];
      7'b011_0011: // op
        case (fun3)
          3'b101: alt <= 1'b1 & ins[30]; // SRL
          3'b0  : alt <= 1'b1 & ins[30]; // ADD
        endcase
      default:
        alt <= 1'b0;
    endcase
    step <= step << 1;
  end

  // for arith to process
  if (step[2])
    step <= step << 1;

  if (step[3])
  begin

    if (op == OP_IMM || op == OP)
      out <= arith3;
    else if (op == LUI)
      out <= arithlui;
    else if (op == JALR)
      out <= arith0 & 32'hfffffffe;
    else if (op == AUIPC || op == BRANCH || op == JAL)
      out <= arith0;
    else if (op == SYSTEM)
      if (ins == 32'hc0001073)
        success <= 1'b1;
      else if (fun3 == 3'b0 && rgs[3] > 1)
        fail <= 1'b0;
    else
      out <= 32'b0;

    // LOAD from memory later
    // out <= mem[idx];

    step <= step << 1;
  end

  // store

  if (step[4])
  begin

    $display("step 3: out %h   x %h   y %h alt %08b ar0 %h ar3 %h arl %h", out, x, y, alt, arith0, arith3, arithlui);

    if (~rd)
    begin
      if (op == LOAD || op == OP_IMM || op == OP || op == AUIPC || op == LUI)
        rgs[rd] <= out;
      else if (op == JALR || op == JAL)
        rgs[rd] <= PC + 4;
    end

    // STORE from memory later
    // mem[idx] <= store_reg;

  // debugging information
    `ifdef DEBUG
    $display($time, " PC   : %08x OP: %08x", PC, ins);
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

    if (op == JAL || op == JALR || (op == BRANCH && branch_reg))
      PC <= out;
    else
      PC <= PC + 4;

    step <= 5'b1;
  end

  if (success)
    begin
    $display("Success");
    led <= 10'b1010101010;
    $finish;
    end
  else if (fail)
    begin
    $display("Failed");
    led <= 10'b101010101;
    $finish;
    end
  else
    led <= PC[9:0];

end
`endif

endmodule
