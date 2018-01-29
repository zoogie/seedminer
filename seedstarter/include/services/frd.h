#ifndef FRD_H
#define FRD_H

#include <3ds.h>

#define SDK(a, b, c, d) ((a<<24) | (b<<16) | (c<<8) | d)

#define FRIENDS_SCREEN_NAME_SIZE 0x16 // 11 (0x16 because UTF-16)
#define FRIENDS_COMMENT_SIZE 0x22 // 16 (0x21 because UTF-16 + null character)
#define FRIEND_LIST_SIZE 0x64 // 100
#define FRIEND_MII_STORE_DATA_SIZE 0x60 // 96

typedef struct
{
	u32 principalId;
	u64 localFriendCode;
} FriendKey;

typedef struct
{
   u32 joinAvailabilityFlag;
   u32 matchmakeSystemType;
   u32 joinGameId;
   u32 joinGameMode;
   u32 ownerPrincipalId;
   u32 joinGroupId;
   u8 applicationArg[0x14];
} GameMode;

typedef struct
{
   GameMode gameMode;
   wchar_t modeDescription[0x80];
} MyPresence;

/*
	The following Mii data struct is from SpecializeMii.
*/
typedef enum MII_SPECIALNESS_t 
{
    MII_SPECIAL    = 0,
    MII_NONSPECIAL = 1,
} MII_SPECIALNESS;

typedef enum MII_COPYABLE_t 
{
    MII_COPYABLE_OFF = 0,
    MII_COPYABLE_ON  = 1,
} MII_COPYABLE;

typedef enum MII_SHAREABLE_t 
{
    MII_SHAREABLE_ON  = 0,
    MII_SHAREABLE_OFF = 1,
} MII_SHAREABLE;

/* Fuck yeah! Bitfields and compiler dependent struct padding!
 *
 * This is absolutely *NOT* portable in any way, shape or form.
 * */

typedef union MiiPosition_t 
{
    u8 raw;
    struct 
	{
        u8 page : 4;
        u8 slot : 4;
    };
} MiiPosition;

typedef union MiiEyebrow_t 
{
	u32 raw;
    struct 
	{
        u32 rotation : 4;
        u32 _unk_bit_4 : 1;
        u32 xspacing : 4;
        u32 ypos : 5;
        u32 _unk_bit_14_15 : 2;
        u32 style : 5;
        u32 color : 3;
        u32 xscale : 4;
        u32 yscale : 4;
    };
} MiiEyebrow;
/*
typedef struct
{
    u16 pad1[0x45];
    u16 name[0xA];
	u16 pad2[0x31];
	u16 pad3[0x100];
} MiiStoreData;
*/

typedef struct
{
    union 
	{
        struct 
		{
            u8 _unk_0x00;
            u8 copyable; // 0 = not copyable, and 1 = copyable
            MiiPosition position;
            u8 category;
        };
        u32 mii_id;
    };
    
	u32 sys_id;
    u32 _unk_0x08;

    union 
	{
        // This unsigned 32bit integer is stored in big-endian and holds the
        // date of creation in its lower 28 bit:
        //
        // seconds since 01/01/2010 00:00:00
        //   = (date_of_creation[bit 0 .. bit 27]) * 2
        u32 date_of_creation;

        // Non special Miis have bit 31 of aforementioned big-endian word set,
        // which corresponds to bit 8 in little endian, which the 3DS uses.
        struct 
		{
            u32 : 7;
            u32 specialness : 1;
            u32 : 24;
        };
    };

    u8 mac[6];
    u8 _pad_0x16[2];

    u16 gender : 1; // 0 = male, 1 = female
    u16 bday_month : 4;
    u16 bday_day : 5;
    u16 color : 4; // 0 = Red, 1 = Orange, 2 = Yellow, 3 = Lime green, 4 = Green, 5 = Blue, 6 = Neon blue, 7 = Pink, 8 = Purple, 9 = Brown, 10 = White, and 11 = Black.
    u16 favorite : 1; // 0 = No, and 1 = Yes.
    u16 _unk_0x19 : 1;

    u16 name[0xA];

    u8 width;
    u8 height;

    u8 disable_sharing : 1; // 0 = Sharing enabled, and 1 = Sharing disabled.
    u8 face_shape : 4;
    u8 skin_color : 3;

    u8 wrinkles : 4;
    u8 makeup : 4;

    u8 hair_style;
    u8 hair_color : 3;
    u8 hair_flip : 1;
    
	u8 _unk_0x33 : 4;
    u32 _unk_0x34;

    MiiEyebrow eyebrow;

    u8 _unk_0x3c[12];

    u16 author[0xA];
	u8 pad3[4];

} MiiStoreData;

typedef struct
{
    u8 region;      // The region code for the hardware region.
    u8 country;     // Country code.
    u8 area;        // Area code.
    u8 language;    // Language code.
    u8 platform;    // Platform code.
} Profile;

Result frdInit(void);
void frdExit(void);
Result FRDU_IsOnline(bool * state);
Result FRDU_HasLoggedIn(bool * state);
Result FRD_Login(Handle event);
Result FRD_Logout(void);
Result FRD_GetMyFriendKey(FriendKey * key);
Result FRD_GetMyPreference(bool * isPublicMode, bool * isShowGameName, bool * isShowPlayedGame);
Result FRD_GetMyProfile(Profile * profile);
Result FRD_GetMyPresence(MyPresence * myPresence);
Result FRD_GetMyScreenName(u16 * name);
Result FRD_GetMyMii(MiiStoreData * mii);
Result FRD_GetMyComment(u16 * comment);
Result FRD_GetMyPlayingGame(u64 * titleId);
Result FRD_GetMyFavoriteGame(u64 * titleId);
Result FRD_IsFromFriendList(u64 friendCode, bool * isFromList);
Result FRD_UpdateGameModeDescription(const wchar_t * desc);
Result FRD_PrincipalIdToFriendCode(u32 principalId, u64 * friendCode);
Result FRD_FriendCodeToPrincipalId(u64 friendCode, u32 * principalId);
Result FRD_GetFriendKeyList(FriendKey * friendKeyList, size_t * num, size_t offset, size_t size);
Result FRD_GetFriendMii(MiiStoreData * miiDataList, const FriendKey * friendKeyList, size_t size);
Result FRD_GetFriendProfile(Profile * profileList, const FriendKey * friendKeyList, size_t size);
Result FRD_GetFriendPlayingGame(u64 * titleid, const FriendKey * friendKeyList, size_t size);
Result FRD_IsValidFriendCode(u64 friendCode, bool * isValid);
Result FRD_SetClientSdkVersion(u32 sdkVer);

#endif