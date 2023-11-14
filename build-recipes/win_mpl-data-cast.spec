# -*- mode: python ; coding: utf-8 -*-
from os.path import exists
import warnings

import mpl_data_cast

NAME = "MPLDataCast"

if not exists("./{}Launcher.py".format(NAME)):
    warnings.warn("Cannot find {}Launcher.py'! ".format(NAME) +
                  "Please run pyinstaller from the 'build-recipes' directory.")


a = Analysis([NAME + "Launcher.py"],
             pathex=["."],
             hookspath=["."],
             runtime_hooks=None)

options = [ ('u', None, 'OPTION'), ('W ignore', None, 'OPTION') ]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name=NAME + ".exe",
          debug=False,
          strip=False,
          upx=False,
          icon=NAME + ".ico",
          console=bool(mpl_data_cast.__version__.count("post")),)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name=NAME)
