from __future__ import print_function
import os,sys,struct,glob

#don't change this mid brute force - can be different amount multiple computers - powers of two recommended for even distribution of workload 1 2 4 8 etc.
process_count=4
#-----------------------------------------------------------------------------------------------------------------
#Don't edit below this line unless you have multiple computers brute-forcing - most of you won't need this feature
#-----------------------------------------------------------------------------------------------------------------
number_of_computers=1       #each computer needs this set to same number if more than one
which_computer_is_this=0    #each computer has a different id # that's less than number_of_computers
'''                        
example for 3 computers
<computer 0>
number_of_computers=3    
which_computer_is_this=0   

<computer 1>
number_of_computers=3    
which_computer_is_this=1 

<computer 2>
number_of_computers=3    
which_computer_is_this=2
'''
#---------------------------------------------------------------------------
#Don't edit below this line unless you know what you're doing (stage2 begin)
#---------------------------------------------------------------------------
if(len(sys.argv) < 2 or len(sys.argv) > 3):
	print("\nCommand line error:")
	print("Usage: python %s cpu|gpu|id0 [# cpu processes] [ID0 hash]" % (sys.argv[0]))
	print("Ex: python %s cpu 4" % (sys.argv[0]))
	print("Ex: python %s gpu" % (sys.argv[0]))
	print("Ex: python %s id0 abcdef0123456789abcdef0123456789" % (sys.argv[0]))
	sys.exit(0)

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

if(sys.argv[1].lower()=="id0"):
	hash_clusterer()
	sys.exit(0)

f=open("saves/lfcs.dat","rb")
buf=f.read()
f.close()

lfcs_len=len(buf)/8
lfcs=[]
ftune=[]
err_correct=0


for i in range(lfcs_len):
	lfcs.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

for i in range(lfcs_len):
	ftune.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])

f=open("saves/lfcs_new.dat","rb")
buf=f.read()
f.close()

lfcs_new_len=len(buf)/8
lfcs_new=[]
ftune_new=[]

for i in range(lfcs_new_len):
	lfcs_new.append(struct.unpack("<i",buf[i*8:i*8+4])[0])

for i in range(lfcs_new_len):
	ftune_new.append(struct.unpack("<i",buf[i*8+4:i*8+8])[0])
#exit()

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
if len(seed) != 0x1000:
	print("Error: movable_part1.sed is not 4KB")
	sys.exit(0)
	
if seed[4]=="\x02":
	print("New3DS")
	isNew=True
elif seed[4]=="\x00":
	print("Old3DS")
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

#---------------------------------------------------------------------------
#stage3 launcher (stage2 end)
#---------------------------------------------------------------------------
if(len(sys.argv)==3):
	process_count=int(sys.argv[2])
	
if(sys.argv[1].lower() == "gpu"):
	print("GPU selected")
	f=open("movable_part2.sed","rb")
	buf=f.read()
	f.close()
	keyy=buf[:16].encode('hex')
	ID0=buf[16:32].encode('hex')
	command="bfcl msky %s %s" % (keyy,ID0)
	print(command)
	os.system(command)
	sys.exit(0)
elif(sys.argv[1].lower()=="cpu"):
	print("CPU selected")
	pass
else:
	print("\nCommand line error:")
	print("Usage: python %s cpu|gpu|id0 [# cpu processes] [ID0 hash]" % (sys.argv[0]))
	print("Ex: python %s cpu 4" % (sys.argv[0]))
	print("Ex: python %s gpu" % (sys.argv[0]))
	print("Ex: python %s id0 abcdef0123456789abcdef0123456789" % (sys.argv[0]))
	sys.exit(0)

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
	
	