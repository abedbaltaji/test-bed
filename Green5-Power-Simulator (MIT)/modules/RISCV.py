import re
import matplotlib.pyplot as plt

from modules.MemFile import MemFile
from modules.HelperFunctions import HelperFunctions

# nov 10 updates:
# supports verbose
# supports negative hex: -0x1 format
# hex helper function checks if input integer - casts to int first in case if string

class RISCV:
    def __init__(self, codefilepath, memfilepath, verbose=False):
        self.codefilepath = codefilepath
        self.steppable = True
        self.ended = False #0 if reaches wfi
        self.memfilepath = memfilepath
        self.memfile = MemFile()
        self.memfile.load(memfilepath)
        self.registers = {} # x1 thru x31, x0 is 0
        self.cycle_counter = 0
        self.verbose = verbose

        # Flags vector
        self.flags_vector ={
            'N': 0,
            'Z': 0,
            'C': 0,
            'V': 0,
            'Q': 0
        }

        # initializes the alternate register names
        self.reg_name = {}
        self._load_reg_names()

        assert self.codefilepath != memfilepath, "Memory and code should have different filepaths."
        
        codefilelines = open(codefilepath, "r").readlines()
        self.codefilelines = []
        for line in codefilelines:
            if line.strip() == "":
                continue
            self.codefilelines.append(line)
        print("\n--> Code file lines are read successfully.\n")
            ## we want to clean this to ensure no blank lines, for line counting purpose
         
        self.pc = 0
        self.instruction_power_dict = {}
        self.previous_inst = ""
        self.inst_line_power_list = [] #(inst, power) for plotting later
        # history of instructions run
        self.plot = False

        # ## RISC-V instructions
        # self.REG = ["sll", "srl", "sra", "xor", "add", "sub", "mul", "mulhu",
        #     "mulh", "mulhsu", "div", "divu", "rem", "remu", "and", "or", "sltu", "slt"]
        # # slt, divu, remu, mulhu,| mulh, mulhsu
        # self.IMM = ["slli", "srli", "srai", "xori", "addi", "andi", "ori",
        #     "sltiu", "slti"] #TODO: subi is not an inst.
        # # slti

        # self.BRANCH = ["beq", "bne", "blt", "bge", "bltu", "bleu",
        #     "bgeu", "bgt", "bgtu", "ble"] #just beq, bne, blt, bge, bltu, bgeu. other ones are pseudo substitutable.
        # self.LOAD = ["lw", "lh", "lb", "lbu", "lhu"] #lbu, lhu
        # self.STORE = ["sw", "sh", "sb"]
        # self.JUMP = ["jal", "jalr"]
        # self.PC_INST = ["auipc", "lui"]
        
        #TO CHECK: added auipc, lui
        # is the immediate value given ALREADY left shifted by 12 bits? or do we need to do shift?
        # do we add current PC or next +4 pc?
        # i assume it takes the imm, left shifts, and adds current pc. (or zero if lui)                

        
        ## ARM instructions
        self.REGULAR = ["add", "adc", "qadd", "sub", "sbc", "rsb", "qsub", "mul", "udiv", "sdiv",
                        "and", "bic", "orr", "orn", "eor",
                        "mov",
                        "lsl", "lsr", "asr", "ror", "rrx"]
        self.QUAD = ["mla", "mls", "umull", "umlal", "smull", "smlal"]
        self.TEST = ["cmp", "cmn", "tst", "teq"]
        self.LOAD = ["ldr", "ldrh", "ldrb"]
        self.STORE = ["str", "strh", "strb"]
        self.STACK = ["push", "pop",
                      "stmia", "ldmdb",
                      "stmdb", "ldmia"]
        self.BRANCH = ["beq", "bne", "bcs", "bhs", "bcc", "blo", "bmi", "bpl", "bvs", "bvc", "bhi", "bls", "bge", "blt", "bgt", "ble", "bal",
                       "bl", "bx", "blx"] # TODO: Test&Branch operations to be added later  
        self.SYNCH = ["ldrex", "strex"]
        self.NOP = ["nop"]
                        
        

    def get_reg_name(self, reg):
        """Interprets a string reg name as one of x0 through x31.
        for example, a0 is x10."""
        # if reg is already x0, through x31, it will not find it and simply return itself.
        # if reg is invalid, it will throw an error.
        try:
            return self.reg_name[reg.strip().lower()]
        except:
            raise SyntaxError("Invalid register: " + reg)

    def _load_reg_names(self, reg_name_filepath="reg_name.txt"):
        """Loads file that tells us mapping of register names.
        For example file would have a0 x10\na1 x11 ..."""

        with open(reg_name_filepath, "r") as f:
            name_list = f.readlines()

        for line in name_list:
            if line.strip() == "":
                continue
            name, xname = line.split()
            # make sure value is 32 bits
            # reads the ’0x0’ string into binary, truncates last 32,
            # then puts back into integer.
            self.reg_name[name] = xname

        print("\n--> Register names loaded successfully.\n")

    ### functions for plotting power ###
    def use_power_data(self, filepath, func=lambda x: x):
        """ Uses power data specified by filepath.
        filepath: string filepath with format ’instruction power\ninst2
        power’
        func: function to apply to numerical power value (for example,
        if we want to convert current to power)
        """
        # reads file and updates self.instruction_power_dict
        with open(filepath, "r") as f:
            inst_power_list = f.readlines()
        for line in inst_power_list:
            if line.strip() == "":
                continue
            inst, power = line.split()
            inst = inst.lower()
            power = float(power)
            # apply function on x. by default, function returns self.
            # this is useful in case we have e.g. current data instead.
            self.instruction_power_dict[inst] = func(power)
        print("\n--> Used power data successfully.\n")

    def get_power_for_instruction(self, inst):
        """ Gets numerical power value associated with instruction (e.g.
        ’add’).
        Returns None (which will plot blank) if instruction’s power is unspecified.
        """
        return self.instruction_power_dict.get(inst.lower(), None)
    
    def _add_point(self, inst, power_value):
        """ Adds instruction and corresponding power value to plot.
        inst: string instruction
        power_value: number for power
        """
        self.inst_line_power_list.append((inst, power_value))
    
    def get_power_consumption_list(self):
        """ Returns the current list of (instruction, power) in
        timestep order."""
        return self.inst_line_power_list
    
    def show_power_plot(self, minstep=None, maxstep=None, minpower=None, maxpower=None):
        """ Shows current power plot of all instructions.
        If plotting is not turned on, it will be blank.
        "None" will be shown as gap in plot.
        minstep, maxstep specifies the range (x) of steps to plot.
        minpower, maxpower specifies the range (y) of power to plot.
        """
        assert len(self.inst_line_power_list) != 0, "Nothing to plot. (Did you use run(plot=True)? )"
        
        # note this is albe to plot NONE points (just gap in plot)

        inst_list, power_list = zip(*self.inst_line_power_list)
        steps = list(range(len(inst_list)))
        plt.plot(steps, power_list, "b-") # blue line graph
        
        # we need to use steps otherwise plt will autogenerate x axis,
        # making it hard to set minstep
        
        xlabels = [str(inst) + "\n" + str(step) for inst,step in zip(inst_list, steps)]
        
        plt.xticks(steps, xlabels) # labels x axis with instructions
        plt.ylabel("Power")
        plt.title("Power Consumption Over Instruction Time Steps")
        # set axis range
        plt.axis(xmin=minstep, xmax=maxstep, ymin=minpower, ymax=maxpower)
        plt.show()

    ### functions for running ###
    def check_steppable(self):
        """Checks if code is steppable (pc is between 0 and end of file)."""
        self.steppable = (0 <= self.pc/4 < len(self.codefilelines)) and (not self.ended)
        return self.steppable
    
    def run(self, max_steps=None, plot=False, verbose=False):
        """Runs code until completion, or until specified max_steps steps.
        If plot=True, power values will be saved."""
    
        self.verbose = verbose
        self.plot = plot
        if self.plot:
            assert self.instruction_power_dict != {}, "To plot, please specify  power data with use_power_data()."
        # can specify max limit number of inst to run
        counter = 0
        if max_steps is None:
            while self.check_steppable():
                if self.cycle_counter % 1000000 == 0:
                   print(self.cycle_counter)
                # execute stuff
                self.step(verbose=verbose)
                counter += 1
            print("Done. End of code file.")
        else:
            for i in range(max_steps):
                if self.check_steppable():
                    self.step(verbose=verbose)
                    counter += 1
                else:
                    print("Done. End of code file.")
                    break
            #print("Executed", str(counter), "steps.")
        return
    
    def step(self, verbose=False):
        """Executes one step (next instruction)."""
        self.verbose = verbose
        assert self.pc%4 == 0 # pc is always 4*
        
        if self.verbose:
            print("--Current pc:", self.pc)
        instruction = self.codefilelines[self.pc//4]
        prev_pc = self.pc

        try:
            new_pc = self.parse_and_exec(instruction)
            # note that when wfi is reached, it cannot step. pc stays same.
        except:
            print("error stepping - cannot parse_and_exec")
            self._raise_error()

        return True
    
    
    def parse_and_exec(self, inst_string):
        """Parses and executes instruction based on string."""

        old_pc = self.pc # used for debugging (prints error)

        # semicolon_address = ""
        if ";" in inst_string:
            # semicolon_address = inst_string.split(';').strip()
            inst_string = inst_string.split(';')[0].strip()

        inst_params = self._match_instruction(inst_string) # could be length 2, 3, etc list

        if self.verbose:
            print("\n> Executing instruction:", inst_string, inst_params)
    
        inst = inst_params[0].strip() #string of the instruction itself
    
        # TODO: Check for suffixes and multiple elements in [] or {}
        if '.w' in inst or '.n' in inst:
            pass
        
        # TODO: Check for {s} suffix
        if inst[-1] == "s":
            pass


        #########
        # if (inst == "wfi"):
        #     self.ended = True
        #     return self.pc # not change pc
        #########
    
        # Note pc is updated after any of the following.

        if inst in self.REGULAR:
            if self.verbose:
              print("--REG")
            rd = self.get_reg_name(inst_params[1])
            ## Negative indicies are used to consider both cases where rs1 = rd, and rs1 =/= rd
            if "#" in inst_params[-1]: # check for imm values (decimal)
                rs1 = self.get_reg_name(inst_params[-2])
                const = HelperFunctions.int_or_hex_to_int(inst_params[-1].replace('#', ''))
                self.reg(inst_params[0], rd, rs1, const, True)   # is_imm = True
            else:
                rs1 = self.get_reg_name(inst_params[-2])
                rs2 = self.get_reg_name(inst_params[-1])
                self.reg(inst_params[0], rd, rs1, rs2, False)   # is_imm = False
            
        elif inst in self.QUAD:
            if self.verbose:
                print("--QUAD")
            rdLo = self.get_reg_name(inst_params[1])
            rdHi = self.get_reg_name(inst_params[2])
            rs1 = self.get_reg_name(inst_params[3])
            rs2 = self.get_reg_name(inst_params[4])
            self.quad(inst_params[0], rdLo, rdHi, rs1, rs2)

        elif inst in self.TEST:
            if self.verbose:
                print("--TEST")
            rs1 = self.get_reg_name(inst_params[1])
            if "#" in inst_params[-1]: # check for imm values (decimal)
                const = HelperFunctions.int_or_hex_to_int(inst_params[2].replace('#', ''))
                self.test_inst(inst_params[0], rd, const, True)   # is_imm = True
            else:
                rs1 = self.get_reg_name(inst_params[2])
                self.test_inst(inst_params[0], rd, rs1, False)   # is_imm = False

        # elif inst in self.BRANCH:
        #     if self.verbose:
        #         print("--BRANCH")
        #     # parse logic in case hex or int
        #     offset = HelperFunctions.int_or_hex_to_int(inst_params[3])
        #     rs1 = self.get_reg_name(inst_params[1])
        #     rs2 = self.get_reg_name(inst_params[2])
        #     self.branch(inst_params[0], rs1, rs2, offset)

        elif inst in self.LOAD:
            if self.verbose:
                print("--LOAD")
            # parse logic in case hex or int
            # offset = HelperFunctions.int_or_hex_to_int(inst_params[2])
            xto = self.get_reg_name(inst_params[1])
            xmem = [d.strip() for d in inst_params[2].split(',')] 
            """ Possible combinations
                1. ldr Rd, [Rb]
                2. ldr Rd, [Rb, #const]
                3. ldr Rd, [Rb, Ri, LSL n]
                4. ldr Rd label             # <-- this option is not supported yet
                5. ldr Rd, [Rb], #const     # <-- this option is not supported yet
                6. ldr Rd, [Rb, #const]!""" # <-- this option is not supported yet

            # TODO: missing option, for literal load with label
            offset = 0
            
            xmem = xmem[0]  # always true case

            if len(xmem) == 2:      # case: [Rb, #const]   
                offset = HelperFunctions.int_or_hex_to_int(xmem[1].replace('#', ''))
            
            # elif len(xmem) == 3:    # case: [Rb, Ri, LSL n]
            #     offset = (xmem[1]) << int(xmem[2].split("#")[-1]) # TODO: have to get Ri value to shift by n

            self.load(inst_params[0], xto, xmem, offset)

        elif inst in self.STORE:
            if self.verbose:
                print("--STORE")
            # parse logic in case hex or int
            # offset = HelperFunctions.int_or_hex_to_int(inst_params[2])
            xval = self.get_reg_name(inst_params[1])
            xmem = [d.strip() for d in inst_params[2].split(',')] 

            offset = 0
            
            xmem = xmem[0]  # always true case

            if len(xmem) == 2:      # case: [Rb, #const]   
                offset = HelperFunctions.int_or_hex_to_int(xmem[1].replace('#', ''))
            
            # elif len(xmem) == 3:    # case: [Rb, Ri, LSL n]
            #     offset = (xmem[1]) << int(xmem[2].split("#")[-1]) # TODO: have to get Ri value to shift by n

            self.store(inst_params[0], xval, xmem, offset)

        elif inst in self.BRANCH:
            if self.verbose:
                print("--BRANCH")
                print(inst)
            self.branch(inst_params[0], inst_params[1]) # must work for both register and label branch


        elif inst in self.SYNCH:
            if self.verbose:
                print("--SYNCH")
                print(inst)
            r1 = self.get_reg_name(inst_params[1])

            """ Possible cases
                1. ldrex Rd, [Rn {, #const}]
                2. strex Rt, Rs, [Rn {, #const}] """
            Rs = ''
            if len(inst_params)  == 3: 
                Rn = [d.strip() for d in inst_params[2].split(',')] 
            elif len(inst_params)  == 4:
                Rs = inst_params[2]
                Rn = [d.strip() for d in inst_params[3].split(',')] 

            offset = 0
            
            Rn = Rn[0]  # always true case

            if len(Rn) == 2:      # case: [Rn, #const]   
                offset = HelperFunctions.int_or_hex_to_int(Rn[1].replace('#', ''))

            const = HelperFunctions.int_or_hex_to_int(inst_params[2])
            self.synch(inst_params[0], r1, Rs, Rn,  const)

        else:
        # design question - should this reset() or not?
        # double check if the behavior of this is equivalent to the commented one.
            print("error inside parse_and_exec")
            self._raise_error()
        # raise SyntaxError(’Invalid instruction on line ’+ str(old_pc//4 + 1),
        # (self.codefilepath, old_pc//4 + 1, 0, inst_string))
        
        # increment cycle counter
        # TODO: check the special case of div
        if inst == "div":
            self.cycle_counter += 32
        else:
            self.cycle_counter += 1

        # if plotting turned on, add point in power plot
        if self.plot:
            if inst != "div":
                self._add_point(inst, self.get_power_for_instruction(inst))
            else:
                assert inst == "div"
                divpwr = self.get_power_for_instruction("div")
                for i in range(32):
                    self._add_point("div", divpwr)
            # need to check the cycle counter is working correctly.
            assert self.cycle_counter == len(self.inst_line_power_list), "Error with cycle counter."
        
        return self.pc
    
    def _match_instruction(self, inst_string):
        """Matches single line instruction string to either of two formats.
        Returns list of parts in instruction.
        """

        string = inst_string.lower().strip()
        
        ###########
        # if (string == "wfi"):
        #     return ["wfi"] # no groups, just itself.
        # sys.exit(0) didn’t work bc throws error.
        ###########
        
        word = "([^\s]+)"
        space = "[\s]+"
        maybespace = "[\s]*"
        multi_word = "(.*?)"
        c_multi_word_c = maybespace + multi_word + maybespace
        s_word_s = maybespace + word + maybespace


        # type 1: inst rs1, [rs2, ...]
        # mem_inst
        type1 = "^" + word + space + word + maybespace + "," + maybespace + "\[" + c_multi_word_c + "\]" + maybespace #+ "\$"

        # type 2: inst rs1, {rs2, ...}
        # stack_inst
        type2 = "^" + word + space + word + maybespace + "," + maybespace + "\{" + c_multi_word_c + "\}" + maybespace #+ "\$"

        # type3: inst rs1, rs2, rs3, rs4
        # quad_inst
        type3 = "^" + word + space + word + maybespace + "," + s_word_s + "," + s_word_s + "," + s_word_s #+ "\$"

        # type4: inst rs1, rs2, rs3
        # regular_inst
        type4 = "^" + word + space + word + maybespace + "," + s_word_s + "," + s_word_s #+ "\$"

        # type 5: inst rs1, rs2
        # dual_inst
        type5 = "^" + word + space + word + maybespace + "," + s_word_s #+ "\$"
        
        # type 6: inst rs1 <label>    (for branch with label)
        # label_branch_inst
        type6 = "^" + word + space + word + space + "\<" + s_word_s + "\>" + maybespace #+ "\$"

        # type 7: inst rs1      (for branch)
        # branch_inst
        type7 = "^" + word + s_word_s #+ "\$"

        # type 8: inst      (for nop)
        # solo_inst
        type8 = "^" + word + maybespace #+ "\$"

        # try to match; return groups
        mem_inst = re.search(type1, string)
        if mem_inst:
            return mem_inst.groups()
        else:
            stack_inst = re.search(type2, string)
            if stack_inst:
                return stack_inst.groups()
            else:
                quad_inst = re.search(type3, string)
                if quad_inst:
                    return quad_inst.groups()
                else:
                    regular_inst = re.search(type4, string)
                    if regular_inst:
                        return regular_inst.groups()
                    else:
                        dual_inst = re.search(type5, string)
                        if dual_inst:
                            return dual_inst.groups()
                        else:
                            label_branch_inst = re.search(type6, string)
                            if label_branch_inst:
                                return label_branch_inst.groups()
                            else:
                                branch_inst = re.search(type7, string)
                                if branch_inst:
                                    return branch_inst.groups()
                                else:
                                    solo_inst = re.search(type8, string)
                                    if solo_inst:
                                        return solo_inst.groups()
                                    else:
                                        print("error in _match_instruction")
                                        self._raise_error()

    ### convenience functions ###
    def get_total_lines(self):
        """Returns total lines in code. Not necessarily total steps."""
        return len(self.codefilelines)

    def reset(self):
        """Resets registers, pc, and memory.
        This can be run after updating the codefile/memory file,
        as it will re-read their filepaths."""
        self.__init__(self.codefilepath, self.memfilepath)
        return

    def set_pc(self, value):
        """Sets current pc to value. Must be multiple of 4."""
        assert value%4 == 0
        self.pc = int(value)
        return

    def get_pc(self):
        """Returns current pc (multiple of 4)."""
        return self.pc

    ### functions to handle different inst ###
    def reg(self, inst, dest, xval1, xval2, is_imm):
        """Executes xval1 inst xval2, saves in dest.
        inst is a string instruction.
        dest, xval1 are strings of register names and xval2 is the imm value in case is_imm = True.
        dest, xval1, xval2 are strings of register names in case is_imm = False.
        pc is updated.
        """
        # if dest == "x0":
        #     self.pc += 4
        #     return

        reg1 = HelperFunctions.hex_string_to_int(self.registers.get(xval1, "0x00000000"))
        if is_imm:
            reg2 = HelperFunctions.hex_string_to_int(HelperFunctions.int_to_hex_string(xval2))
        else:
            reg2 = HelperFunctions.hex_string_to_int(self.registers.get(xval2, "0x00000000"))  # if !is_imm
        
        
        # so take low and mod 32
        # sxxW is for RV32, so they require top bit of imm to be 0
        if inst == "lsl":
            flag = 'NZC'
            if is_imm:
                shift_binstring = bin(int(HelperFunctions.int_to_hex_string(reg2), 16))[2:][-6:]
                # this needs ^ to be done in case const is -, then we want the hex string and extract lower bits
                shift_val = int(shift_binstring, 2) %32
                result = int(reg1 * 2**(shift_val))
            else:
                # puts zeros in gaps
                # get lower 6 bits of reg2
                shift_binstring = bin(int(self.registers.get(xval2, "0x00000000"), 16))[2:][-6:]
                # note - unclear behaviour - will this mod 32?
                shift_val = int(shift_binstring, 2) %32
                # only low 6 bits of shift amount is used
                # we do not use hex_to_int because don’t want truncate negatives
                result = reg1*2**(shift_val)
            

        elif inst == "lsr":
            flag = 'NZC'
            if is_imm:
                reg1_hexstring = self.registers.get(xval1, "0x00000000")
                # print("reg1_hextring", reg1_hexstring)
                reg1_raw_binstring = bin(int(reg1_hexstring, 16))[2:] #remove ’0b’
                # print("reg1_raw_binstring", reg1_raw_binstring)
                reg1_binstring = "0"*(32-len(reg1_raw_binstring)) + reg1_raw_binstring
                # print("reg1_binstring", reg1_binstring)
                # we do not use hex_to_int because it is off by 1 for shifting negative nums
                
                # now we get shift amount
                shift_binstring = bin(int(HelperFunctions.int_to_hex_string(reg2), 16))[2:][-6:]
                # this needs ^ to be done in case const is -, then we want the hex string and extract lower bits
                
                shift_val = int(shift_binstring, 2) %32
                # print("shift_val", shift_val)
                filler = "0"
                shifted = reg1_binstring[:-shift_val] # all bits except last shift_val bits
                # print("shifted", shifted)

                result = int("0b" + filler*(32 - len(shifted)) + shifted, 2)
            else:
                # shifts zeros into gaps
                #string to be shifted is converted to binary of 32 bits
                reg1_hexstring = self.registers.get(xval1, "0x00000000")
                reg1_raw_binstring = bin(int(reg1_hexstring, 16))[2:] #remove ’0b’
                reg1_binstring = "0"*(32-len(reg1_raw_binstring)) + reg1_raw_binstring
                # we do not use hex_to_int because it is off by 1 for shifting negative nums
                
                # now we get shift amount
                shift_binstring = bin(int(self.registers.get(xval2, "0x00000000"), 16))[2:][-6:]
                shift_val = int(shift_binstring, 2) %32
                filler = "0"
                shifted = reg1_binstring[:-shift_val] # all bits except last shift_val bits
                result = int("0b" + filler*(32 - len(shifted)) + shifted, 2)

        elif inst == "asr":
            flag = 'NZC'
            if is_imm:
                reg1_hexstring = self.registers.get(xval1, "0x00000000")
                reg1_raw_binstring = bin(int(reg1_hexstring, 16))[2:] #remove "0b"
                reg1_binstring = "0"*(32-len(reg1_raw_binstring)) + reg1_raw_binstring
                # we do not use hex_to_int because it is off by 1 for shifting negative nums
                
                # now we get shift amount
                shift_binstring = bin(int(HelperFunctions.int_to_hex_string(reg2), 16))[2:][-6:]
                # this needs ^ to be done in case const is -, then we want the hex string and extract lower bits
                shift_val = int(shift_binstring, 2) %32
                filler = reg1_binstring[0]
                shifted = reg1_binstring[:-shift_val] # all bits except last shift_val bits
                result = int("0b" + filler*(32 - len(shifted)) + shifted, 2)
            else:
                reg1_hexstring = self.registers.get(xval1, "0x00000000")
                reg1_raw_binstring = bin(int(reg1_hexstring, 16))[2:] #remove "0b"
                reg1_binstring = "0"*(32-len(reg1_raw_binstring)) + reg1_raw_binstring
                # we do not use hex_to_int because it is off by 1 for shifting negative nums
                filler = reg1_binstring[0] # find highest bit
                
                # now we get shift amount
                shift_binstring = bin(int(self.registers.get(xval2, "0x00000000"), 16))[2:][-6:]
                shift_val = int(shift_binstring, 2) %32
                shifted = reg1_binstring[:-shift_val] # all bits except last shift_val bits
                result = int("0b" + filler*(32 - len(shifted)) + shifted, 2)

        elif inst == "eor":
            flag = 'NZCV'
            result = reg1^reg2
        
        elif inst == "add":
            flag = 'NZCV'
            result = reg1 + reg2
        
        elif inst == "sub":
            flag = 'NZCV'
            result = reg1 - reg2
        
        elif inst == "and":
            flag = 'NZCV'
            result = reg1 & reg2
        
        elif inst == "orr":
            flag = 'NZCV'
            result = reg1 | reg2
        
        elif inst == "mul":
            flag = ''
            result = reg1 * reg2
        
        # elif inst == "mulhu": # multiply, high bits, unsigned
        #     result = int(HelperFunctions.int_to_hex_string(reg1),16) * int(int(HelperFunctions.int_to_hex_string(reg2),16)) //2**32
        
        # elif inst == "mulh":
        #     result = reg1 * reg2 //2**32
        
        # elif inst == "mulhsu": # multiply, high bits, signed * unsigned
            # result = reg1 * int(int(HelperFunctions.int_to_hex_string(reg2),16))//2**32
        
        elif inst == "sdiv":
            flag = ''
            # div performs signed division
            # (divu performs unsigned)
            # according to RISCV manual, dividing by 0 sets all bits to 1
            # (which is -1 in div, and 2**length-1 for divu),
            if reg2 == 0:
                result = -1
            else:
            # Additionally, the only way to overflow div (signed) is
            # -2**(32-1)/-1. Here, the result should be -2**(31).
            # this is already supported when we use hex_string_to_int etc.
                result = reg1 // reg2

        elif inst == "divu":
            flag = ''
            # unsigned division
            reg1_u = int(HelperFunctions.int_to_hex_string(reg1), 16)
            reg2_u = int(HelperFunctions.int_to_hex_string(reg2), 16)
            if reg2_u == 0:
                result = 2**32-1 #32 bit, all 1’s
            else:
                result = reg1_u // reg2_u

        else:
            print("Unsupported reg instruction.")
            self._raise_error()

        result_hexstring = HelperFunctions.int_to_hex_string(result)
        if self.verbose:
            print("--Result of " + inst, result_hexstring)

        # save result
        self.registers[dest] = result_hexstring
        if flag != '':
            self.update_flags_vector(reg1, reg2, result, flag)

        self.pc += 4

    def quad(self, inst, rdLo, rdHi, rs1, rs2):
        """Executes rs1 inst rs2, saves in rdHi:rdLo.
        inst is a string instruction.
        dest, rs1, rs2 are strings of register names.
        In this case there is no imm values.
        pc is updated.
        """

        reg1 = HelperFunctions.hex_string_to_int(self.registers.get(rs1, "0x00000000"))
        reg2 = HelperFunctions.hex_string_to_int(self.registers.get(rs2, "0x00000000"))


    # def pc_inst(self, inst, dest, const):
    #     const = HelperFunctions.hex_string_to_int(HelperFunctions.int_to_hex_string(const))
        
    #     if inst == "auipc":
    #         # upper immediate is constant left shift by 12 bits
    #         result = self.pc + const*(2**12)
        
    #     elif inst == "lui":
    #         result = const*(2**12)
        
    #     result_hexstring = HelperFunctions.int_to_hex_string(result)
        
    #     if self.verbose:
    #         print("--Result of " + inst, result_hexstring)
    #     if dest != "x0  ":
    #         self.registers[dest] = result_hexstring
    #     self.pc += 4

    def test_inst(self, inst, rs1, rs2, is_imm):
        """Compare instruction. If x1 inst x2, update Flags vector accordingly.
        inst is string instruction.
        rs1 string register name and rs2 is an imm value in case of is_imm = True.
        rs1, rs2 are string register names in case of is_imm = False.
        pc is updated.
        """

        reg1 = HelperFunctions.hex_string_to_int(self.registers.get(rs1, "0x00000000"))
        if is_imm:
            reg2 = HelperFunctions.hex_string_to_int(HelperFunctions.int_to_hex_string(rs2))
        else:
            reg2 = HelperFunctions.hex_string_to_int(self.registers.get(rs2, "0x00000000"))  # if !is_imm

        if inst == "cmp":
            tst = reg1 - reg2
        elif inst == "cmn":
            tst = reg1 + reg2
        elif inst == "tst":
            tst = reg1 & reg2
        elif inst == "teq":
            tst = reg1^reg2

        self.update_flags_vector(reg1, reg2, tst, 'NZCV')

    def branch(self, inst, new_pc):
        """Executes branch instruction.
        inst is string instruction.
        new_pc is the address in memory to branch to in case condition is True (according to flags vector).
        new_pc is HEX, must be multiple of 4.
        pc is updated.
        """

        new_pc = HelperFunctions.hex_string_to_int(new_pc)
        assert new_pc%4 == 0
        do_branch = False
        
        if inst == "beq":
            do_branch = self.flags_vector['Z'] == 1
        elif inst == "bne":
            do_branch = self.flags_vector['Z'] == 0
        elif inst == "bcs" or inst == "bhs":
            do_branch = self.flags_vector['C'] == 1
        elif inst == "bcc" or inst == "blo":
            do_branch = self.flags_vector['C'] == 0
        elif inst == "bmi":
            do_branch = self.flags_vector['N'] == 1
        elif inst == "bpl":
            do_branch = self.flags_vector['N'] == 0
        elif inst == "bvs":
            do_branch = self.flags_vector['V'] == 1
        elif inst == "bvc":
            do_branch = self.flags_vector['V'] == 0
        elif inst == "bhi":
            do_branch = self.flags_vector['C'] == 1 and self.flags_vector['Z'] == 0
        elif inst == "bls":
            do_branch = self.flags_vector['C'] == 0 or self.flags_vector['Z'] == 1
        elif inst == "bge":
            do_branch = self.flags_vector['N'] == self.flags_vector['V']
        elif inst == "blt":
            do_branch = self.flags_vector['N'] != self.flags_vector['V']
        elif inst == "bgt":
            do_branch = self.flags_vector['Z'] == 0 and self.flags_vector['N'] == self.flags_vector['V']
        elif inst == "ble":
            do_branch = self.flags_vector['Z'] == 1 or self.flags_vector['N'] != self.flags_vector['V']
        elif inst == "bal":
            do_branch = True


        elif inst == "blt":
            do_branch = x1_value < x2_value
        elif inst == "bge":
            do_branch = x1_value >= x2_value
        elif inst == "bltu":
            # unsigned comparison
            do_branch = int(self.registers.get(x1, "0x00000000"),16) < int(self.registers.get (x2, "0x00000000"),16)
        elif inst == "bleu":
            # unsigned less than or equal to
            do_branch = int(self.registers.get(x1, "0x00000000"),16) <= int(self.registers.get(x2, "0x00000000"),16)
        elif inst == "bgeu":
            do_branch = int(self.registers.get(x1, "0x00000000"),16) >= int(self.registers.get(x2, "0x00000000"),16)
        elif inst == "bgt":
            do_branch = x1_value > x2_value
        elif inst == "bgtu":
            do_branch = int(self.registers.get(x1, "0x00000000"),16) > int(self.registers.get (x2, "0x00000000"),16)
        elif inst == "ble":
            do_branch = x1_value <= x2_value
            # "bgeu", "bgt", "bgtu", "ble",
        else:
            print("Unsupported branch instruction.")
            self._raise_error()
        if do_branch:
            self.pc += offset
        else:
            # no branch, go to next instruction
            self.pc += 4
        return

    # def jump_jal(self, inst, rd, imm):
    #     """Jumps to offset imm more than pc, and saves current pc+4"""
    #     # save pc+4 in rd
    #     if rd != "x0":
    #         self.registers[rd] = HelperFunctions.int_to_hex_string(self.pc + 4)
    #     # move pc to pc + imm
    #     self.pc += imm #imm already parsed to int
    #     return

    # def jump_jalr(self, inst, rd, rs1, imm):
    #     """Jumps to (address saved in rs1) + imm, zeroing the last bit
    #     saves pc+4 in rd."""
    #     if rd != "x0":
    #         self.registers[rd] = HelperFunctions.int_to_hex_string(self.pc + 4)
    #     rs_address = self.registers.get(rs1, "0x00000000")
    #     self.pc = HelperFunctions.hex_string_to_int(rs_address) + imm #regs store hex
    #     return

    def store(self, inst, xvalue, xmem_reg, offset):
        """Executes store instruction. Value inside register xvalue is stored
        at:
        (address specified in register xmem) + offset.
        inst is string instruction
        xvalue, xmem are string register names.
        offset is integer number, must be correct multiple (depending on
        inst).
        Note that depending on the type of inst, the number of bytes saved
        varies.
        pc is updated.
        """
        # example:
        # sw x1, 8(x2)
        # stores value saved in x1 reg into location (x2 reg) + 8
        # the total offset is the offset conributed by
        # offset input, and the amount ’xmem’ is off from a multiple of 4.
        xmem = self.registers.get(xmem_reg, "0x00000000")
        # print(’--xmem initially’, xmem)
        xmem_rem = HelperFunctions.hex_string_to_int(xmem)%4 # offset from  multiple of 4 memory address
        # print(’--xmem_rem, offset from multiple of 4’, xmem_rem)
        xmem = HelperFunctions.int_to_hex_string(HelperFunctions.hex_string_to_int(xmem) - xmem_rem)
        # print(’--xmem-xmem_rem’, xmem)
        offset += xmem_rem
        # print(’--offset’,offset)
        # offset might be a multiple of 4.
        # note this is compatible with negative offset.
        whole_lines = int(offset)//4
        # print(’--whole lines within offset’, whole_lines)
        rem = int(offset)%4
        # print(’--true remainder after offset’, rem)
        location_int = HelperFunctions.hex_string_to_int(xmem) + whole_lines*4 # need to mul by 4
        location_hex = HelperFunctions.int_to_hex_string(location_int)
        # print(’--location hex, whole lines and xmem’, location_hex)
        mem_string = self.memfile.read(location_hex)
        # print(’--value read from location’, mem_string)
        word_to_store = self.registers.get(xvalue, "0x00000000")
        # print(’--value from reg to store’, xvalue, word_to_store)
        INTERVAL = 0
        # one byte is 2 hex digits, or 8 bits.
        # depending on instruction, read different length.
        if inst == "strb":
            INTERVAL = 2
        elif inst == "strh":
            assert rem == 0 or rem == 2, "strh supports 16 bit/2 byte/4 hex digit offsets."
            INTERVAL = 4
        elif inst == "str":
            assert rem == 0, "str supports 32 bit/4 byte/8 hex digit offsets."
            INTERVAL = 8
        else:
            print("Unsupported store instruction.")
            self._raise_error()

        # extract length of store string based on inst
        word_to_store = word_to_store[-INTERVAL:]
        if self.verbose:
            print("--Storing", word_to_store)
            print("--To address", location_hex)
        new_mem_string = mem_string[0:len(mem_string)-(rem+INTERVAL//2)*2] + word_to_store + mem_string[len(mem_string)-(rem+INTERVAL//2)*2+INTERVAL:]
        
        # update memory
        self.memfile.update(location_hex, new_mem_string)
        if self.verbose:
            print("--Result of store", new_mem_string)
        self.pc += 4
        return

    def _raise_error(self):
        """Internal function to raise syntax error on current line."""
        line = self.pc//4
        raise SyntaxError("Invalid instruction on line " + str(line+1), (self.codefilepath, line + 1, 0, self.codefilelines[line]))

    def load(self, inst, xinto, xmem_reg, offset):
        """Loads what’s saved in xmem (with offset) into register xinto.
        inst: string of instruction
        xmem: string of memory location
        offset: integer number (should align with memory, depending on inst)
        xinto: string of register name
        pc is updated.
        """
        # example:
        # lw x1, 8(x2)
        # loads into reg x1, value from location (x2 reg) + 8
        if xinto == "x0":
            self.pc += 4
            return
        
        # the total offset is the offset conributed by
        # offset input, and the amount ’xmem’ is off from a multiple of 4.
        xmem = self.registers.get(xmem_reg, "0x00000000")
        # print(’--xmem original’, xmem)
        xmem_rem = HelperFunctions.hex_string_to_int(xmem)%4 # offset from multiple of 4 memory address
        xmem = HelperFunctions.int_to_hex_string(HelperFunctions.hex_string_to_int(xmem) - xmem_rem)
        # print(’--xmem ’, xmem)

        offset += xmem_rem
        # print(’--offset’,offset)

        # offset might be a multiple of 4.
        # note this is compatible with negative offset.
        whole_lines = int(offset)//4
        rem = int(offset)%4
        # print(’--whole_lines in offset’, whole_lines)
        # print(’--true rem’, rem)

        location_int = HelperFunctions.hex_string_to_int(xmem) + whole_lines*4  # need to mul by 4!
        location_hex = HelperFunctions.int_to_hex_string(location_int)

        # print(’--location’, location_hex)
        mem_string = self.memfile.read(location_hex) #location points to very last bit in the line
        # print(’--mem_string at location’, mem_string)
        
        INTERVAL = 8
        # setting intervals
        # 0 offset: -2 because read 2 bits
        # 1 offset: -4 4 bits from the end
        # 2 offset: -6
        # 3 offset: -8
        
        if inst == "ldrb":
            INTERVAL=2
        elif inst == "ldrh":
            assert rem == 0 or rem == 2, "ldrh supports 16 bit/2 byte/4 hex digit offsets."
            INTERVAL = 4
        elif inst == "ldr":
            assert rem == 0, "ldr supports 32 bit/4 byte/8 hex digit offsets."
            INTERVAL = 8
        else:
            print("Unsupported load instruction.")
            self._raise_error()

        value = mem_string[len(mem_string)-(rem+INTERVAL//2)*2: len(mem_string)-(rem+INTERVAL//2)*2+INTERVAL]

        # print(’--final value loaded’, value)
        if self.verbose:
            print("--Loaded bits", value)

        if xinto != "x0":
            self.registers[xinto] = "0x" + (8-len(value))*(value[0])+ value
        
        # print(’--reg saved to’, xinto)
        if self.verbose:
            print("--Saved as", self.registers.get(xinto, "0x00000000"))
        # in case if it is x0, save nothing

        self.pc += 4
        return
    
    def update_flags_vector(self, op1, op2, ans, flags):
        """ Update the flag vector accoeding to a previous execution result.
        op1 and op2 are the operands (int)
        ans is the answer the previous operation (int)
        flags is a string that contains flags to update, depends on the previous instruction"""

        if 'N' in flags:
            self.flags_vector['N'] = 1 if ans < 0 else 0
        if 'Z' in flags:
            self.flags_vector['Z'] = 1 if ans == 0 else 0
        if 'C' in flags:
            self.flags_vector['C'] = 1 if op1+op2>((2**32)-1) else 0
        if 'V' in flags:
            self.flags_vector['V'] = 1 if (op1>0 and op2>0 and ans<0) or (op1<0 and op2<0 and ans>0) else 0
        if 'Q' in flags:
            self.flags_vector['Q'] = 0 # TODO: implement check saturation flag


    def save(self, output_location):
        """Saves memory into output_location. Does not save registers. Does
        not reset."""
        self.memfile.save(output_location)
        return True
    
    def get_average_power(self):
        power_consumption_list = self.inst_line_power_list
        avg_power = 0

        for inst in power_consumption_list:
            avg_power += inst[1] # power_consumption_list(inst, power), so we want the second element for each tuple

        return avg_power
    
    def get_instruction_stats(self):
        """ Returns a dict with statistics of the 
        occurence of each instruction while execution. """
        power_consumption_list = self.inst_line_power_list
        instruction_stat = {}

        for inst in power_consumption_list:
            if inst[0] in instruction_stat:
                instruction_stat[inst[0]] += 1 # power_consumption_list(inst, power), so we want the second element for each tuple
            else:
                instruction_stat[inst[0]] = 1
        return instruction_stat