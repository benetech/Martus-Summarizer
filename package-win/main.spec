# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '../src/main.py'],
             pathex=['C:\\Users\\jeff\\Desktop\\martus-summarizer\\package-win'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'main.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='martus.ico')
app = BUNDLE(exe,
             name=os.path.join('dist', 'main.exe.app'))
