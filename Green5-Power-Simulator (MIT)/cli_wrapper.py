# import sys
# sys.path.insert(1, ’../py-riscv-package/py_riscv’)
# import riscv_compiler
# import random
# import os

# # disable/enable print
# default_stdout = sys.stdout

# def disable_print():
#     sys.stdout = open(os.devnull, "w")

# def enable_print():
#     if (sys.stdout != default_stdout):
#         sys.stdout.close()
#         sys.stdout = default_stdout

# # specify number of iterations.
# # specify which memory locations will be random (list format).
# # mem locations need to be hex strings.

# def repeated_runs(iters, random_mem_locations, code_filepath, power_filepath, output_filepath):
#     enable_print()
#     for i in range(iters):
#         print("====== Iteration " + str(i+1) + " of " + str(iters) + " ======")
        
#         # create mem file with random vals, name it "mem_iter_i.txt"
#         with open(os.path.join(output_filepath, "mem_iter_" + str(i) + ".txt"), "w") as f:
#             for loc_index in range(len(random_mem_locations)):
#                 random_number = random.randint(0, 2**32-1) # 32 bit
#                 line = str(random_mem_locations[loc_index]) + "\t" + str(random_number) + "\n"
#                 f.write(line)
#             f.close()
        
#         disable_print()
#         riscv_instance = riscv_compiler.RISCV(code_filepath, os.path.join(output_filepath, "mem_iter_" + str(i) + ".txt"))
#         riscv_instance.use_power_data(power_filepath)
#         riscv_instance.run(plot=True)
#         power_output = riscv_instance.get_power_consumption_list()
        
#         # save in output_power_iter_i.txt
#         with open(os.path.join(output_filepath,
#             "output_power_iter_" + str(i) + ".txt"), "w") as outfile:
#             for j in range(len(power_output)):
#                 inst, pwr = power_output[j]
#                 line = str(inst) + "\t" + str(pwr) + "\n"
#                 outfile.write(line)
#             outfile.close()

#         enable_print()
#         print("Output written to", os.path.join(output_filepath,
#         "output_power_iter_" + str(i) + ".txt"))
#         print(riscv_instance.registers)
#         # registers store hex values.

#     if __name__ == "__main__":
#         arg_dict = dict(arg.split("=") for arg in sys.argv[1:])
#         iters = arg_dict.get("iters", 1) #default to 1 iter
#         try:
#             memlistfile = arg_dict["memlistfile"]
#         except:
#             print("Please provide memlistfile.")
#             sys.exit()
#         try:
#             powerfile = arg_dict["powerfile"]
#         except:
#             print("Please provide powerfile.")
#             sys.exit()
#         try:
#             codefile = arg_dict["codefile"]
#         except:
#             print("Please provide codefile.")
#             sys.exit()
        
#         outfolder = arg_dict.get("outfolder", "")
#         iters = int(iters) # default as string
        
#         print("Using iters:", iters)
#         print("Using randomizing the memory addresses listed in file:", memlistfile)
#         print("Using codefile:", codefile)
#         print("Using power file:", powerfile)
#         print("Using out folder:", outfolder)
        
#         # expects random memory addresses listed with whitespaces
#         with open(memlistfile, "r") as m:
#             mem_list = m.read().split()
#             m.close()
#         repeated_runs(iters, mem_list, codefile, powerfile, outfolder)