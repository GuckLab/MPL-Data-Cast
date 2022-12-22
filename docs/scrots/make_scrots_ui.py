"""Screenshots for documentation """
import sys
from PyQt6.QtWidgets import QApplication

from mpl_data_cast.gui.main import MPLDataCast
from mpl_data_cast.gui.preferences import Preferences

app = QApplication(sys.argv)

mw = MPLDataCast()
mw.grab().save("ui_main.png")

prf = Preferences(mw)
prf.grab().save("ui_preferences.png")

mw.close()
