#include <stdint.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include "types.h"

u8 sha256[0x20]={0};
u8 ID0[0x10]={0};
u8 part2[0x20]={0};
u8 msed[0x140]={0};
u32 keyy[4]={0}; 
u32 save_offset=0;

u32 check_finish(){
	FILE *f=fopen("movable.sed","rb");
	if(!f) return 0;
	fclose(f);
	printf("Dumped movable.sed detected, closing down process...\n");
	return 1;
}

u32 save_progress(u64 start, u64 size, u32 progress){
	char savename[0x100]={0};
	snprintf(savename,0xFF,"saves/save_%08I64X-%09I64X.bin", start, size);
	FILE *f=fopen(savename,"wb+");
	if(f){
		printf("Saving progress to file %s ...\n\n", savename);
		fwrite(&progress, 1, 4, f);
		fclose(f);
	}
	else{
		printf("Error: could not open %s\n", savename);
		return 1;
	}
	return 0;
}

u32 load_progress(u64 start, u64 size){
	char savename[0x100]={0};
	snprintf(savename,0xFF,"saves/save_%08I64X-%09I64X.bin", start, size);
	FILE *f=fopen(savename,"rb");
	if(f){
		printf("Loading %s ...\n", savename);
		fread(&save_offset, 1, 4, f);
		fclose(f);
		
		s32 neg = save_offset&1 ? -1 : 1;
		s32 offset_converted = neg*((s32)save_offset+1)/2;
		printf("Resuming at msed3 offset %d\n\n", offset_converted);
	}
	else{
		printf("Error: could not open %s\n", savename);
		printf("Starting at msed3 offset 0\n\n");
		return 1;
	}
	return 0;
}

s32 bf_block(u32 offset, u64 start, u64 size){ 
	//size=0x800000; 
	u64 finish=start+size;
	
	s32 neg = offset&1 ? -1 : 1;
	s32 offset_converted = neg*((s32)offset+1)/2;
	
	if(offset_converted+((s32)keyy[3]&0x7FFFFFFF) < 0) return -2; //oob check
	
	printf("At msed2 address 0x%08I64X, size 0x%09I64X:\n", start, size);
	
	u32 original=keyy[3];
	printf("Brute forcing msed3 offset %d (0x%08X)...\n", offset_converted, keyy[3]+offset_converted);
	keyy[3]+=offset_converted;
	for(u64 i=start;i<finish;i++){
		keyy[2]=i;
		SHA256(keyy, 0x10, sha256);
		if(!memcmp(sha256, ID0, 0x10))return 0;
	}
	
	keyy[3]=original;
	return -1;
}

int main(int argc, char **argv)
{
	u64 start=0;
	u64 size=0;
	int ret=1;
	
	if(argc!=3){
		printf("seedminer.exe <start_offset> <size>\nNote that all values interpreted as hex\n");
		return 1;
	}
	
	start=strtoul(argv[1], NULL, 16);
	size=strtoul(argv[2],NULL, 16);
	
	printf("Loading movable_part2.sed...\n");
	
	FILE *f;
	f = fopen("movable_part2.sed", "rb");
	if(f==NULL)return 0;
	fread(part2, 1, 0x20, f);
	fclose(f);
	
	memcpy(keyy, part2, 0x10);
	memcpy(ID0, part2+0x10, 0x10);
	
	load_progress(start, size);
	
	//keyy[3]=0x80000004;
	
	for(u32 i=save_offset;i<0x100000;i++){
		ret = bf_block(i, start, size);
		if(!ret)break;
		if(check_finish()) return 0;
		if(ret == -1) save_progress(start, size, i+1);
	}
	
	printf("\nKEYY HIT!!!\n");
	printf("Writing keyy to movable.sed...\n");
	memcpy(msed+0x110, keyy, 0x10);
	printf("Dumping movable.sed (don't inject this to real 3ds) ...\n");
	f = fopen("movable.sed", "wb");
	fwrite(msed, 1, 0x140, f);
	fclose(f);
	printf("Done!\n");

	char filename[0x100]={0};
	u32 lfcs=keyy[0];
	u32 lfcs_blk=lfcs>>12;
	s32 error=(lfcs/5)-keyy[3];
	u32 seedtype=(keyy[3]&0x80000000)>>31;
	snprintf(filename, 0x100, "msed_data_%08X.bin",lfcs_blk);
	f = fopen(filename, "wb");
	fwrite(&lfcs_blk, 1, 4, f);
	fwrite(&error, 1, 4, f);
	fwrite(&seedtype, 1, 4, f);
	fclose(f);
	printf("\n%s dumped!\nPlease share this^ and help improve seedminer for others\nYou benefited from others that shared theirs before!\nPass on the favor, please!!\n", filename);
	printf("Done!\n");
	
	getchar();

	return 0;
}