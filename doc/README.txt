IIThis is a stand-alone packaging of the martus flattener and martus summarizer tools, with a GUI, designed for easy distribution to and running by Martus users who want a quick summary of their data.

Single-file distribution
------------------------
This program is packaged into a single Windows .exe using pyinstaller


Libraries
---------
This program is mean to run totally on its own, outside the standard hrdag software environment.  That means that all hrdag libraries it needs are copied into the src/ directory for packaging into the tool.  In most cases, these libraries are modified for use in the summarizer, usually by simplifying them, removing unit tests, removing features, etc.