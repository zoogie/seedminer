#include <stdlib.h>
#include <string.h>
#include <3ds.h>

u32 keyy[4]={0};

#include "fs.h"

void openArchive(FS_ArchiveID id)
{
	FSUSER_OpenArchive(&fsArchive, id, fsMakePath(PATH_EMPTY, ""));
}

void closeArchive(FS_ArchiveID id)
{
	FSUSER_CloseArchive(fsArchive);
}

Result makeDir(FS_Archive archive, const char * path)
{
	if ((!archive) || (!path))
		return -1;
	
	return FSUSER_CreateDirectory(archive, fsMakePath(PATH_ASCII, path), 0);
}

bool fileExists(FS_Archive archive, const char * path)
{
	if ((!path) || (!archive))
		return false;
	
	Handle handle;

	Result ret = FSUSER_OpenFile(&handle, archive, fsMakePath(PATH_ASCII, path), FS_OPEN_READ, 0);
	
	if (R_FAILED(ret))
		return false;

	ret = FSFILE_Close(handle);
	
	if (R_FAILED(ret))
		return false;
	
	return true;
}

bool fileExistsNand(const char * path)
{
	if (!path)
		return false;
	
	Handle handle;

	openArchive(ARCHIVE_NAND_CTR_FS);
	Result ret = FSUSER_OpenFileDirectly(&handle, ARCHIVE_NAND_CTR_FS, fsMakePath(PATH_EMPTY, ""), fsMakePath(PATH_ASCII, path), FS_OPEN_READ, 0);
	
	if (R_FAILED(ret))
	{
		closeArchive(ARCHIVE_NAND_CTR_FS);
		return false;
	}

	ret = FSFILE_Close(handle);
	
	if (R_FAILED(ret))
	{
		closeArchive(ARCHIVE_NAND_CTR_FS);
		return false;
	}
	
	closeArchive(ARCHIVE_NAND_CTR_FS);
	return true;
}

bool dirExists(FS_Archive archive, const char * path)
{	
	if ((!path) || (!archive))
		return false;
	
	Handle handle;

	Result ret = FSUSER_OpenDirectory(&handle, archive, fsMakePath(PATH_ASCII, path));
	
	if (R_FAILED(ret))
		return false;

	ret = FSDIR_Close(handle);
	
	if (R_FAILED(ret))
		return false;
	
	return true;
}

u64 getFileSize(FS_Archive archive, const char * path)
{
	u64 st_size;
	Handle handle;

	FSUSER_OpenFile(&handle, archive, fsMakePath(PATH_ASCII, path), FS_OPEN_READ, 0);
	FSFILE_GetSize(handle, &st_size);
	FSFILE_Close(handle);
	
	return st_size;
}

Result writeFile(const char * path, void * buf)
{
	Handle handle;
	u32 len = strlen(buf);
	u64 size;
	u32 written;
	
	if (fileExists(fsArchive, path))
		FSUSER_DeleteFile(fsArchive, fsMakePath(PATH_ASCII, path));
	
	Result ret = FSUSER_OpenFileDirectly(&handle, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, ""), fsMakePath(PATH_ASCII, path), (FS_OPEN_WRITE | FS_OPEN_CREATE), 0);
	ret = FSFILE_GetSize(handle, &size);
	ret = FSFILE_SetSize(handle, size + len);
	ret = FSFILE_Write(handle, &written, size, buf, len, FS_WRITE_FLUSH);
	ret = FSFILE_Close(handle);
	
	return R_SUCCEEDED(ret)? 0 : -1;
}

Result copy_file(char * old_path, char * new_path)
{
	int chunksize = (512 * 1024);
	char * buffer = (char *)malloc(chunksize);

	u32 bytesWritten = 0, bytesRead = 0;
	u64 offset = 0;
	Result ret = 0;
	
	Handle inputHandle, outputHandle;

	openArchive(ARCHIVE_NAND_CTR_FS);
	Result in = FSUSER_OpenFileDirectly(&inputHandle, ARCHIVE_NAND_CTR_FS, fsMakePath(PATH_EMPTY, ""), fsMakePath(PATH_ASCII, old_path), FS_OPEN_READ, 0);
	
	u64 size = getFileSize(fsArchive, old_path);

	if (R_SUCCEEDED(in))
	{
		// Delete output file (if existing)
		FSUSER_DeleteFile(fsArchive, fsMakePath(PATH_ASCII, new_path));

		Result out = FSUSER_OpenFileDirectly(&outputHandle, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, ""), fsMakePath(PATH_ASCII, new_path), (FS_OPEN_CREATE | FS_OPEN_WRITE), 0);
		
		if (R_SUCCEEDED(out))
		{
			// Copy loop (512KB at a time)
			do
			{
				ret = FSFILE_Read(inputHandle, &bytesRead, offset, buffer, chunksize);
				memset(buffer, 0, 0x110);
				memset(buffer+0x120, 0, 0x20);
				bytesWritten += FSFILE_Write(outputHandle, &bytesWritten, offset, buffer, size, FS_WRITE_FLUSH);
				
				if (bytesWritten == bytesRead)
					break;
			}
			while(bytesRead);

			ret = FSFILE_Close(outputHandle);
			
			if (bytesRead != bytesWritten) 
				return ret;
		}
		else 
			return out;

		FSFILE_Close(inputHandle);
		closeArchive(ARCHIVE_NAND_CTR_FS);
	}
	else 
		return in;

	memcpy(keyy, buffer+0x110, 0x10);
	free(buffer);
	return ret;
}