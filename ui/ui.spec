# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files
import pyqtlet
import os

osgeo_binaries = collect_data_files('osgeo', include_py_files=True)

block_cipher = None

binaries = []
for p, lib in osgeo_binaries:
    if '.pyd' in p:
        binaries.append((p, '.'))

a = Analysis(['ui.py', 'ui.spec'],
             pathex=['.'],
             binaries=binaries,
             datas=[(os.path.dirname(pyqtlet.__file__), 'pyqtlet')],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='SHETran Results Viewer',
          debug=True,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
