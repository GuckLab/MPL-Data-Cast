import os
import sys
import dclab
import h5py
import numpy
import pkg_resources
from PyQt6 import uic, QtCore, QtGui, QtWidgets

from .._version import version as __version__

# set Qt icon theme search path
QtGui.QIcon.setThemeSearchPaths([
    os.path.join(pkg_resources.resource_filename("mpl_data_cast", "img"),
                 "icon-theme")])
QtGui.QIcon.setThemeName(".")


class MPLDataCast(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        """Initialize MPL-Data-Cast"""
        QtCore.QCoreApplication.setApplicationName("MPL-Data-Cast")

        super(MPLDataCast, self).__init__(*args, **kwargs)

        QtWidgets.QMainWindow.__init__(self)
        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "main.ui")
        uic.loadUi(path_ui, self)

        # GUI
        self.setWindowTitle(f"MPL-Data-Cast {__version__}")
        # Disable native menu bar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # File menu
        self.actionQuit.triggered.connect(self.on_action_quit)
        # Help menu
        self.actionSoftware.triggered.connect(self.on_action_software)
        self.actionAbout.triggered.connect(self.on_action_about)

        self.show()
        self.raise_()

    @QtCore.pyqtSlot()
    def on_action_quit(self):
        """Determine what happens when the user wants to quit"""
        QtCore.QCoreApplication.quit()

    def on_action_about(self):
        gh = "GuckLab/MPL-Data-Cast"
        rtd = "mpl-data-cast.readthedocs.io"
        about_text = "Convert and transfer data from measurement PCs to " \
                     "network shares at MPL.<br><br>" \
                     + "Author: Paul Müller and others<br>" \
                     + "GitHub: " \
                     + "<a href='https://github.com/{gh}'>{gh}</a><br>".format(gh=gh) \
                     + "Documentation: " \
                     + "<a href='https://{rtd}'>{rtd}</a><br>".format(rtd=rtd)
        QtWidgets.QMessageBox.about(self,
                                    "MPL-Data-Cast {}".format(__version__),
                                    about_text)

    @QtCore.pyqtSlot()
    def on_action_software(self):
        libs = [dclab,
                h5py,
                numpy,
                ]

        sw_text = f"MPL-Data-Cast {__version__}\n\n"
        sw_text += f"Python {sys.version}\n\n"
        sw_text += "Modules:\n"
        for lib in libs:
            sw_text += f"- {lib.__name__} {lib.__version__}\n"
        sw_text += f"- PyQt6 {QtCore.QT_VERSION_STR}\n"

        QtWidgets.QMessageBox.information(self, "Software", sw_text)
