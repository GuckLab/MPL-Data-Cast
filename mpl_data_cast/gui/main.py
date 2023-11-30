from importlib import resources
import time
import signal
import pathlib
import sys
import traceback

import dclab
import h5py
import numpy
from PyQt6 import uic, QtCore, QtWidgets

from .. import recipe as mpldc_recipe
from .._version import version

from . import preferences
from . import splash


class MPLDataCast(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        """Initialize MPL-Data-Cast"""
        # Settings apply to promoted widgets as well
        QtCore.QCoreApplication.setOrganizationName("MPL")
        QtCore.QCoreApplication.setApplicationName("MPL-Data-Cast")
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
        super(MPLDataCast, self).__init__(*args, **kwargs)

        # if "--version" was specified, print the version and exit
        if "--version" in sys.argv:
            print(version)
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
            sys.exit(0)

        ref_ui = resources.files("mpl_data_cast.gui") / "main.ui"
        with resources.as_file(ref_ui) as path_ui:
            uic.loadUi(path_ui, self)

        # settings
        self.settings = QtCore.QSettings()

        # Populate the recipe list
        recipes = mpldc_recipe.get_available_recipe_names()
        for rr in recipes:
            self.comboBox_recipe.addItem(rr, rr)
        # Set default recipe to "CatchAll"
        default = recipes.index("CatchAll")
        self.comboBox_recipe.setCurrentIndex(default)
        self.on_recipe_changed()

        # load some values from the settings
        # signals
        self.pushButton_transfer.clicked.connect(self.on_task_transfer)
        # GUI
        self.setWindowTitle(f"MPL-Data-Cast {version}")
        # Disable native menu bar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # File menu
        self.actionPreferences.triggered.connect(self.on_action_preferences)
        self.actionQuit.triggered.connect(self.on_action_quit)
        # Help menu
        self.actionSoftware.triggered.connect(self.on_action_software)
        self.actionAbout.triggered.connect(self.on_action_about)

        # Recipe selection
        self.comboBox_recipe.currentIndexChanged.connect(
            self.on_recipe_changed)

        self.show()
        self.raise_()
        splash.splash_close()

    @property
    def current_recipe(self):
        name = self.comboBox_recipe.currentData()
        return mpldc_recipe.map_recipe_name_to_class(name)

    @QtCore.pyqtSlot()
    def on_action_preferences(self):
        """Show the preferences dialog"""

        dlg = preferences.Preferences(self)
        dlg.setWindowTitle("MPL-Data-Cast Preferences")
        dlg.exec()
        # update maximum tree depth
        self.widget_output.tree_depth_limit = int(self.settings.value(
            "main/tree_depth_limit", 8))
        self.widget_input.tree_depth_limit = int(self.settings.value(
            "main/tree_depth_limit", 8))
        self.widget_output.path = self.settings.value("main/output_path",
                                                      pathlib.Path.home())

    @QtCore.pyqtSlot()
    def on_action_quit(self) -> None:
        """Determine what happens when the user wants to quit"""
        QtCore.QCoreApplication.quit()

    def on_action_about(self) -> None:
        """Show imprint."""
        gh = "GuckLab/MPL-Data-Cast"
        rtd = "mpl-data-cast.readthedocs.io"
        about_text = "Convert and transfer data.<br><br>" \
                     + "Author: Paul Müller and others<br>" \
                     + "GitHub: " \
                     + "<a href='https://github.com/{gh}'>{gh}</a><br>".format(gh=gh) \
                     + "Documentation: " \
                     + "<a href='https://{rtd}'>{rtd}</a><br>".format(rtd=rtd)  # noqa 501
        QtWidgets.QMessageBox.about(self,
                                    "MPL-Data-Cast {}".format(version),
                                    about_text)

    @QtCore.pyqtSlot()
    def on_action_software(self) -> None:
        """Show used software packages and dependencies."""
        libs = [dclab,
                h5py,
                numpy,
                ]

        sw_text = f"MPL-Data-Cast {version}\n\n"
        sw_text += f"Python {sys.version}\n\n"
        sw_text += "Modules:\n"
        for lib in libs:
            sw_text += f"- {lib.__name__} {lib.__version__}\n"
        sw_text += f"- PyQt6 {QtCore.QT_VERSION_STR}\n"

        QtWidgets.QMessageBox.information(self, "Software", sw_text)

    @QtCore.pyqtSlot()
    def on_task_transfer(self) -> None:
        """Execute recipe to transfer data."""
        if not self.widget_input.path.exists():
            QtWidgets.QMessageBox.information(self, "Error",
                                              "Input directory not correct!")
        if not self.widget_output.path.exists():
            QtWidgets.QMessageBox.information(self, "Error",
                                              "Output directory not correct!")

        rp = self.current_recipe(self.widget_input.path,
                                 self.widget_output.path)

        nb_files = 0  # counter for files, used for progress bar
        for elem in self.widget_input.path.rglob("*"):
            if (elem.is_file()
                    and elem.name not in mpldc_recipe.IGNORED_FILE_NAMES):
                nb_files += 1
        with Callback(self, nb_files) as path_callback:
            result = rp.cast(path_callback=path_callback)
        if result["success"]:
            self.progressBar.setValue(100)
            QtWidgets.QMessageBox.information(self, "Transfer completed",
                                              "Data transfer completed.")
            self.progressBar.setValue(0)
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
        else:
            msg = "Some problems occured during data transfer:\n"
            for path, _ in result["errors"]:
                msg += f" - {path}\n"

            QtWidgets.QMessageBox.information(self, "Error", msg)

            text = ""
            for path, tb in result["errors"]:
                text += f"PATH {path}:\n{tb}\n\n"
            pathlib.Path("mpldc-dump.txt").write_text(text)

    @QtCore.pyqtSlot()
    def on_recipe_changed(self):
        # Update the recipe description
        rec_cls = self.current_recipe
        doc = rec_cls.__doc__.strip().split("\n")[0]
        self.label_recipe_descr.setText(f"*{doc}*")
        self.widget_input.recipe = rec_cls
        self.widget_output.recipe = rec_cls


class Callback:
    """Makes it possible to execute code everytime a file was processed.
    Used for updating the progress bar and calculating the processing rate."""

    def __init__(self, gui, max_count: int):
        self.gui = gui
        self.counter = 0
        self.max_count = max_count
        self.size = 0
        self.time_start = time.monotonic()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __call__(self, path) -> None:
        self.size += path.stat().st_size
        self.gui.progressBar.setValue(int(self.counter / self.max_count * 100))
        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
        self.counter += 1


def excepthook(etype, value, trace) -> None:
    """
    Handler for all unhandled exceptions.

    Parameters
    ----------
    etype : Type[BaseException]
        the exception type (`SyntaxError`, `ZeroDivisionError`, etc...)
    value : BaseException | str
        The exception error message;
    trace : TracebackType | str
        the traceback header, if any (otherwise, it prints the standard
        Python header: ``Traceback (most recent call last)``.
    """
    vinfo = f"Unhandled exception in MPL-Data-Cast version {version}:\n"
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join([vinfo] + tmp)

    errorbox = QtWidgets.QMessageBox()
    errorbox.addButton(QtWidgets.QPushButton('Close'),
                       QtWidgets.QMessageBox.ButtonRole.YesRole)
    errorbox.addButton(QtWidgets.QPushButton(
        'Copy text && Close'), QtWidgets.QMessageBox.ButtonRole.NoRole)
    errorbox.setText(exception)
    ret = errorbox.exec()
    if ret == 1:
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(exception)


def error(message: str, info: str = "", details: str = "") -> None:
    """Shows a little window for error messages."""
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    msg.setWindowTitle("Errors occured")
    msg.setText(message)
    if info:
        msg.setInformativeText(info)
    if details:
        msg.setDetailedText(details)
    msg.exec()


# Make Ctr+C close the app
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Display exception hook in separate dialog instead of crashing
sys.excepthook = excepthook
