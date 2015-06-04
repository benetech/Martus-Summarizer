This is a PyInstaller project to build the executable.

I've only ever run this on windows.  It should work with very little modification on Linux.  For the Mac app, I used an alternative called py2app.

Pre-requisites:
 Python 2.6 or 2.7, must use the 32-bit version, since we want to compile a 32-bit Windows program
 wxWindows, 32-bit version for whatever version of python you're using
 pywin32 (windows extensions for python)
 PyInstaller

NB: These are prerequisites for *building* updated versions of the summarizer.  After the .exe file (or .app file on Mac) has been built, these things are all included in that .exe file, so they are *not* prerequisites for *running* the Summarizer.  Users of the summarizer need nothing but the .exe file.

The steps below assume that you have a copy of the martus-summarizer source tree copied somewhere onto a Windows machine with the above software installed.  Here, that code is on the Desktop.


0. configure PyInstaller (this step can be skipped if you've done it before, since the config is saved in c:\Program Files\pyinstaller-1.5.1):

c:\Users\jeff\Desktop\martus-summarizer\package-win>c:\Python27\python.exe "c:\Program Files\pyinstaller-1.5.1\Configure.py"


1. Create the pyinstaller spec file:

c:\Users\jeff\Desktop\martus-summarizer\package-win>c:\Python27\python.exe "c:\Program Files\pyinstaller-1.5.1\Makespec.py" --windowed --onefile --icon=martus.ico ../src/main.py

You should see a message reporting that the build specification file (main.spec) has been created.


2. Build the executable:

c:\Users\jeff\Desktop\martus-summarizer\package-win>c:\Python27\python.exe "c:\Program Files\pyinstaller-1.5.1\Build.py" main.spec

The build takes a couple mintues.  PyInstaller is putting together a python runtime, all needed python libraries, and the code for the summarizer together into a self-contained exe.  This final exe file, which can be distributed by itself, is package/dist/main.exe  All the other cruft created in the build/ and dist/ directories can now be safely deleted.

3. Package it up. 
Run these commands (back in POSIX land, or the equivalents on Windows) to give the executable a better name, package it with the manual, and compute hashes for posting:

cd martus-summarizer/package-win/dist
mv main.exe Martus_Data_Summarizer.exe
cp ../../doc/Martus-Data-Summarizer-User-Guide-v1.1.pdf .
shasum Martus_Data_Summarizer.exe > Martus_Data_Summarizer.exe.sha1
zip Martus_Data_Summarizer.Win.zip Martus_Data_Summarizer.exe Martus-Data-Summarizer-User-Guide-v1.1.pdf
shasum Martus_Data_Summarizer.Win.zip > Martus_Data_Summarizer.Win.zip.sha1
rm Martus-Data-Summarizer-User-Guide-v1.1.pdf
