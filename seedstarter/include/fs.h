#ifndef FS_H
#define FS_H

#include <3ds.h>

FS_Archive fsArchive, ctrArchive;

void openArchive(FS_ArchiveID id);
void closeArchive(FS_ArchiveID id);
Result makeDir(FS_Archive archive, const char * path);
bool fileExists(FS_Archive archive, const char * path);
bool fileExistsNand(const char * path);
bool dirExists(FS_Archive archive, const char * path);
Result writeFile(const char * path, void * buf);
Result copy_file(char * old_path, char * new_path);


#endif