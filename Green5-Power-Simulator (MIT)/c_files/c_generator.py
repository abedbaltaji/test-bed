import sys
import random

#1000 outer loop, 7500

def gen_main(command, outer_loop, inner_loop, instr="REG", immediate=None, kargs=""):

    """
    kargs is an input for STACK operations, must be a string in the form of 'ex1, ex2, ex3'. Length, number of elements is up to you (1 or more).
    """
    target = open("main.c", "w")

    ################
    ## write headers
    ################

    target.write("""// Test Cortex-M3

#include <stdio.h>
#include <string.h>
// # include <stdlib.h>

#include "xparameters.h"
#include "xgpio_l.h"
#include "xuartlite_l.h"

#include "dwt.h"
#include "trigger.h"
#include "simple_serial.h"

//-----------------------------------------------------------------------------
// random function (custom)
//-----------------------------------------------------------------------------

unsigned long random (unsigned long x)
{
    return ((1103515245 * x + 12345) % 2147483648);
}

""")
                 
    target.write("""
int main ( void )
{

    while (1){
    unsigned int i;
    unsigned long res, var1, var2;

    // PRNG Seed
    unsigned long randx = 80817752;
    
    // wait for data
    uint8_t command = simpleserial_recv_byte();
    while (command != 'n'){
        command = simpleserial_recv_byte();
    }
    
    // Clear Data-Path
    
    __asm volatile ("MOV R4, #0x00000000" : :);
    __asm volatile ("MOV R5, #0x00000000" : :);
    __asm volatile ("add R6, R4, R5;" : :);
    __asm volatile ("sub R6, R4, R5;" : :);
    __asm volatile ("mul R6, R4, R5;" : :);
    __asm volatile ("and R6, R4, R5;" : :);
    __asm volatile ("orr R6, R4, R5;" : :);
    __asm volatile ("eor R6, R4, R5;" : :);
    __asm volatile ("lsl R6, R4, R5;" : :);
    __asm volatile ("lsr R6, R4, R5;" : :);

    // Clear Data-Path""")

    if (instr=="LD") or (instr == "ST"):
        target.write("""
    // move the value of the base address into R5
    static long address_var[""" + str(inner_loop) + """]; // Note: static keyword is to create the array in the memory, and not in the stack, for size limitation issues
    __asm volatile("MOV R5, %[input_0];":: [input_0] "r" (address_var));
    """)

    if instr=="LD":
        target.write("""
    randx = random(randx); //pick a random within 2^11 to save
    //move the random value into register R6
    __asm volatile ("mov R6, %[input_0];" : : [input_0] "r"(randx));
    //store R6 at the address in R5""")
        
        if command == "ldr":
            for i in range(inner_loop):
                target.write("""
    __asm volatile("str R6, [R5, #""" + str(i*4) + """]" ::);""")
        if command == "ldrh":
            for i in range(inner_loop):
                target.write("""
    __asm volatile("strh R6, [R5, #""" + str(i*2) + """]" ::);""")
        if command == "ldrb":
            for i in range(inner_loop):
                target.write("""
    __asm volatile("strb R6, [R5, #""" + str(i) + """]" ::);""")
        
    if instr=="STACK" and command=="pop":
        for i in range(inner_loop):
            target.write("""
    __asm volatile ("push {""" + kargs + """};" : :);""")  
            
    #logic to deal with outer_loop, for loads and stores:
    #Note, the .csv file is where we input the
    #values for outer loop. so we expect those
    #to be calculated/ confirmed in CSV.
    
    if instr != "BRANCH":
        target.write("""
        
        // Power Measurement Start
        
        
        trigger_set(1);

        for (i = 0; i < """ + str(outer_loop) + """; i++)
        {
        // Initialize Variables / Registers Start
        """)
    else:
        target.write("""
        
        trigger_set(1);
        """)

    if instr=="REG" or instr=="TEST" or instr=="STACK":
    # set R4, R5 to different things
        target.write("""
        randx = random(randx);
        __asm volatile ("MOV R4, %[input_0]" : : [input_0] "r" (randx));
        randx = random(randx);
        __asm volatile ("MOV R5, %[input_1]" : : [input_1] "r" (randx));
    // Initialize Variables / Registers End""")

    elif (instr == "IMM") or (instr == "SHAMT") or (instr == "ST"):
    # only use R4, assuming other is immediate
    # branch sets its own values
        target.write("""
        randx = random(randx);
        __asm volatile ("MOV R4, %[input_0]" : : [input_0] "r" (randx));
    // Initialize Variables / Registers End""")
        
        target.write("""
            // Test Code Start
    """)
        
    if instr=="REG":

        if command == "mov":
            for i in range(inner_loop):
                target.write("""
            __asm volatile (\"""" + command + """ R6, R4;" : :);""")
        else:
            for i in range(inner_loop):
                target.write("""
            __asm volatile (\"""" + command + """ R6, R4, R5;" : :);""")
    
    elif instr=="IMM":

        if command == "and": # special case for ANDi, max imm value is limited in ARM
            for i in range(inner_loop):
                target.write("""
            __asm volatile (\"""" + command + """ R6, R4, """
            + str(random.randint(0, 2**8-1)) + """;" : :);""")
        elif command == "mov":
            for i in range(inner_loop):
                target.write("""
            __asm volatile (\"""" + command + """ R6, #"""
            + str(random.randint(0, 2**8-1)) + """;" : :);""")
        else:
            for i in range(inner_loop):
                target.write("""
            __asm volatile (\"""" + command + """ R6, R4, """
            + str(random.randint(0, 2**12-1)) + """;" : :);""")

    elif instr=="SHAMT":
        for i in range(inner_loop):
            target.write("""
        __asm volatile (\"""" + command + """ R6, R4,"""
        + str(random.randint(0, 2**5-1)) + """;" : :);""")
            
    elif instr=="BRANCH":

        if command[0] == "b" and command != "bic":          
            target.write("""
        __asm volatile ("b loop" : :);
        __asm volatile ("loop:" : :);
        __asm volatile ("b loop" : :);
    """)
            
    elif instr == "TEST":
        for i in range(inner_loop):
            target.write("""
        __asm volatile (\"""" + command + """ R5, R4" : :);""")
            
    elif instr == "STACK":
        if kargs == []:
            raise TypeError("missing required input kargs.")
        if command == "push" or command == "pop":  
            for i in range(inner_loop):        
                target.write("""
        __asm volatile (\"""" + command + """ {""" + kargs + """};" : :);""")    
        
    elif instr == "LD":
        if command == "ldr":
            for i in range(inner_loop):
                target.write("""
        __asm volatile ("ldr R6, [R5, #""" + str(i*4)+"""]" :: );""")
                #4092
                #if lw, outer_loop *8
        if command == "ldrh":
            for i in range(inner_loop):
                target.write("""
            __asm volatile ("ldrh R6, [R5, #""" + str(i*2)+"""]" :: );""")
            #4094
            #if lh, outer loop *4
        if command == "ldrb":
            for i in range(inner_loop):
                target.write("""
        __asm volatile ("ldrb R6, [R5, #""" + str(i)+"""]" :: );""")
                #4095

        # if lb, outer loop * 2.
        #reason is because only 4092, but we want 7000, 1000
        #so total 7000*1000
        #previously, inner was 7000. But now inner is 4000. so outer needs
        #to double. This is because IMM only has 12 bits, so largest 4095.

    elif instr == "ST":
        if command == "str":
            for i in range(inner_loop):
                target.write("""
        __asm volatile("str R4, [R5, #""" + str(i*4)+"""]" :: );""")
        if command == "strh":
            for i in range(inner_loop):
                target.write("""
        __asm volatile("strh R4, [R5, #""" + str(i*2)+"""]" :: );""")
        if command == "strb":
            for i in range(inner_loop):
                target.write("""
        __asm volatile("strb R4, [R5, #""" + str(i)+"""]" :: );""")
    else:
        raise SystemExit("INVALID INSTRUCTION TYPE.")
    
    if instr != "BRANCH":
        target.write("""
        // Test Code End
        }
        
        
        trigger_set(0);
        
        // Power Measurement End

    """)
    else:
        # no need for setting trigger to 0 in case of Branch since it is an endless loop.
        target.write("""
    trigger_set(0);

""")

    if instr=="STACK" and command=="push":
        for i in range(inner_loop):
            target.write("""
    __asm volatile ("pop {""" + kargs + """};" : :);""")  

    target.write("""
    // Send results to host
    
    __asm ("MOV %[result], R6"
        : [result] "=r" (res)
        :
    );
    __asm ("MOV %[result], R4"
        : [result] "=r" (var1)
        :
    );
    __asm ("MOV %[result], R5"
        : [result] "=r" (var2)
        :
    );

    simpleserial_send_byte('e');
    simpleserial_send_bytes(4, &var1);
    simpleserial_send_bytes(4, &var2);
    simpleserial_send_bytes(4, &res); 
    
    }
} """)
    target.close()


if __name__ == "__main__":
    print(sys.argv)

    if len(sys.argv)<2:
        raise TypeError("missing input parameters.")

    command = sys.argv[1]
    command = command.lower()
    outer_loop = int(sys.argv[2])
    inner_loop = int(sys.argv[3])

    instr = "REG"
    if len(sys.argv) > 4: #has index 4, length 5
        instr = (sys.argv[4]).strip()
        instr = instr.upper()

    kargs=[]
    if len(sys.argv) > 5: #has index 5, length 6
        kargs = (sys.argv[5])

    gen_main(command, outer_loop, inner_loop, instr=instr, kargs=kargs) 