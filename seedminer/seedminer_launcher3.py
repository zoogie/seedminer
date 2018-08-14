# Seedminer vX.X.X
from binascii import hexlify, unhexlify
from textwrap import dedent
import glob
import os
import signal
import struct
import subprocess
import sys
import time
import urllib.request

# don't change this mid brute force - can be different amount multiple computers - powers of two recommended for even distribution of workload 1 2 4 8 etc.
process_count = 4
# -----------------------------------------------------------------------------------------------------------------
# Note: Optional argument parsing will override the following two variables and multiply them by 2!
# If optional arguments are not provided, the following two variables will not be multiplied.
# ---
# for gpu options
offset_override = 0  # this allows starting brute-force at a user-defined offset
# ---
# only for the do_gpu() function (movable.sed brute-forcing)
max_msky_offset = 16384  # this allows ending at a user-defined offset; 16384 should be considered the max though!
# -----------------------------------------------------------------------------------------------------------------
# for gpu options
# set this variable to "True" (without the quotes) if you want to use less of your gpu while mining
# your hash rate will decrease by a bit
force_reduced_work_size = False
# -----------------------------------------------------------------------------------------------------------------
# Don't edit below this line unless you have multiple computers brute-forcing - most of you won't need this feature
# -----------------------------------------------------------------------------------------------------------------
number_of_computers = 1  # each computer needs this set to same number if more than one
which_computer_is_this = 0  # each computer has a different id # that's less than number_of_computers
# -----------------------------------------------------------------------------------------------------------------
# Don't edit below this line unless you know what you're doing (function defs begin)
# -----------------------------------------------------------------------------------------------------------------
lfcs = []
ftune = []
lfcs_new = []
ftune_new = []
err_correct = 0
os_name = os.name
id0 = None
year = 0


def signal_handler(sig, frame):  # So KeyboardInterrupt exceptions don't appear
    sys.exit(0)
    
def bfcl_signal_handler(sig, frame): #Shows a message if the users interrupts bruteforcing
    print("\nBruteforcing aborted by the user. If you want to resume it later, TAKE NOTE of the offset value shown above!")
    pause()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def int16bytes(n):
    return n.to_bytes(16, 'big')


def expand():
    for i in range(1, len(lfcs)):
        lfcs[i] = lfcs[i] << 12 | 0x800
        
    for i in range(1, len(lfcs_new)):
        lfcs_new[i] = lfcs_new[i] << 12 | 0x800


def bytes2int(s):
    n = 0
    for i in range(4):
        n += ord(s[i:i + 1]) << (i * 8)
    return n


def int2bytes(n):
    s = bytearray(4)
    for i in range(4):
        s[i] = n & 0xFF
        n = n >> 8
    return s


def byteswap4(n):
    # using a slice to reverse is better, and easier for bytes
    return n[::-1]


def endian4(n):
    return (n & 0xFF000000) >> 24 | (n & 0x00FF0000) >> 8 | (n & 0x0000FF00) << 8 | (n & 0x000000FF) << 24


def getmsed3estimate(n, isnew):
    global err_correct
    newbit = 0x0
    if isnew:
        fc = lfcs_new
        ft = ftune_new
        newbit = 0x80000000
    else:
        fc = lfcs
        ft = ftune

    fc_size = len(fc)
    ft_size = len(ft)

    if fc_size != ft_size:
        return -1

    for i in range(fc_size):
        if n < fc[i]:
            xs = (n - fc[i - 1])
            xl = (fc[i] - fc[i - 1])
            y = ft[i - 1]
            yl = (ft[i] - ft[i - 1])
            ys = ((xs * yl) // xl) + y
            err_correct = ys
            return ((n // 5) - ys) | newbit

    return ((n // 5) - ft[ft_size - 1]) | newbit


def mii_gpu():
    global model
    global year

    from Cryptodome.Cipher import AES

    nk31 = 0x59FC817E6446EA6190347B20E9BDCE52
    with open("input.bin", "rb") as f:
        enc = f.read()
    if len(enc) != 0x70:
        print("Error: input.bin is invalid size (likely QR -> input.bin conversion issue)")
        pause()
        sys.exit(1)
    nonce = enc[:8] + b"\x00" * 4
    cipher = AES.new(int16bytes(nk31), AES.MODE_CCM, nonce)
    dec = cipher.decrypt(enc[8:0x60])
    nonce = nonce[:8]
    final = dec[:12] + nonce + dec[12:]

    with open("output.bin", "wb") as f:
        f.write(final)
    if len(sys.argv) >= 3:
        model = sys.argv[2].lower()
    elif len(sys.argv) != 1:
        print("Error: need to specify new|old movable.sed")
        pause()
        sys.exit(1)
    model_str = b""
    start_lfcs_old = 0x0B000000 // 2
    start_lfcs_new = 0x05000000 // 2
    start_lfcs = 0
    if len(sys.argv) == 4:
            year = int(sys.argv[3])

    if model == "old":
        model_str = b"\x00\x00"
        if year == 2011:
            start_lfcs_ol
            d = 0x01000000
        elif year == 2012:
            start_lfcs_old = 0x04000000
        elif year == 2013:
            start_lfcs_old = 0x07000000
        elif year == 2014:
            start_lfcs_old = 0x09000000
        elif year == 2015:
            start_lfcs_old = 0x09800000
        elif year == 2016:
            start_lfcs_old = 0x0A000000
        elif year == 2017:
            start_lfcs_old = 0x0A800000
        else:
            print("Year 2011-2017 not entered so beginning at lfcs midpoint " + hex(start_lfcs_old))
        start_lfcs = start_lfcs_old

    elif model == "new":
        model_str = b"\x02\x00"
        if year == 2014:
            start_lfcs_new = 0x00800000
        elif year == 2015:
            start_lfcs_new = 0x01800000
        elif year == 2016:
            start_lfcs_new = 0x03000000
        elif year == 2017:
            start_lfcs_new = 0x04000000
        else:
            print("Year 2014-2017 not entered so beginning at lfcs midpoint " + hex(start_lfcs_new))
        start_lfcs = start_lfcs_new
    start_lfcs = endian4(start_lfcs)
    if os_name == 'nt':
        init_command = "bfcl lfcs {:08X} {} {} {:08X}".format(start_lfcs, hexlify(model_str).decode('ascii'), hexlify(final[4:4 + 8]).decode('ascii'), endian4(offset_override))
    else:
        init_command = "./bfcl lfcs {:08X} {} {} {:08X}".format(start_lfcs, hexlify(model_str).decode('ascii'), hexlify(final[4:4 + 8]).decode('ascii'), endian4(offset_override))
    print(init_command)
    
    signal.signal(signal.SIGINT, bfcl_signal_handler)
    
    if force_reduced_work_size is True:
        command = "{} rws".format(init_command)
        subprocess.call(command.split())
    else:
        command = "{} sws sm".format(init_command)
        proc = subprocess.call(command.split())
        if proc == 251 or proc == 4294967291:  # Help wanted for a better way of catching an exit code of '-5'
            time.sleep(3)  # Just wait a few seconds so we don't burn out our graphics card
            subprocess.call("{} rws sm".format(init_command).split())


def generate_part2():
    global err_correct
    with open("saves/lfcs.dat", "rb") as f:
        buf = f.read()

    lfcs_len = len(buf) // 8
    err_correct = 0

    for i in range(lfcs_len):
        lfcs.append(struct.unpack("<i", buf[i*8:i*8+4])[0])

    for i in range(lfcs_len):
        ftune.append(struct.unpack("<i", buf[i*8+4:i*8+8])[0])

    with open("saves/lfcs_new.dat", "rb") as f:
        buf = f.read()

    lfcs_new_len = len(buf) // 8

    for i in range(lfcs_new_len):
        lfcs_new.append(struct.unpack("<i", buf[i*8:i*8+4])[0])

    for i in range(lfcs_new_len):
        ftune_new.append(struct.unpack("<i", buf[i*8+4:i*8+8])[0])

    noobtest = b"\x00" * 0x20
    with open("movable_part1.sed", "rb") as f:
        seed = f.read()
    if noobtest in seed[0x10:0x30]:
        print("Error: ID0 has been left blank, please add an ID0")
        print("Ex: python {} id0 abcdef012345EXAMPLEdef0123456789".format(sys.argv[0]))
        pause()
        sys.exit(1)
    if noobtest[:4] in seed[:4]:
        print("Error: LFCS has been left blank, did you do a complete two-way friend code exchange before dumping friendlist?")
        pause()
        sys.exit(1)
    if len(seed) != 0x1000:
        print("Error: movable_part1.sed is not 4KB")
        pause()
        sys.exit(1)
    if seed[4:5] == b"\x02":
        print("New3DS msed")
        isnew = True
    elif seed[4:5] == b"\x00":
        print("Old3DS msed - this can happen on a New3DS")
        isnew = False
    else:
        print("Error: can't read u8 msed[4]")
        pause()
        sys.exit(1)

    expand()
    print("LFCS      : " + hex(bytes2int(seed[0:4])))
    print("msed3 est : " + hex(getmsed3estimate(bytes2int(seed[0:4]), isnew)))
    print("Error est : " + str(err_correct))
    msed3 = getmsed3estimate(bytes2int(seed[0:4]), isnew)

    offset = 0x10
    hash_final = b""
    i = None
    for i in range(64):
        try:
            hash_init = unhexlify(seed[offset:offset + 0x20])
        except:
            break
        hash_single = byteswap4(hash_init[0:4]) + byteswap4(hash_init[4:8]) + byteswap4(hash_init[8:12]) + byteswap4(hash_init[12:16])
        print("ID0 hash " + str(i) + ": " + hexlify(hash_single).decode('ascii'))
        hash_final += hash_single
        offset += 0x20
    print("Hash total: " + str(i))

    part2 = seed[0:12] + int2bytes(msed3) + hash_final

    pad = 0x1000 - len(part2)
    part2 += b"\x00" * pad

    with open("movable_part2.sed", "wb") as f:
        f.write(part2)
    print("movable_part2.sed generation success")

#Checks if an ID0 is valid, and returns True or False accordingly
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

def hash_clusterer():
    global id0
    
    buf = b""
    hashcount = 0

    if len(sys.argv) == 3:
        dirs = [sys.argv[2]]
    else:
        dirs = glob.glob("*")

    try:
        with open("movable_part1.sed", "rb") as f:
            file = f.read()
    except IOError:
        print("movable_part1.sed not found, generating a new one")
        print("don't forget to add an lfcs to it!\n")
        with open("movable_part1.sed", "wb") as f:
            file = b"\x00" * 0x1000
            f.write(file)

    if id0 == None:
        for i in dirs:
            if is_id0_valid(i):
                buf += str(i).encode("ascii")
                hashcount += 1
    else:
        buf += str(id0).encode("ascii")
        hashcount += 1
        
    print(id0)

    if hashcount > 1:
        print("Too many ID0 dirs! ({})\nMove the ones your 3DS isn't using!".format(hashcount))
        pause()
        sys.exit(1)

    if hashcount == 1:
        print("Hash added!")
    else:
        print("No hashes added!")
        pause()
        sys.exit(0)

    with open("movable_part1.sed.backup", "wb") as f:
        f.write(file)

    file = file[:0x10]
    pad_len = 0x1000 - len(file+buf)
    pad = b"\x00" * pad_len
    with open("movable_part1.sed", "wb") as f:
        f.write(file + buf + pad)
    print("There are now {} ID0 hashes in your movable_part1.sed!".format(len(file + buf) // 0x20))
    print("Done!")


def do_cpu():
    global process_count
    if len(sys.argv) == 3:
        process_count = int(sys.argv[2])

    if which_computer_is_this >= number_of_computers:
        print("You can't assign an id # to a computer that doesn't exist")
        pause()
        sys.exit(1)

    max_1 = 0x100000000
    address_begin = 0
    address_end = max_1

    address_space = max_1 // number_of_computers

    for i in range(number_of_computers):
        if which_computer_is_this == i:
            address_begin = (i * address_space)
            address_end = (address_begin + address_space)
            print("This computer id: " + str(i))
    if which_computer_is_this == number_of_computers - 1:
        address_end = max_1

    print("Overall starting msed2 address: " + hex(address_begin))
    print("Overall ending   msed2 address: " + hex(address_end) + "\n")

    process_space = address_end - address_begin
    process_size = process_space // process_count

    signal.signal(signal.SIGINT, bfcl_signal_handler)
    
    multi_procs = []
    for i in range(process_count):
        process_begin = address_begin + (process_size * i)
        process_end = process_begin + process_size
        if i == process_count - 1:
            process_end = address_end
        start = process_begin
        size = process_end - process_begin
        time.sleep(0.25)  # For readability and organization
        print("\nProcess: " + str(i) + " Start: " + hex(process_begin) + " Size: " + hex(size))
        if os_name == 'nt':
            proc = subprocess.Popen("seedminer {:08X} {:09X}".format(start, size).split())
        else:
            proc = subprocess.Popen("./seedminer {:08X} {:09X}".format(start, size).split())
        multi_procs.append(proc)
    for proc in multi_procs:
        proc.wait()


def do_gpu():
    with open("movable_part2.sed", "rb") as f:
        buf = f.read()
    keyy = hexlify(buf[:16]).decode('ascii')
    id0 = hexlify(buf[16:32]).decode('ascii')
    if os_name == 'nt':
        init_command = "bfcl msky {} {} {:08X} {:08X}".format(keyy, id0, endian4(offset_override), endian4(max_msky_offset))
    else:
        init_command = "./bfcl msky {} {} {:08X} {:08X}".format(keyy, id0, endian4(offset_override), endian4(max_msky_offset))
    print(init_command)
    
    signal.signal(signal.SIGINT, bfcl_signal_handler)
    
    if force_reduced_work_size is True:
        command = "{} rws".format(init_command)
        proc = subprocess.call(command.split())
    else:
        command = "{} sws sm".format(init_command)
        proc = subprocess.call(command.split())
        if proc == 251 or proc == 4294967291:  # Help wanted for a better way of catching an exit code of '-5'
            time.sleep(3)  # Just wait a few seconds so we don't burn out our graphics card
            command = "{} rws sm".format(init_command)
            proc = subprocess.call(command.split())
    return proc


def download(url, dest):
    try:
        response = urllib.request.urlopen(url)
        html = response.read()
        with open(dest, "rb") as f:
            data = f.read()
        if data != html:
            with open(dest, "wb") as f:
                f.write(html)
                print("Updating " + dest + " success!")
        else:
            print(dest + " is already up-to-date!")
    except:
        print("Error updating " + dest)


def update_db():
    download("https://github.com/zoogie/seedminer/blob/master/seedminer/saves/lfcs.dat?raw=true", "saves/lfcs.dat")
    download("https://github.com/zoogie/seedminer/blob/master/seedminer/saves/lfcs_new.dat?raw=true", "saves/lfcs_new.dat")


def error_print():
    print(dedent("""
    Command line error
    Usage:
    python {0} cpu|gpu|id0|mii old|mii new|update-db [# cpu processes] [starting gpu offset] [max gpu offset] [ID0 hash] [year 3ds built]
    Examples:
    python {0} cpu
    python {0} cpu 4
    python {0} gpu
    python {0} gpu 0
    python {0} gpu 0 8192
    python {0} id0 abcdef012345EXAMPLEdef0123456789
    python {0} mii new 2017
    python {0} mii old 2011
    python {0} mii new
    python {0} mii old
    python {0} update-db
    
    Starting the script without any arguments will bring up the mode selection menu instead.""".format(sys.argv[0])))

###########USER INTERFACE RELATED VARIABLES###########
##PREPARE, LOTS OF NEWLY DEFINED FUNCTIONS INCOMING!##

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
            
#"Press any key to continue" message
def pause(alt_msg = None):
    if alt_msg == None:
        input("Press any key to continue...")
    else:
        input(alt_msg)
   
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
    global offset_override
    ofs = int(ofs)
    if ofs == 0:
        offset_override = 0
    elif ofs > 0:
        offset_override = ofs * 2 - 1
    else:
        offset_override = abs(ofs) * 2
    print("Bruteforcing will resume on offset {}".format(ofs))
    
#Shows the main menu
def show_main_menu():
    global id0
    clear_screen()
    #Protip about dedent: by doing like this print statement below, eg triple quotes without immediately going to a new line, the other lines will still show one unit of indent. On the other hand, immediately going to a new line after the quotes (like in show_gpu_options()) will make everything dedented.
    print(dedent("""Available options:
    1. GPU bruteforce (normal)
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
        update_db()
        hash_clusterer()
        generate_part2()
        do_gpu()
    elif mode == 2:
        show_gpu_options()
        update_db()
        hash_clusterer()
        generate_part2()
        do_gpu()
    elif mode == 3:
        update_db()
        hash_clusterer()
        generate_part2()
        do_cpu()
    elif mode == 4:
        global model
        global year
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
        mii_gpu()
        generate_part2()
        offset_override = 0
        do_gpu()
    ask_for_deletion()
    ask_for_renaming()

#Shows the GPU bruteforcing options if the corresponding "mode" is selected
def show_gpu_options():
    global force_reduced_work_size
    global offset_override
    ofs = 0
    while True:
        clear_screen()
        print(dedent("""Available options (and their respective current status):
        1. Enabled reduced work size: {} (default is False)
        2. Starting offset: {} (Default is 0)
        Type "s" when you're ready to start""".format(force_reduced_work_size, ofs)))
        inp = ask_list_input(2, True)
        if inp == 1:
            force_reduced_work_size = ask_yes_no(dedent("""
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
                    get_offset_arg(ofs)
                    break
                except ValueError:
                    print("Please enter a valid number: ", end="")
        elif inp == "s":
            break
    
# ---------------------------------------------------------------------------
# command handler
# ---------------------------------------------------------------------------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if len(sys.argv) > 4:
    error_print()
    pause()
    sys.exit(1)
	
#If no arguments have been specified, the text-based menu will show up.
if len(sys.argv) == 1:
    show_main_menu()
    sys.exit(0)

if sys.argv[1].lower() == "gpu":
    if len(sys.argv) == 3 or len(sys.argv) == 4:
        try:
            offset_override = get_offset_arg(sys.argv[2])
        except ValueError:
            print("Invalid parameter supplied!")
            pause()
            sys.exit(1)
    if len(sys.argv) == 4:
        try:
            max_msky_offset = int(sys.argv[3]) * 2
        except ValueError:
            print("Invalid parameter supplied!")
            pause()
            sys.exit(1)
    print("GPU selected")
    generate_part2()
    sys.exit(do_gpu())
elif sys.argv[1].lower() == "cpu":
    print("CPU selected")
    generate_part2()
    do_cpu()
    sys.exit(0)
elif sys.argv[1].lower() == "id0":
    print("ID0 selected")
    hash_clusterer()
    sys.exit(0)
elif sys.argv[1].lower() == "mii":
    print("MII selected")
    mii_gpu()
    generate_part2()
    offset_override = 0
    sys.exit(do_gpu())
elif sys.argv[1].lower() == "update-db":
    print("Update msed_data selected")
    update_db()
    sys.exit(0)
else:
    error_print()
    pause()
    sys.exit(1)
