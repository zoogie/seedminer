#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "frd.h"
#include "utils.h"
#include "fs.h"

extern u32 keyy[4];
u32 rnd;

static Handle amHandle;

Result amGetServiceHandle(void)
{
	return srvGetServiceHandle(&amHandle, "am:net");
}

Result amCloseServiceHandle(void)
{
	return svcCloseHandle(amHandle);
}

Result amNetGetDeviceCert(u8 const * buffer) //from https://github.com/joel16/3DSident
{
	Result ret = 0;
	u32 *cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x818, 1, 2); // 0x08180042
	cmdbuf[1] = 0x180;
	cmdbuf[2] = (0x180 << 4) | 0xC;
	cmdbuf[3] = (u32)buffer;

	if(R_FAILED(ret = svcSendSyncRequest(amHandle))) 
		return ret;

	return (Result)cmdbuf[1];
}

Result dumpFriend(u64 lfcs_share, u64 lfcs_msed, int num){
	Result res;
	char filename[0x100]={0};
	u8 part1[0x1000]={0};
	memcpy(part1, &lfcs_msed, 5);
	snprintf(filename, 0xFF,"/seedstarter/LFCS/%d_%04llu-%04llu-%04llu_part1.sed", num, lfcs_share/100000000LL, (lfcs_share/10000)%10000, lfcs_share%10000);
	FILE *g=fopen(filename,"wb");
	res = fwrite(part1, 1, 0x1000, g);
	fclose(g);
	return res;
}

int strlen16(u16* strarg)
{
   if(!strarg)
     return -1; //strarg is NULL pointer
   u16* str = strarg;
   for(;*str;++str)
     ; // empty body
   return str-strarg;
}

void data_dump()
{
	Result ret=0;
	ret = cfguInit();
	printf("cfgu %08X\n",(int)ret);
	if(R_FAILED(ret))
	{
		printf("\ncfguInit failed: 0x%08x\n", (unsigned int)ret);
		return;
	}

	Handle dirHandle;
	FS_Archive sdmcArchive;
	FS_DirectoryEntry entries[8];
	u32 entriesRead=0;
	char hash[0x21]={0};
	int validHash=0;
	u64 lfcs=0;
	u64 lfcs2=0;
	u64 lfcs3=0;
		
		
	ret = CFGU_GetConfigInfoBlk2(8, 0x00090001, (u8*)&lfcs);
	ret = CFGU_GetConfigInfoBlk2(8, 0x00090000, (u8*)&lfcs2); //debugging possible issues with false lfcs's. both lfcs and lfcs2 should be the same.
	printf("cfgu_getblk2: %08X\n",(int)ret);
	if(ret){
		printf("GetConfigInfoBlk2 failed! Exiting...\n");
		return;
	}
	ret = CFGI_GetLocalFriendCodeSeed(&lfcs3);
	u8 filebuffer[0x1000]={0};
	printf("LFCS  %016llX\n",lfcs);
	printf("LFCS2 %016llX\n",lfcs2);
	lfcs  &= 0xFFFFFFFFFFLL; //low 5 bytes of lfcs, which should be the same as movable.sed lfcs
	lfcs2 &= 0xFFFFFFFFFFLL; //ditto
	if(!ret){
		printf("LFCS3 %016llX\n",lfcs3);
		if(lfcs != lfcs2 || lfcs2 != lfcs3 || lfcs != lfcs3) printf("WARNING: lfcs's not equal, please report\n\n");
		lfcs=lfcs3; //lfcs3 is from a much more trusted function than the config savegame derived lfcs's.
	}
	else{
		printf("LFCS3 not available - need cfg:i\n");
		if(lfcs != lfcs2) printf("WARNING: lfcs's not equal, please report\n\n");
	}
	
	
	memcpy(filebuffer, &lfcs, 8);
	int c;
	
	ret = FSUSER_OpenArchive(&sdmcArchive, ARCHIVE_SDMC, (FS_Path){ PATH_EMPTY, 1, (u8*)"" });
	printf("openArchive %08X\n",(int)ret);
	ret = FSUSER_OpenDirectory(&dirHandle, sdmcArchive,(FS_Path){PATH_ASCII, 14, (u8*)"/Nintendo 3DS"});
	printf("openDir     %08X\n",(int)ret);
	ret = FSDIR_Read(dirHandle, &entriesRead, 8, entries);
	
	if(ret==0){
		for(int j=0;j<entriesRead;j++){
			if(strlen16(entries[j].name)==32){
				for(int i=0;i<32;i++){
					c=*(entries[j].name+i) & 0xFF; 
					if(c<0x67&&c>0x60)c-=0x20;
					if( (c>0x47||c<0x40) && (c<0x29||c>0x3A) ) goto nothex;
				}
				validHash++;  
				for(int i=0;i<32;i++){
					hash[i]=*(entries[j].name+i) & 0xFF;
				}
			}
			printf("%d ",strlen16(entries[j].name));
			nothex:;
		}
		printf("\nID0   %s\n",hash);
	}
	memcpy(&filebuffer[0x10], hash, 0x20);

	if(validHash==1){
		FILE *f=fopen("/seedstarter/movable_part1.sed","wb");
		fwrite(filebuffer, 1, 0x1000, f);
		fclose(f);
		printf("\nSuccess! movable_part1.sed dumped\n");
	}
	else{
		printf("\nERROR!!\nIncorrect number of hash dirs found! (%d)\nMake sure there is *only* one!\n", validHash);
	}

}

Result friends_dump(){
	
	Result res;
	u8 lfcs[8];

	res = frdInit();
	printf("frd:u %08X\n",(int)res);
	
	if(res) {
		printf("ERROR: frd:u could not be initialized\n");
		printf("to get this service, app-takeover may be required\n\n");
		return 1;
	}
	
	size_t friendCount = 0;
	FriendKey friendKey[FRIEND_LIST_SIZE];
	FRD_GetFriendKeyList(friendKey, &friendCount, 0, FRIEND_LIST_SIZE);
	
	MiiStoreData friendMii[FRIEND_LIST_SIZE];
	FRD_GetFriendMii(friendMii, friendKey, friendCount); 
	char friendNames[FRIEND_LIST_SIZE][0x14];
	memset(friendNames, 0, FRIEND_LIST_SIZE*0x14);
	
	//FILE *g=fopen("friends.bin","wb");
	//fwrite(friendMii, 1, sizeof(friendMii[0])*friendCount, g);
	//fclose(g);
	
	u64 friendCodes[FRIEND_LIST_SIZE];
	for (size_t i = 0x0; i < friendCount; i++) 
	{
		FRD_PrincipalIdToFriendCode(friendKey[i].principalId, &friendCodes[i]);
		u16_to_u8(&friendNames[i][0x0], &friendMii[i].name[0], 0x14);
		//memcpy(&friendNames[i][0x0], &friendMii[i].name[0], 0x14);
	}
	
	FILE *f=fopen("/seedstarter/LFCS/friends.txt","w");
	fprintf(f,"\tName       : Friend Code    LFCS(BE)         : LFCS(LE)\n"); 
	fprintf(f,"-----------------------------------------------------------------\n");
	for (size_t i = 0x0; i < friendCount; i++)
	{
		memcpy(lfcs, &friendKey[i].localFriendCode, 8);
		fprintf(f,"%d.\t%s : %04llu-%04llu-%04llu %016llX : ", i, &friendNames[i][0], friendCodes[i]/100000000LL, (friendCodes[i]/10000)%10000, friendCodes[i]%10000, friendKey[i].localFriendCode);
		for(int i=0;i<5;i++){
			fprintf(f,"%02X ",lfcs[i]);
		}
		fprintf(f,"\n");
		res = dumpFriend(friendCodes[i], friendKey[i].localFriendCode&0xFFFFFFFFFFLL, i);
		if(res) printf("Friend %d dumped to /seedstarter/LFCS/\n", i);
		else    printf("Friend %d file dump error\n", i);
	}
	fclose(f);
	
	printf("\n%d friends dumped to sdmc:/seedstarter/LFCS\n",friendCount);
	return 0;
}

Result msed_data(){
	Result res;
	
	struct msed_data{
		u32 lfcs_blk;
		s32 msed3offset;
		u32 seedtype;
	} mdata;
	
	//nand to sd copy function from the following. 
	//https://github.com/joel16/3DS-Recovery-Tool Thanks to Joel16 for it.
	res = copy_file( "/private/movable.sed", "/seedstarter/movable.sed");
	
	if(res){ 
		printf("Movable.sed dump failed.\n");
		printf("no cfw or luma3DS 9.0+ possible reasons\n\n");
	}
	else{
		char filename[0x100]={0};
		u32 lfcs=*keyy;
		u32 lfcs_blk=lfcs >> 12;
		u32 msed3=*(keyy+3);
		s32 msed3offset=(lfcs/5)-(msed3&0x7FFFFFFF);
		u32 seedtype=(msed3&0x80000000)>>31;
		printf("Movable.sed (keyy only) dump to sdmc:/ success!\nDon't inject to a real 3DS - TADpole use only!\n\n");
		printf("  LFCS  exact  %08lX\n", lfcs);
		printf("* LFCS  block  %08lX\n", lfcs_blk);
		printf("  Msed3 exact  %08lX\n", msed3);
		printf("* Msed3 offset %ld\n", msed3offset);
		printf("* Seedtype     %ld\n", seedtype);
		mdata.lfcs_blk=lfcs_blk;
		mdata.msed3offset=msed3offset;
		mdata.seedtype=seedtype;
		snprintf(filename, 0x100, "/seedstarter/msed_data_%08lX.bin", rnd);
		printf("\n* will be written to\nsdmc:%s\n\n",filename);
		FILE *f=fopen(filename,"wb");
		fwrite(&mdata, 1, sizeof(mdata), f);
		fclose(f);
		printf("Done.\n");
	}
	return res;
}

Result ctcert_dump(){
	Result res;
	u8 ctcert[0x19E]={0};
	
	res = amGetServiceHandle();
	printf("am:net %08X\n",(int)res);
	
	if(res){
		printf("ERROR: am:net failed\n");
		printf("no cfw or luma3DS 9.0+ possible reasons\n\n");
		return 1;
	}
	
	res = amNetGetDeviceCert(ctcert); //thanks joel16 for this
	printf("getcert %08X\n",(int)res);
	memcpy(ctcert+0x180, "ctcert privkey  goes here", 25);
	
	FILE *f=fopen("/seedstarter/ctcert.bin","wb");
	fwrite(ctcert, 1, 0x19E, f);
	fclose(f);
	printf("Remember to run ctcertifier.firm to add privkey!\n");
	printf("Done.\n");
	return res;
}

void showMenu(){
	consoleClear();
	printf("<< seedstarter - zoogie >> v1.1\n\n");
	printf("Based on friendMii, 3DSident, and\n");
	printf("3DS-Recovery-Tool by Joel16\n");
	printf("Please run with Luma3DS 9.0+ if possible\n\n");
	
	printf("    A dump LFCS from GetConfigInfoBlk2\n");
	printf("    B dump LFCS from friendlist\n");
	printf("CFW-X dump msed_data.bin\n");
	printf("CFW-Y dump ctcert.bin (no privkey)\n");
	printf("START exit app\n\n");
}

void waitKey(){
	printf("Press A to continue...\n");
	
	while (1)
	{
		hidScanInput();
		u32 kDown = hidKeysDown();
		if (kDown & KEY_A) break; 
		gfxFlushBuffers();
		gfxSwapBuffers();
		gspWaitForVBlank();
	}
	showMenu();
}

int main(int argc, char **argv) 
{
	gfxInitDefault();
	consoleInit(GFX_TOP, NULL);
	srand(time(NULL));
    rnd=rand();
	
	showMenu();
	mkdir("sdmc:/seedstarter/", 0777);
	mkdir("sdmc:/seedstarter/LFCS/", 0777);
	
	while (aptMainLoop()) 
	{
		hidScanInput();
		u32 kDown = hidKeysDown();
		//u32 kHeld = hidKeysHeld();
		
		if (kDown & KEY_START)
			break;
	    else if (kDown & KEY_A){
			data_dump();
			waitKey();
		}
		else if (kDown & KEY_B){
			friends_dump();
			waitKey();
		}
		else if (kDown & KEY_X){
			msed_data();
			waitKey();
		}
		else if (kDown & KEY_Y){
			ctcert_dump();
			waitKey();
		}
		gfxFlushBuffers();
		gfxSwapBuffers();
		gspWaitForVBlank();
	}

	gfxExit();
	return 0;
}