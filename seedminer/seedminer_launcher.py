from __future__ import print_function
import os,sys,struct,glob

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

def int16bytes(n):
	s=""
	for i in range(16):
		s=chr(n & 0xFF)+s
		n=n>>8
	return s

def expand():
	for i in range(1,len(lfcs)):
		lfcs[i]=lfcs[i]<<12 | 0x800
		
	for i in range(1,len(lfcs_new)):
		lfcs_new[i]=lfcs_new[i]<<12 | 0x800

def bytes2int(s):
	n=0
	for i in range(4):
		n+=ord(s[i])<<(i*8)
	return n

def int2bytes(n):
	str=bytearray(4)
	for i in range(4):
		str[i]=n & 0xFF
		n=n>>8
	return str
	
def byteSwap4(n):
	return n[3]+n[2]+n[1]+n[0]
	
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
			ys=((xs*yl)/xl)+y
			err_correct=ys
			return ((n/5)-ys) | newbit
			
	return ((n/5)-ft[ft_size-1]) | newbit
	
def mii_gpu():
	from Cryptodome.Cipher import AES

	nk31=0x59FC817E6446EA6190347B20E9BDCE52
	f=open("input.bin","rb")
	enc=f.read()
	f.close()

	nonce=enc[:8]+"\x00"*4
	cipher = AES.new(int16bytes(nk31), AES.MODE_CCM, nonce )
	dec=cipher.decrypt(enc[8:0x60])
	nonce=nonce[:8]
	final=dec[:12]+nonce+dec[12:]

	f=open("output.bin","wb")
	f.write(final)
	f.close()
	if(len(sys.argv) >= 3):
		model=sys.argv[2].lower()
	else:
		print("Error: need to specify new|old movable.sed")
		sys.exit(0)
	model_str=""
	start_lfcs_old=0x0B000000/2
	start_lfcs_new=0x05000000/2
	start_lfcs=0
	year=0
	if(len(sys.argv)==4):
			year=int(sys.argv[3])
		
	if(model=="old"):
		model_str="\x00\x00"
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
		model_str="\x02\x00"
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
	command="bfcl lfcs %08X %s %s %08X" % (start_lfcs, model_str.encode("hex"), final[4:4+8].encode("hex"), endian4(offset_override))
	print(command)
	os.system(command)

def generate_part2():
	global err_correct
	f=open("saves/lfcs.dat","rb")
	buf=f.read()
	f.close()

	lfcs_len=len(buf)/8
	err_correct=0

	for i in range(lfcs_len):
		lfcs.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

	for i in range(lfcs_len):
		ftune.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])

	f=open("saves/lfcs_new.dat","rb")
	buf=f.read()
	f.close()

	lfcs_new_len=len(buf)/8

	for i in range(lfcs_new_len):
		lfcs_new.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

	for i in range(lfcs_new_len):
		ftune_new.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])

	isNew=False
	msed3=0
	noobtest="\x00"*0x20
	f=open("movable_part1.sed","rb")
	seed=f.read()
	f.close()
	if(noobtest in seed[0x10:0x30]):
		print("Error: ID0 has been left blank, please add an ID0")
		print("Ex: python %s id0 abcdef0123456789abcdef0123456789" % (sys.argv[0]))
		sys.exit(0)
	if(noobtest[:4] in seed[:4]):
		print("Error: LFCS has been left blank, did you do a complete two-way friend code exchange before dumping friendlist?")
		sys.exit(0)
	if len(seed) != 0x1000:
		print("Error: movable_part1.sed is not 4KB")
		sys.exit(0)
		
	if seed[4]=="\x02":
		print("New3DS msed")
		isNew=True
	elif seed[4]=="\x00":
		print("Old3DS msed - this can happen on a New3DS")
		isNew=False
	else:
		print("Error: can't read u8 msed[4]")
		sys.exit(0)

	expand()
	print("LFCS      : "+hex(bytes2int(seed[0:4])))
	print("msed3 est : "+hex(getMsed3Estimate(bytes2int(seed[0:4]),isNew)))
	print("Error est : "+str(err_correct))
	msed3=getMsed3Estimate(bytes2int(seed[0:4]),isNew)

	offset=0x10
	hash_final=""
	for i in range(64):
		try:
			hash=seed[offset:offset+0x20].decode("hex")
		except:
			break
		hash_single=byteSwap4(hash[0:4])+byteSwap4(hash[4:8])+byteSwap4(hash[8:12])+byteSwap4(hash[12:16])
		print("ID0 hash "+str(i)+": "+hash_single.encode('hex'))
		hash_final+=hash_single
		offset+=0x20

	print("Hash total: "+str(i))
	part2=seed[0:12]+int2bytes(msed3)+hash_final

	pad=0x1000-len(part2)
	part2+="\x00"*pad

	f=open("movable_part2.sed","wb")
	f.write(part2)
	f.close()
	print("movable_part2.sed generation success")

def hash_clusterer():
	buf=""
	hashcount=0

	f=open("movable_part1.sed","rb")
	file=f.read()
	f.close()
	f=open("movable_part1.sed.backup","wb")
	f.write(file)
	f.close()

	trim=0
	try:
		trim=file.index("\x00"*0x40)
		if(trim<0x10):
			trim=0x10
		file=file[:trim]
	except:
		pass
	
	if(len(sys.argv)==3):
		dirs=[]
		dirs.append(sys.argv[2])
	else:
		dirs=glob.glob("*")

	for i in dirs:
		try:
			print(i,end='')
			int(i,16)
			if(len(i)==32 and i not in file):
				buf+=i
				hashcount+=1
			else:
				print(" -- improper ID0 length or already in file",end='')
			print("")
		except:
			print(" -- not an ID0")
		
	print("")
	if(hashcount>1):
		print("Too many ID0 dirs! (%d)\nMove the ones your 3ds isn't using!" % (hashcount))
		sys.exit(0)

	if(hashcount==1):
		print("Hash added!")
	else:
		print("No hashes added!")
	pad_len=0x1000-len(file+buf)
	pad="\x00"*pad_len
	f=open("movable_part1.sed","wb")
	f.write(file+buf+pad)
	f.close()
	print("There are now %d ID0 hashes in your movable_part1.sed!" % ((len(file+buf)/0x20)))
	print("Done!")

def do_cpu():
	global process_count
	if(len(sys.argv)==3):
		process_count=int(sys.argv[2])
		
	if(which_computer_is_this >= number_of_computers):
		print("You can't assign an id # to a computer that doesn't exist")
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
	f=open("movable_part2.sed","rb")
	buf=f.read()
	f.close()
	keyy=buf[:16].encode('hex')
	ID0=buf[16:32].encode('hex')
	command="bfcl msky %s %s %08X" % (keyy,ID0, endian4(offset_override))
	print(command)
	os.system(command)
	
def error_print():
	print("\nCommand line error")
	print("Usage:")
	print("python %s cpu|gpu|id0|mii old|mii new [# cpu processes] [ID0 hash] [year 3ds built]" % (sys.argv[0]))
	print("Examples:")
	print("python %s cpu 4" % (sys.argv[0]))
	print("python %s gpu" % (sys.argv[0]))
	print("python %s id0 abcdef012345EXAMPLEdef0123456789" % (sys.argv[0]))
	print("python %s mii new 2017" % (sys.argv[0]))
	print("python %s mii old 2011" % (sys.argv[0]))
	print("python %s mii old" % (sys.argv[0]))
#---------------------------------------------------------------------------
#command handler
#---------------------------------------------------------------------------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if(sys.version_info[0] != 2):
	print("For the highest levels of customer safety and satisfaction, please use Python 2")
	sys.exit(0)
if(len(sys.argv) < 2 or len(sys.argv) > 4):
	error_print()
	sys.exit(0)
	
if(sys.argv[1].lower() == "gpu"):
	print("GPU selected")
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
	sys.exit(0)
else:
	error_print()
	sys.exit(0)