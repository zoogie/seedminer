import os,sys

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
#Don't edit below this line unless you know what you're doing
#---------------------------------------------------------------------------

if(which_computer_is_this >= number_of_computers):
	print("You can't assign an id # to a computer that doesn't exist")
	exit()

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
	os.system("start stage3.exe %08X %09X" % (start,size))
	print("Process: "+str(i)+" Start: "+hex(process_begin)+" Size: "+hex(size))
	
	