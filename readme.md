seedminer (beta v0.1) - zoogie

1. Buy a DSiWare Transfer compatible dsiware game and download it (if you don't already have one). EA Sudoku is a great choice, for example.
2. Run stage1.3dsx on your 3ds. Make sure there aren't more than 1 sdmc:/Nintendo 3DS/20eaa90314ec7859... etc.
   directories there! Move the one(s) that aren't currently being used by the 3ds. You also need wifi on when you run this, similar to udsploit.
   You don't have to be connected to an access point -- the app does not contact any servers.
3. It should dump movable_part1.sed. Take this file and put it in the stage2 folder.
4. Run stage2.py (or stage3.exe) and it should generate movable_part2.sed.
5. Place that file in the stage3/CPU_Conventional/ folder.
6. Run the python script stage3_launcher.py (or exe, but that's hardcoded to 4 threads!). You can edit the number of CPU processes to use first
   (if the .py version) 4 is good for 2x cores and 8 for 4x cores, etc. Don't change # of computers unless you know what you are doing 
   (experimental feature).
   Note: There will be multiple windows opened when stage3 is executed. Don't close them, each one is brute-forcing a specific area and closing 
   even one could ruin your chance of getting the movable.sed.
7. Wait until the stage3.exe process windows close and movable.sed is dumped. This could take 0-2 days on average but
   should get better as seedminer matures. Progress is saved if you have to quit. Changing the # of processes mid-brute force
   will mess up the saves and probably everything else.
8. Now that you have your precious movable.sed (never lose it!), follow the directions at https://github.com/zoogie/TADpole for
   dumping/editing/rebuilding a dsiware export (TAD).
9. Place the resulting <dsiware>_patched.bin in your sdmc:/Nintendo 3DS/ID0/ID1/Nintendo Dsiware/(here) minus the "_patched"
10.Import it, and you should have dsiwarehax execution. Check 3ds.guide and follow the rest of the DSiware Transfer method.

Note: if you have a choice whether to run the stage.py or .exe, choose the script. Same with stage3_launcher.
