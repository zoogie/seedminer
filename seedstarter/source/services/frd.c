#include <string.h>
#include <wchar.h>

#include "frd.h"

static Handle frdHandle;
static int frdRefCount;

Result frdInit(void)
{
	Result ret = 0;

	if (AtomicPostIncrement(&frdRefCount)) 
		return 0;

	ret = srvGetServiceHandle(&frdHandle, "frd:u");
	
	if (R_FAILED(ret)) 
		ret = srvGetServiceHandle(&frdHandle, "frd:n");
	
	if (R_FAILED(ret)) 
		ret = srvGetServiceHandle(&frdHandle, "frd:a");
	
	if (R_FAILED(ret)) 
		AtomicDecrement(&frdRefCount);

	return ret;
}

void frdExit(void)
{
	if (AtomicDecrement(&frdRefCount)) 
		return;
	
	svcCloseHandle(frdHandle);
}

Result FRDU_IsOnline(bool * state) // Online state
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x02, 0, 0); // 0x00020000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*state = cmdbuf[2] & 0xFF;
	
	return cmdbuf[1];
}

Result FRDU_HasLoggedIn(bool * state)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x01, 0, 0); // 0x00010000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*state = cmdbuf[2] & 0xFF;
	
	return cmdbuf[1];
}

Result FRD_Login(Handle event)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x03, 0, 2); // 0x00030002
	cmdbuf[1] = 0;
	cmdbuf[2] = event;
    
	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_Logout(void)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x04, 0, 0); // 0x00040000
    
	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_GetMyFriendKey(FriendKey * key)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x05, 0, 0); // 0x00050000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	memcpy(key, &cmdbuf[2], sizeof(FriendKey));
	
	return cmdbuf[1];
}

Result FRD_GetMyPreference(bool * isPublicMode, bool * isShowGameName, bool * isShowPlayedGame)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x06, 0, 0); // 0x00060000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*isPublicMode = cmdbuf[2] & 0xFF; // Public mode 
	*isShowGameName = cmdbuf[3] & 0xFF; // Show current game 
	*isShowPlayedGame = cmdbuf[4] & 0xFF; // Show game history.
	
	return cmdbuf[1];
}

Result FRD_GetMyProfile(Profile * profile)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x07, 0, 0); // 0x00070000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	memcpy(profile, &cmdbuf[2], sizeof(Profile));
	
	return cmdbuf[1];
}

Result FRD_GetMyPresence(MyPresence * myPresence)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();
	u32 * statbuf = getThreadStaticBuffers();

	cmdbuf[0] = IPC_MakeHeader(0x08, 0, 0); // 0x00080000
	statbuf[0] = 0x4B0002;
	statbuf[1] = (u32)myPresence;
  
	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_GetMyScreenName(u16 * name)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x09, 0, 0); // 0x00090000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;
	
	memcpy(name, &cmdbuf[2], FRIENDS_SCREEN_NAME_SIZE); // 11-byte UTF-16 screen name (with null terminator)
	
	return cmdbuf[1];
}

Result FRD_GetMyMii(MiiStoreData * mii)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x0A, 0, 0); // 0x000A0000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	memcpy(mii, &cmdbuf[2], FRIEND_MII_STORE_DATA_SIZE);
	
	return cmdbuf[1];
}

Result FRD_GetMyComment(u16 * comment)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x0F, 0, 0); // 0x000F0000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;
	
	memcpy(comment, &cmdbuf[2], FRIENDS_COMMENT_SIZE); // 16-byte UTF-16 comment
	
	return cmdbuf[1];
}

Result FRD_GetMyPlayingGame(u64 * titleId)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x0C, 0, 0); // 0x000C0000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*titleId = (((u64)cmdbuf[3]) << 32 | (u64)cmdbuf[2]);
	
	return cmdbuf[1];
}

Result FRD_GetMyFavoriteGame(u64 * titleId)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x0D, 0, 0); // 0x000D0000

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*titleId = (((u64)cmdbuf[3]) << 32 | (u64)cmdbuf[2]);
	
	return cmdbuf[1];
}

Result FRD_IsFromFriendList(u64 friendCode, bool * isFromList)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x1B, 2, 0); // 0x001B0080
	cmdbuf[1] = (u32)(friendCode & 0xFFFFFFFF);
	cmdbuf[2] = (u32)(friendCode >> 32);

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*isFromList = cmdbuf[2] & 0xFF;
	
	return cmdbuf[1];
}

Result FRD_UpdateGameModeDescription(const wchar_t * desc)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x1D, 0, 2); // 0x001D0002
	cmdbuf[1] = 0x400802;
	cmdbuf[2] = (uintptr_t)desc;
    
	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_PrincipalIdToFriendCode(u32 principalId, u64 * friendCode)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x24, 1, 0); // 0x00240040
	cmdbuf[1] = principalId;

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*friendCode = (((u64)cmdbuf[3]) << 32 | (u64)cmdbuf[2]);
	
	return cmdbuf[1];
}

Result FRD_FriendCodeToPrincipalId(u64 friendCode, u32 * principalId)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x25, 2, 0); // 0x00250080
	cmdbuf[1] = (u32)(friendCode & 0xFFFFFFFF);
	cmdbuf[2] = (u32)(friendCode >> 32);

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*principalId = cmdbuf[2];
	
	return cmdbuf[1];
}

Result FRD_GetFriendKeyList(FriendKey * friendKeyList, size_t * num, size_t offset, size_t size)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x11, 2, 0); // 0x00110080
	cmdbuf[1] = 0;
	cmdbuf[2] = size;
	cmdbuf[64] = (size << 18) | 2;
	cmdbuf[65] = (u32)friendKeyList;

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*num = cmdbuf[2];
	
	return cmdbuf[1];
}

Result FRD_GetFriendMii(MiiStoreData * miiDataList, const FriendKey * friendKeyList, size_t size)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x14, 1, 4); // 0x00140044
	cmdbuf[1] = size;
	cmdbuf[2] = (size << 18) | 2;
	cmdbuf[3] = (u32)friendKeyList;
	cmdbuf[4] = IPC_Desc_Buffer((size * 0x60), IPC_BUFFER_W);
	cmdbuf[5] = (u32)miiDataList;

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_GetFriendProfile(Profile * profileList, const FriendKey * friendKeyList, size_t size)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();
	u32 profileSize = size * sizeof(Profile);

	cmdbuf[0] = IPC_MakeHeader(0x15, 1, 2); // 0x00150042
	cmdbuf[1] = size;
	cmdbuf[2] = (size << 18) | 2;
	cmdbuf[3] = (u32)friendKeyList;
	cmdbuf[64] = (profileSize << 10) | 2;
	cmdbuf[65] = (u32)profileList;

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_GetFriendPlayingGame(u64 * titleid, const FriendKey * friendKeyList, size_t size)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x18, 1, 4); // 0x00180044
	cmdbuf[1] = 0;
	cmdbuf[2] = (size << 18) | 2;
	cmdbuf[3] = (u32)friendKeyList;
	cmdbuf[4] = (4352 * size) | 0xC;
	cmdbuf[5] = (u32)titleid;

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}

Result FRD_IsValidFriendCode(u64 friendCode, bool * isValid)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x26, 2, 0); // 0x00260080
	cmdbuf[1] = (u32)(friendCode & 0xFFFFFFFF);
	cmdbuf[2] = (u32)(friendCode >> 32);

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	*isValid = cmdbuf[2] & 0xFF;
	
	return cmdbuf[1];
}

Result FRD_SetClientSdkVersion(u32 sdkVer)
{
	Result ret = 0;
	u32 * cmdbuf = getThreadCommandBuffer();

	cmdbuf[0] = IPC_MakeHeader(0x32, 1, 2); // 0x00320042
	cmdbuf[1] = sdkVer;
	cmdbuf[2] = IPC_Desc_CurProcessHandle();

	if (R_FAILED(ret = svcSendSyncRequest(frdHandle)))
		return ret;

	return cmdbuf[1];
}