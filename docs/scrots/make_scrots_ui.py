"""Screenshots for documentation """
import sys
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication

from mpl_data_cast.gui.main import MPLDataCast

app = QApplication(sys.argv)

mw = MPLDataCast()
mw.grab().save("ui_main.png")

mw.close()
