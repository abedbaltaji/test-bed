from pre_processing_functions import clean_code, preprocessing_memory_input
from modules.RISCV import RISCV
import re


if __name__ == "__main__":

    # asm_code_path = "inputs/code_cleaned_rel_address.txt"
    # mem_file_path= "inputs/mem_cleaned.txt"
    # power_data_file_path= "inputs/power_data_CW.txt"

    # clean_code("matrix_mult_3x3.txt")
    # preprocessing_memory_input()

    # riscv_inst = RISCV(codefilepath= asm_code_path, memfilepath= mem_file_path)
    
     
    # riscv_inst.use_power_data(filepath=power_data_file_path)
    # riscv_inst.run(plot=True, verbose=False)
    # riscv_inst.save("output_mem.txt")
    # riscv_inst.show_power_plot()

    # print("get_average_power", riscv_inst.get_average_power())

    # print("get_instruction_stats", riscv_inst.get_instruction_stats())

    string= "ldr r1, {r2, #12}"

    word = "([^\s]+)"
    space = "[\s]+"
    maybespace = "[\s]*"
    multi_word = "(.*?)"
    c_multi_word_c = maybespace + multi_word + maybespace
    s_word_s = maybespace + word + maybespace

    type1 = "^" + word + space + word + maybespace + "," + maybespace + "\[" + c_multi_word_c + "\]" + maybespace #+ "\$"

    mem_inst = re.search(type1, string)
    print(mem_inst)
    if mem_inst:
        print("grps", mem_inst.groups()) 

    # riscv_inst.show_power_plot(maxstep=80, minpower=1000, maxpower=4000)
    
    # print(riscv_inst._match_instruction("mul a5,a5,a4"))