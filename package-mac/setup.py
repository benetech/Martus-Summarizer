"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['../src/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSPrefersPPC': True,
        'CFBundleIdentifier': "org.benetech.martus.data_summarizer",
        'CFBundleName': "Martus Data Summarizer",
        'CFBundleDisplayName': "Martus Data Summarizer",
    },
    'iconfile': 'martus.icns'
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
