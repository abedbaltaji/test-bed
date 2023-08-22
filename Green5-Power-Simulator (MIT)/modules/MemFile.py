from modules.HelperFunctions  import HelperFunctions

class MemFile:
  
    """Class representing a memory file.
    Operations to load, update, read, and save.
    Operations don’t modify original file."""
    # assumes memory file is separated by whitespace
    def __init__(self):
        self.filepath = ""
        self.lines = {} # maps address number to value
    
    def load(self, filepath):
        """loads memory specified in filepath as memory.
        Expects each line to be formatted like "address value"
        For example: 0x00000004 0xabababab
        """
        self.filepath = filepath
        with open(filepath, "r") as f:
            inst_list = f.readlines()
        
        for line in inst_list:
            if line.strip() == "":
                continue
            address, value = line.split()
            # make sure value is 32 bits
            # reads the ’0x0’ string into binary, truncates last 32,
            # then puts back into integer.
            value = HelperFunctions.int_to_hex_string(HelperFunctions.int_or_hex_to_int(value))
            self.lines[address] = value

    def update(self, line, data):
        """Updates the data saved at address "line".
        line, data are string hex values."""
        # ensure values are 32 bit
        line = HelperFunctions.int_to_hex_string(HelperFunctions.hex_string_to_int(line))
        data = HelperFunctions.int_to_hex_string(HelperFunctions.hex_string_to_int(data))
        self.lines[line] = data

    def read(self, line):
        """Reads memory from address "line"."""
        ## line must be in hex string
        ## add functionality for lines that aren’t multiples of 4 exactly.
        return self.lines.get(line, "0x00000000")
                          
    def save(self, filepath):
        """Save current memory into location filepath."""
        with open(filepath, "w") as outfile:
            for i in self.lines.keys():
                outfile.write(i + "\t" + self.lines[i].strip() + "\n")
        print("Memory saved to", filepath)
        return True