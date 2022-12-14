import os
import time
import sys
import pathlib
import dclab
import h5py
import numpy
import pkg_resources
from PyQt6 import uic, QtCore, QtGui, QtWidgets

from ..mod_recipes.rcp_rtdc import RTDCRecipe
from .._version import version as __version__

# set Qt icon theme search path
QtGui.QIcon.setThemeSearchPaths([
    os.path.join(pkg_resources.resource_filename("mpl_data_cast", "img"),
                 "icon-theme")])
QtGui.QIcon.setThemeName(".")


class TargetPathError(BaseException):
    pass


class MPLDataCast(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        """Initialize MPL-Data-Cast"""
        QtCore.QCoreApplication.setApplicationName("MPL-Data-Cast")
        super(MPLDataCast, self).__init__(*args, **kwargs)

        QtWidgets.QMainWindow.__init__(self)
        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "main.ui")
        uic.loadUi(path_ui, self)

        # some variables
        self.path_input = None
        self.path_target = None
        # signals
        self.pushButton_transfer.clicked.connect(self.on_task_transfer)
        # connect the lineEdit editingFinished() signal to the function to
        # update the text displayed in the lineEdit element
        # self.lineEdit_input.textEdited.connect(self.update_input_dir())
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

    # @show_wait_cursor
    @QtCore.pyqtSlot()
    def on_task_transfer(self):
        if not self.widget_input.path.exists():
            QtWidgets.QMessageBox.information(self, "Error",
                                              "Input directory not correct!")
            # raise InputPathError
        if not self.widget_output.path.exists():
            QtWidgets.QMessageBox.information(self, "Error",
                                              "Target directory not correct!")
            # raise TargetPathError

        # instantiate the class
        rp = RTDCRecipe(self.widget_input.path, self.widget_output.path)

        nb_files = 0
        for elem in self.widget_input.path.rglob("*.*"):
            if elem.is_file():
                nb_files += 1
        with Callback(self, nb_files) as path_callback:
            result = rp.cast(path_callback=path_callback)
        if result["success"]:
            QtWidgets.QMessageBox.information(self, "Transfer completed",
                                              "Data transfer completed.")
        else:
            msg = "Some problems occured during data transfer:\n"
            for path, _ in result["errors"]:
                msg += f" - {path}\n"

            QtWidgets.QMessageBox.information(
                self, "Error", msg)

            text = ""
            for path, tb in result["errors"]:
                text += f"PATH {path}:\n{tb}\n\n"
            pathlib.Path("mpldc-dump.txt").write_text(text)


class Callback:
    def __init__(self, gui, max_count):
        self.gui = gui
        self.counter = 0
        self.max_count = max_count
        self.size = 0
        self.time_start = time.monotonic()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __call__(self, path):
        self.counter += 1
        self.size += path.stat().st_size
        self.gui.progressBar.setValue(int(self.counter/self.max_count * 100))
        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)

    def get_rate(self):
        curtime = time.monotonic()
        if curtime > self.time_start:
            return self.size / 1024 ** 2 / (curtime - self.time_start)
        else:
            return 0
