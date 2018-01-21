import os,sys,struct

f=open("lfcs.dat","rb")
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

f=open("lfcs_new.dat","rb")
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
f=open("movable_part1.sed","rb")
seed=f.read()
f.close()
if len(seed) != 0x1000:
	print("Error: movable_part1.sed is not 4KB")
	exit()
	
if seed[4]=="\x02":
	print("New3DS")
	isNew=True
elif seed[4]=="\x00":
	print("Old3DS")
	isNew=False
else:
	print("Error: can't read u8 msed[4]")
	exit()

	
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
			