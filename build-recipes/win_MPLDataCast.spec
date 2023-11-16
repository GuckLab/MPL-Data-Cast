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

pyz = PYZ(a.pure)

splash = Splash('../docs/artwork/mpldc_splash.png',
                binaries=a.binaries,
                datas=a.datas,
                text_pos=(44, 163),
                text_size=10,
                text_color='black',
                minify_script=True)

exe = EXE(pyz,
          a.scripts,
          splash,
          [],
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
               splash.binaries,
               strip=False,
               upx=False,
               name=NAME)
