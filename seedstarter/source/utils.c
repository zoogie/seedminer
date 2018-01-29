#include "utils.h"

bool isN3DS(void)
{
	bool isNew3DS = false;
	
	if (R_SUCCEEDED(APT_CheckNew3DS(&isNew3DS)))
		return isNew3DS;
	
	return false;
}

void u16_to_u8(char * buf, u16 * input, size_t bufsize)
{
	u32 end=0;
	if(bufsize>0x14)bufsize=0x14;
	if(bufsize<=0) return;
	for(int i=0;i<bufsize/2;i++){
		*(buf+i)=*(input+i) & 0xFF;
		if((*buf+i)<0x20) *(buf+i)=35; //# if unprintable
		if(*(buf+i)==0)end=1;
		if(end)*(buf+i)=0x20; //space instead of null to keep formatting pretty
	}

}

u16 touchGetX(void)
{
	touchPosition pos;
	hidTouchRead(&pos);
	
	return pos.px;
}

u16 touchGetY(void)
{
	touchPosition pos;
	hidTouchRead(&pos);
	
	return pos.py;
}