Directory for building a distributable Mac app of the Martus Data Summarizer.

Essentially, this packages the summarizer together with an entire Python distribution and the wxPython GUI libraries, both of which it needs to run.  This makes for a large App.

Uses py2app, which must be installed as a python package.
The documentation of py2app guided this build process and would be necessary to modify it:
http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html

To run:

# Remove any current build directories.
rm -rf build/ dist/*

# If setup.py is not present, recreate it:
py2applet --make-setup ../src/main.py

# Modify the setup.py as desired.  I did so by adding the following options:
# OPTIONS = {
#     'argv_emulation': True,
#     'plist': {
#         'LSPrefersPPC': True,
#         'CFBundleIdentifier': "org.benetech.martus.data_summarizer",
#         'CFBundleName': "Martus Data Summarizer",
#         'CFBundleDisplayName': "Martus Data Summarizer",
#     },
#     'iconfile': 'martus.icns'
# }


# Assemble the application bundle.
python setup.py py2app


# zip it up.  I've used the finder, but I'm sure command line works too.
cp ../doc/Martus-Data-Summarizer-User-Guide-v1.1.pdf dist/
cd dist
shasum Martus\ Data\ Summarizer.app > Martus_Data_Summarizer.app.sha1
zip -r Martus_Data_Summarizer.zip Martus\ Data\ Summarizer.app Summarizer-user-guide-v1.0.pdf
shasum Martus_Data_Summarizer.zip > Martus_Data_Summarizer.zip.sha1
rm -r Martus\ Data\ Summarizer.app Martus-Data-Summarizer-User-Guide-v1.1.pdf
cd ..

