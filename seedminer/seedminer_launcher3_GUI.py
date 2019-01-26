#Seedminer Text-based UI v1.0

#fef0fef0fef0fef0fef0fef0fef0fef0
#↑↑↑↑↑dummy ID0 for testing↑↑↑↑↑
#10 points for Gryffindor if you get the reference

#"Press any key to continue" message
def pause(alt_msg = None):
    if alt_msg == None:
        input("Press any key to continue...")
    else:
        input(alt_msg)

try:
    import seedminer_launcher3 as sl3
except ModuleNotFoundError:
    print("This script needs to be placed in the same direcory as the seedminer_launcher3.py script")
    pause("Press any key to exit")
    exit(1)
    
import os
import sys
import signal
from textwrap import dedent

force_reduced_work_size = False
offset_override = 0

##########FUNCTIONS##########
def signal_handler(sig, frame):  # So KeyboardInterrupt exceptions don't appear
    sys.exit(0)
    
def bfcl_signal_handler(sig, frame): #Shows a message if the users interrupts bruteforcing
    print("\n\nBruteforcing aborted by the user. If you want to resume it later, TAKE NOTE of the offset value shown above!")
    pause()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#Checks if ID0 is valid
def is_id0_valid(id0):
    try:
        print(id0, end='')
        sys.stdout.flush()
        int(id0, 16)
        if len(id0) == 32:
            print(" -- valid ID0")
            return True
        else:
            print(" -- improper ID0 length")
            sys.stdout.flush()
            return False
    except:
        print(" -- not an ID0")
        return False

#Clears the screen
def clear_screen():
    stupidworkaroundvariable = os.system("cls") if os.name == "nt" else print("\033c", end="")
    del stupidworkaroundvariable
    #This mess of a code is to support clearing the screen on both Windows and Unix
    #The "stupidworkaroundvariable" is used to prevent the cls return code on the screen (without it a 0 would've been automatically printed after clearing the screen, which is kinda pointless)
    #Thank you https://stackoverflow.com/a/23075152 and https://stackoverflow.com/a/2084628 , my solution uses a combination of both

#Asks a simple yes/no questions, and returns True or False accordingly
def ask_yes_no(msg):
    inp = input(msg + " (y/n) ")
    while True:
        if inp.lower() == "y":
            return True
        elif inp.lower() == "n":
            return False;
        else:
            inp = input("Please enter a valid option (y/n) ")

#Asks to input a number from a list of choices
def ask_list_input(count, allow_s):
    rang = range(1, count + 1)
    inp = input("\nPlease select an option: ")
    while True:
        if inp.lower() == "s":
            return "s"
        try:
            if int(inp) in rang:
                return int(inp)
            else:
                raise ValueError
        except ValueError:
            inp = input("Please select a valid option: ")
            

   
#Asks to delete no longer needed files
def ask_for_deletion():
    inp = ask_yes_no("\nDo you want to delete no longer needed files? ")
    if inp == True:
        try:
            os.remove("movable_part1.sed")
            os.remove("movable_part1.sed.backup")
            os.remove("movable_part2.sed")
            os.remove("input.bin")
        except FileNotFoundError:
            print("", end="") #really stupid workaround
        
#Asks to rename the movable.sed in order to contain the friend code
def ask_for_renaming():
    inp = ask_yes_no("Do you want to rename the movable.sed file to contain the friend code?")
    if inp == True:
        inp = input("Enter the friend code: ")
        fc = ''.join([i for i in inp if i.isdigit()])
        os.rename("movable.sed", "movable_" + fc + ".sed")
        
#Due to how bfcl's offset argument works, this is required so support negative numbers. Does NOT include non-integer input failsafe, so this should be wrapped in a try/except block
def get_offset_arg(ofs):
    ofs = int(ofs)
    if ofs == 0:
        offset_override = 0
    elif ofs > 0:
        offset_override = ofs * 2 - 1
    else:
        offset_override = abs(ofs) * 2
    print("Bruteforcing will resume on offset {}".format(ofs))
    return offset_override
    
#Shows the main menu
def show_main_menu():
    clear_screen()
    #Protip about dedent: by doing like this print statement below, eg triple quotes without immediately going to a new line, the other lines will still show one unit of indent. On the other hand, immediately going to a new line after the quotes (like in show_gpu_options()) will make everything dedented.
    print(dedent("""Available options:
    1. GPU bruteforce (normal) (recommended)
    2. GPU bruteforce (with options)
    3. CPU bruteforce
    4. Mii bruteforce
    Note: the LCFS databases will be automatically updated"""))
    mode = ask_list_input(4, False)
    while True:
        inp = input("Enter the ID0: ")
        if is_id0_valid(inp) == True:
            id0 = inp
            break;
    if mode == 1:
        sl3.update_db()
        sl3.hash_clusterer(id0)
        sl3.generate_part2()
        signal.signal(signal.SIGINT, bfcl_signal_handler)
        sl3.do_gpu()
    elif mode == 2:
        show_gpu_options()
        sl3.update_db()
        sl3.hash_clusterer(id0)
        sl3.generate_part2()
        signal.signal(signal.SIGINT, bfcl_signal_handler)
        sl3.do_gpu()
    elif mode == 3:
        sl3.update_db()
        sl3.hash_clusterer(id0)
        sl3.generate_part2()
        sl3.do_cpu()
    elif mode == 4:
        model = None
        year = None
        inp = input("Which model is the 3DS? (old/new) ")
        while True:
            if inp.lower() == "old":
                model = "old"
                break
            elif inp.lower() == "new":
                model = "new"
                break
            else:
                inp = input("Please enter a valid option (old/new): ")
        while True:
            inp = input("Which year was the 3DS built (if you're not sure/don't know, enter 0)? ")
            try:
                year = int(inp)
                break
            except ValueError:
                inp = ("Please enter the year was the 3DS built (if you're not sure/don't know, enter 0): ")
        sl3.mii_gpu(year, model)
        sl3.hash_clusterer(id0)
        sl3.generate_part2()
        sl3.offset_override = 0
        sl3.force_reduced_work_size = False
        signal.signal(signal.SIGINT, bfcl_signal_handler)
        sl3.do_gpu()
    ask_for_deletion()
    ask_for_renaming()
    print("Done")
    pause()

#Shows the GPU bruteforcing options if the corresponding option is selected
def show_gpu_options():
    ofs = 0
    while True:
        clear_screen()
        print(dedent("""Available options (and their respective current status):
        1. Enabled reduced work size: {} (default is False)
        2. Starting offset: {} (Default is 0)
        Type "s" when you're ready to start""".format(sl3.force_reduced_work_size, ofs)))
        inp = ask_list_input(2, True)
        if inp == 1:
            sl3.force_reduced_work_size = ask_yes_no(dedent("""
            Reduced work size allows to use less of your GPU while bruteforcing. This can be useful if the computer becomes unresponsive, but it will make the bruteforcing process slower.
            Do you want to enable reduced work size?"""))

        elif inp == 2:
            print(dedent("""
            This allows to resuming a previous bruteforcing job, by changing which offset to start bruteforcing at.
            WARNING! ONLY use this is you're resuming a previous bruteforce, and ONLY if you know exactly where it stopped!
            Don't use this to start bruteforcing at random offsets!"""))
            print("Which offset do you want to resume from? ", end="")
            while True:
                ofs = input()
                try:
                    sl3.offset_override = get_offset_arg(ofs)
                    break
                except ValueError:
                    print("Please enter a valid number: ", end="")
        elif inp == "s":
            print("")
            break
            
##########END OF FUNCTIONS##########

show_main_menu()