# prefixes all the hex numbers in code2.txt with ’0x’.
# also changes all the absolute addresses to current addresses

base_dir_path = "inputs/"

def clean_code(code_file_path):
    f = open(base_dir_path + code_file_path, "r")
    lines = f.read().split("\n")
    f.close()
    g = open(base_dir_path + "code_cleaned_rel_address.txt", "w")

    print("\nclean_code() =>\n")

    line_pc = 0
    for nextline in lines:
        if nextline.strip() == "":
            continue
            # line_pc is not incremented.
        inst = nextline.split() [0]
        comma_split_line = nextline.split(",")
        current_instruction = inst.strip().lower()
        if (current_instruction in ["jal", "jalr", "beq", "bne", "blt",
            "bltu", "bgt", "auipc", "lui"]):
            num = comma_split_line[-1] # this will never be negative.
            if num[0:2] != "0x":
                num = "0x" + num # append hex
            relative_address = num
            # also subtract current pc from number
            # note: only for jumps/branches.
            # note: inconsistency in dumpfile, "jalr" uses relative
            if current_instruction in ["jal", "beq", "bne",
                "blt", "bltu", "bgt"]:
                absolute_address = int(num, 16)
                current_address = line_pc
                relative_address = hex(absolute_address - current_address)
            line = ",".join(comma_split_line[0:-1] + [relative_address] )
        else: # don’t change if not special instruction
            line = nextline
        print(line)
        g.write(line + "\n")
        line_pc += 4
    g.close()

    
def preprocessing_memory_input():
# prefixes all the hex numbers in code2.txt with ’0x’.
    f = open(base_dir_path + "mem.txt", "r")
    lines = f.read().split("\n")
    f.close()
    g = open(base_dir_path + "mem_cleaned.txt", "w")
    print("\npreprocessing_memory_input() =>\n")
    for nextline in lines:
        if nextline.strip() == "":
            continue
        addr, value = nextline.split()
        line = ("0x" + addr if "0x" not in addr else addr) + ("\t 0x" + value if "0x" not in value else "\t" + value)
        
        print(line)
        g.write(line + "\n")
    g.close()