class HelperFunctions:

    @staticmethod
    def int_to_hex_string(intvalue):
        """Converts an integer into 32 bit hex string (8 digits)
        Implements two’s complement and truncates."""
        # intvalue up to 2**31-1
        # 2**31 is 1000...0 in binary, or 800..00 in hex
        # negative int is -2**31
        intvalue = int(intvalue) # in case input is a string
        intvalue = (2**32 + intvalue)%2**32
        hex_str = hex(intvalue)[2:]
        return "0x" + "0"*(8-len(hex_str)) + hex_str

    @staticmethod
    def hex_string_to_int(hexstr):
        """Converts hex string into integer value.
        Implements two’s complement and assumes 32 bit (or less) input."""
        intvalue = int(hexstr, 16)
        actualvalue = (intvalue - 2**31 + 1) %(-2**32) + 2**31 - 1
        return actualvalue

    @staticmethod
    def int_or_hex_to_int(num):
        """Interprets num as an integer, where num is either an integer,
        string integer, or hex string."""
        try:
            if type(num) == int:
                return num
            elif type(num) == str:
                if num[0:2] == "0x" or num[0:3] == "-0x":
                    num = HelperFunctions.hex_string_to_int(num)
                else:
                    num = HelperFunctions.hex_string_to_int(HelperFunctions.int_to_hex_string(int(num)))
                    # this is needed to ensure handling of twos complement
                return num
        except:
            raise SyntaxError("Invalid constant: " + str(num) + " is not a number or hex string.")