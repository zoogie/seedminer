import os,sys,struct,glob
import urllib.request
from binascii import hexlify, unhexlify

#don't change this mid brute force - can be different amount multiple computers - powers of two recommended for even distribution of workload 1 2 4 8 etc.
process_count=4
offset_override=0           #for gpu options, this allows starting brute-force at a user-defined offset
#-----------------------------------------------------------------------------------------------------------------
#Don't edit below this line unless you have multiple computers brute-forcing - most of you won't need this feature
#-----------------------------------------------------------------------------------------------------------------
number_of_computers=1       #each computer needs this set to same number if more than one
which_computer_is_this=0    #each computer has a different id # that's less than number_of_computers
#-----------------------------------------------------------------------------------------------------------------
#Don't edit below this line unless you know what you're doing (function defs begin)
#-----------------------------------------------------------------------------------------------------------------
lfcs=[]
ftune=[]
lfcs_new=[]
ftune_new=[]
err_correct=0
id0 = None

def int16bytes(n):
    return n.to_bytes(16, 'big')

def expand():
    for i in range(1,len(lfcs)):
        lfcs[i]=lfcs[i]<<12 | 0x800
        
    for i in range(1,len(lfcs_new)):
        lfcs_new[i]=lfcs_new[i]<<12 | 0x800

def bytes2int(s):
    n=0
    for i in range(4):
        n+=ord(s[i:i+1])<<(i*8)
    return n

def int2bytes(n):
    s=bytearray(4)
    for i in range(4):
        s[i]=n & 0xFF
        n=n>>8
    return s
    
def byteSwap4(n):
    # using a slice to reverse is better, and easier for bytes
    return n[::-1]
    
def endian4(n):
    return (n&0xFF000000)>>24 | (n&0x00FF0000)>>8 | (n&0x0000FF00)<<8 | (n&0x000000FF)<<24

def getMsed3Estimate(n,isNew):
    global err_correct
    newbit=0x0
    if isNew:
        fc=lfcs_new
        ft=ftune_new
        newbit=0x80000000
    else:
        fc=lfcs
        ft=ftune
        
    fc_size=len(fc)
    ft_size=len(ft)
    
    if fc_size != ft_size:
        return -1

    for i in range(fc_size):
        if n<fc[i]:
            xs=(n-fc[i-1])
            xl=(fc[i]-fc[i-1])
            y=ft[i-1]
            yl=(ft[i]-ft[i-1])
            ys=((xs*yl)//xl)+y
            err_correct=ys
            return ((n//5)-ys) | newbit
            
    return ((n//5)-ft[ft_size-1]) | newbit
    
def mii_gpu():
    from Cryptodome.Cipher import AES

    nk31=0x59FC817E6446EA6190347B20E9BDCE52
    with open("input.bin", "rb") as f:
        enc=f.read()
    if(len(enc) != 0x70):
        print("Error: input.bin is invalid size (likely QR -> input.bin conversion issue)")
        pause()
        sys.exit(0)
    nonce=enc[:8]+b"\x00"*4
    cipher = AES.new(int16bytes(nk31), AES.MODE_CCM, nonce )
    dec=cipher.decrypt(enc[8:0x60])
    nonce=nonce[:8]
    final=dec[:12]+nonce+dec[12:]

    with open("output.bin", "wb") as f:
        f.write(final)
    if(len(sys.argv) >= 3):
        model=sys.argv[2].lower()
    else:
        print("Error: need to specify new|old movable.sed")
        pause()
        sys.exit(0)
    model_str=b""
    start_lfcs_old=0x0B000000//2
    start_lfcs_new=0x05000000//2
    start_lfcs=0
    year=0
    if(len(sys.argv)==4):
            year=int(sys.argv[3])
        
    if(model=="old"):
        model_str=b"\x00\x00"
        if  (year==2011):
            start_lfcs_old=0x01000000
        elif(year==2012):
            start_lfcs_old=0x04000000
        elif(year==2013):
            start_lfcs_old=0x07000000
        elif(year==2014):
            start_lfcs_old=0x09000000
        elif(year==2015):
            start_lfcs_old=0x09800000
        elif(year==2016):
            start_lfcs_old=0x0A000000
        elif(year==2017):
            start_lfcs_old=0x0A800000
        else:
            print("Year 2011-2017 not entered so beginning at lfcs midpoint "+hex(start_lfcs_old))
        start_lfcs=start_lfcs_old
        
    elif(model=="new"):
        model_str=b"\x02\x00"
        if    (year==2014):
            start_lfcs_new=0x00800000
        elif  (year==2015):
            start_lfcs_new=0x01800000
        elif  (year==2016):
            start_lfcs_new=0x03000000
        elif  (year==2017):
            start_lfcs_new=0x04000000
        else:
            print("Year 2014-2017 not entered so beginning at lfcs midpoint "+hex(start_lfcs_new))
        start_lfcs=start_lfcs_new
    start_lfcs=endian4(start_lfcs)
    command="bfcl lfcs %08X %s %s %08X" % (start_lfcs, hexlify(model_str).decode('ascii'), hexlify(final[4:4+8]).decode('ascii'), endian4(offset_override))
    print(command)
    os.system(command)

def generate_part2():
    global err_correct
    with open("saves/lfcs.dat", "rb") as f:
        buf=f.read()

    lfcs_len=len(buf)//8
    err_correct=0

    for i in range(lfcs_len):
        lfcs.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

    for i in range(lfcs_len):
        ftune.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])

    with open("saves/lfcs_new.dat", "rb") as f:
        buf=f.read()

    lfcs_new_len=len(buf)//8

    for i in range(lfcs_new_len):
        lfcs_new.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

    for i in range(lfcs_new_len):
        ftune_new.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])

    isNew=False
    msed3=0
    noobtest=b"\x00"*0x20
    with open("movable_part1.sed", "rb") as f:
        seed=f.read()
    if(noobtest in seed[0x10:0x30]):
        print("Error: ID0 has been left blank, please add an ID0")
        print("Ex: python %s id0 abcdef012345EXAMPLEdef0123456789" % (sys.argv[0]))
        pause()
        sys.exit(0)
    if(noobtest[:4] in seed[:4]):
        print("Error: LFCS has been left blank, did you do a complete two-way friend code exchange before dumping friendlist?")
        pause()
        sys.exit(0)
    if len(seed) != 0x1000:
        print("Error: movable_part1.sed is not 4KB")
        pause()
        sys.exit(0)
        
    if seed[4:5]==b"\x02":
        print("New3DS msed")
        isNew=True
    elif seed[4:5]==b"\x00":
        print("Old3DS msed - this can happen on a New3DS")
        isNew=False
    else:
        print("Error: can't read u8 msed[4]")
        pause()
        sys.exit(0)

    expand()
    print("LFCS      : "+hex(bytes2int(seed[0:4])))
    print("msed3 est : "+hex(getMsed3Estimate(bytes2int(seed[0:4]),isNew)))
    print("Error est : "+str(err_correct))
    msed3=getMsed3Estimate(bytes2int(seed[0:4]),isNew)

    offset=0x10
    hash_final=b""
    for i in range(64):
        try:
            hash=unhexlify(seed[offset:offset+0x20])
        except:
            break
        hash_single=byteSwap4(hash[0:4])+byteSwap4(hash[4:8])+byteSwap4(hash[8:12])+byteSwap4(hash[12:16])
        print("ID0 hash "+str(i)+": "+hexlify(hash_single).decode('ascii'))
        hash_final+=hash_single
        offset+=0x20

    print("Hash total: "+str(i))
    part2=seed[0:12]+int2bytes(msed3)+hash_final

    pad=0x1000-len(part2)
    part2+=b"\x00"*pad

    with open("movable_part2.sed", "wb") as f:
        f.write(part2)
    print("movable_part2.sed generation success")

def hash_clusterer():
    buf=b""
    hashcount=0

    if(len(sys.argv)==3):
        dirs=[]
        dirs.append(sys.argv[2])
    elif(id0 != None):
        dirs=[]
        dirs.append(id0)
    else:
        dirs=glob.glob("*")
        
    try:
        with open("movable_part1.sed", "rb") as f:
            file=f.read()
    except:
        inp = ask_yes_no("movable_part1.sed not found, do you want to generate a new one?")
        if(inp == True):
            print("don't forget to add an lfcs to it!\n")
            pause()
            with open("movable_part1.sed", "wb") as f:
                file=b"\x00"*0x1000
                f.write(file)
        else:
            sys.exit(0)

    for i in dirs:
        try:
            temp=str(i).encode("ascii")
            print(i,end='')
            int(i,16)
            if(len(i)==32): #Even if the ID0 is already in the file, it works too
                buf+=temp
                hashcount+=1
            else:
                print(" -- improper ID0 length",end='')
            print("")
        except:
            print(" -- not an ID0")
        
    print("")
    if(hashcount>1):
        print("Too many ID0 dirs! (%d)\nMove the ones your 3ds isn't using!" % (hashcount))
        pause()
        sys.exit(0)
        
    if(hashcount==1):
        print("Hash added!")
    else:
        print("No hashes added!")
        sys.exit(0)
        
    with open("movable_part1.sed.backup", "wb") as f:
        f.write(file)
    
    file=file[:0x10]
    pad_len=0x1000-len(file+buf)
    pad=b"\x00"*pad_len
    with open("movable_part1.sed", "wb") as f:
        f.write(file+buf+pad)
    print("There are now %d ID0 hashes in your movable_part1.sed!" % ((len(file+buf)//0x20)))
    print("Done!")

def do_cpu():
    global process_count
    if(len(sys.argv)==3):
        process_count=int(sys.argv[2])
        
    if(which_computer_is_this >= number_of_computers):
        print("You can't assign an id # to a computer that doesn't exist")
        pause()
        sys.exit(0)

    MAX=0x100000000
    address_begin=0
    address_end=MAX

    address_space=MAX//number_of_computers

    for i in range(number_of_computers):
        if(which_computer_is_this==i):
            address_begin=(i*address_space)
            address_end=(address_begin+address_space)
            print("This computer id: "+str(i));
    if(which_computer_is_this==number_of_computers-1):
        address_end=MAX

    print("Overall starting msed2 address: "+hex(address_begin))
    print("Overall ending   msed2 address: "+hex(address_end))
    print("")

    process_space=address_end-address_begin
    process_size=process_space//process_count

    for i in range(process_count):
        process_begin=address_begin+(process_size*i)
        process_end=process_begin+process_size
        if(i==(process_count-1)):
            process_end=address_end
        start=process_begin
        size=process_end-process_begin
        os.system("start seedMiner.exe %08X %09X" % (start,size))
        print("Process: "+str(i)+" Start: "+hex(process_begin)+" Size: "+hex(size))
        
def do_gpu():
    with open("movable_part2.sed", "rb") as f:
        buf=f.read()
    keyy=hexlify(buf[:16]).decode('ascii')
    ID0=hexlify(buf[16:32]).decode('ascii')
    command="bfcl msky %s %s %08X" % (keyy,ID0, endian4(offset_override))
    print(command)
    try:
        os.system(command)
    except KeyboardInterrupt:
        print("Bruteforcing aborted. If you're planning on resuming it, make sure to TAKE NOTE of the offset value above!")

def download(url, dest):
    try:
        response = urllib.request.urlopen(url)
        html = response.read()
        data=""
        with open(dest, "rb") as f:
            data=f.read()
        if(data != html):
            with open(dest, "wb") as f:
                f.write(html)
                print("Updating "+dest+" success!")
        else:
            print(dest+" is already up-to-date!")
    except:
        print("Error updating "+dest)
    
def update_db():
    download("https://github.com/zoogie/seedminer/blob/master/seedminer/saves/lfcs.dat?raw=true","saves/lfcs.dat")
    download("https://github.com/zoogie/seedminer/blob/master/seedminer/saves/lfcs_new.dat?raw=true","saves/lfcs_new.dat")
    
def error_print():
    print("\nCommand line error")
    print("Usage:")
    print("python %s cpu|gpu|id0|mii old|mii new|update-db [# cpu processes] [ID0 hash] [year 3ds built] [continue from offset #]" % (sys.argv[0]))
    print("Examples:")
    print("python %s cpu 4" % (sys.argv[0]))
    print("python %s gpu" % (sys.argv[0]))
    print("python %s gpu -12" % (sys.argv[0]))
    print("python %s id0 abcdef012345EXAMPLEdef0123456789" % (sys.argv[0]))
    print("python %s mii new 2017" % (sys.argv[0]))
    print("python %s mii old 2011" % (sys.argv[0]))
    print("python %s mii old" % (sys.argv[0]))
    print("python %s update-db" % (sys.argv[0]))
    print("Running the script without any arguments will bring up a menu where you can select what to do")
    
def ask_yes_no(msg):
    while True:
        inp = input(msg + " (y/n) ")
        if (inp.lower() == "y"):
            return True
        elif (inp.lower() == "n"):
            return False;
            
def ask_list_input(count):
    while True:
        try:
            rang = range(1, count + 1)
            inp = input("\nPlease select an option: ")
            if(int(inp) in rang):
                return int(inp)
            else:
                raise ValueError
        except ValueError:
            print("Please enter a valid number")
            
def pause():
    input("Press any key to continue...")
    
def ask_for_deletion():
    inp = ask_yes_no("Do you want to delete no longer needed files? ")
    if(inp == True):
        try:
            os.remove("movable_part1.sed")
            os.remove("movable_part1.sed.backup")
            os.remove("movable_part2.sed")
            os.remove("input.bin")
        except FileNotFoundError:
            print("", end="") #really stupid workaround
        
def ask_for_renaming():
    inp = ask_yes_no("Do you want to rename the movable.sed file to contain the friend code?")
    if(inp == True):
        inp = input("Enter the friend code: ")
        fc = ''.join([i for i in inp if i.isdigit()])
        os.rename("movable.sed", "movable_" + fc + ".sed")

        
#---------------------------------------------------------------------------
#command handler
#---------------------------------------------------------------------------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)



if(len(sys.argv) > 4):
    error_print()
    sys.exit(0)
	
if(len(sys.argv) == 1):
    print("Available options: ")
    print("1. CPU bruteforce")
    print("2. GPU bruteforce (normal)")
    print("3. GPU bruteforce (restore from offset)")
    print("4. Mii bruteforce")
    print("Note: saves/lfcs and saves/lfcs_new will be automatically updated")
    inp = ask_list_input(4)
    if(inp != 4):
        id0 = input("Enter the ID0: ")
    if(inp == 1):
        update_db()
        hash_clusterer()
        generate_part2()
        do_cpu()
    elif(inp == 2):
        update_db()
        hash_clusterer()
        generate_part2()
        do_gpu()
    elif(inp == 3):
        while True:
            try:
                ofs = int(input("Which offset do you want to resume from? "))
                if(ofs == 0):
                    offset_override = 0
                elif(ofs > 0):
                    offset_override = ofs * 2 - 1
                else:
                    offset_override = abs(ofs) * 2
                print("Bruteforcing will resume on offset %d" % ofs)
                break
            except ValueError:
                print("Please enter a valid number")
        update_db()
        hash_clusterer()
        generate_part2()
        do_gpu()
    elif(inp == 4):
        mii_gpu()
        generate_part2()
        offset_override=0
        do_gpu()
    ask_for_deletion()
    ask_for_renaming()
    sys.exit(0)
        
if(sys.argv[1].lower() == "gpu"):
    print("GPU selected")
    if(len(sys.argv)==3):
        try:
            ofs = int(sys.argv[2])
            if(ofs == 0):
                offset_override = 0
            elif(ofs > 0):
                offset_override = ofs * 2 - 1
            else:
                offset_override = abs(ofs) * 2
            print("Bruteforcing will resume on offset %d" % ofs)
        except:
            print("Error: the specified offset number isn't an integer")
            pause()
            sys.exit(0)
    generate_part2()
    do_gpu()
    sys.exit(0)
elif(sys.argv[1].lower()=="cpu"):
    print("CPU selected")
    generate_part2()
    do_cpu()
    sys.exit(0)
elif(sys.argv[1].lower()=="id0"):
    print("ID0 selected")
    hash_clusterer()
    sys.exit(0)
elif(sys.argv[1].lower()=="mii"):
    print("MII selected")
    mii_gpu()
    generate_part2()
    offset_override=0
    do_gpu()
    sys.exit(0)
elif(sys.argv[1].lower()=="update-db"):
    print("Update msed_data selected")
    update_db()
    sys.exit(0)
else:
    error_print()
    sys.exit(0)
