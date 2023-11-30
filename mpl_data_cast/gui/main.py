from importlib import resources
import time
import signal
import pathlib
import sys
import threading
import traceback

import dclab
import h5py
import numpy
from PyQt6 import uic, QtCore, QtWidgets

from .. import recipe as mpldc_recipe
from .._version import version

from . import preferences
from . import splash
from . import widget_tree


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
        # set default output path
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
    def on_recipe_changed(self):
        # Update the recipe description
        rec_cls = self.current_recipe
        doc = rec_cls.__doc__.strip().split("\n")[0]
        self.label_recipe_descr.setText(f"*{doc}*")
        self.widget_input.recipe = rec_cls
        self.widget_output.recipe = rec_cls

    @QtCore.pyqtSlot()
    def on_task_transfer(self) -> None:
        """Execute recipe to transfer data."""
        # sanity checks
        if not self.widget_input.path.exists():
            QtWidgets.QMessageBox.error(self,
                                        "Input directory error",
                                        "Input directory does not exist!")
        if not self.widget_output.path.exists():
            QtWidgets.QMessageBox.error(self,
                                        "Output directory error",
                                        "Output directory does not exist!")

        self.pushButton_transfer.setEnabled(False)
        rp = self.current_recipe(self.widget_input.path,
                                 self.widget_output.path)

        tree_counter = self.widget_input.tree_counter
        with CastingCallback(self, tree_counter) as path_callback:
            # run the casting operation in a separate thread
            caster = CastingThread(rp, path_callback=path_callback)
            caster.start()

        while not caster.result:
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
            time.sleep(.1)

        caster.join()
        result = caster.result

        self.widget_output.trigger_recount_objects()

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
        self.label_file.setText("")
        self.pushButton_transfer.setEnabled(True)


class CastingCallback:
    """Makes it possible to execute code everytime a file was processed.
    Used for updating the progress bar and calculating the processing rate."""

    def __init__(self,
                 gui: MPLDataCast,
                 tree_counter: widget_tree.TreeObjectCounter):
        self.gui = gui
        self.counter = 0
        #: This is a thread running in the background, counting recipe files.
        self.tree_counter = tree_counter

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __call__(self, path_list) -> None:
        path = path_list[0]
        # Let the user know where we are
        self.gui.label_file.setText(f"Processing {path}...")

        if self.tree_counter.has_counted:
            # Let the user know how far we are
            self.gui.progressBar.setRange(0, 100)
            self.gui.progressBar.setValue(
                int(self.counter / self.tree_counter.num_objects * 100))
        else:
            # go to undetermined state
            self.gui.progressBar.setRange(0, 0)

        self.counter += len(path_list)


class CastingThread(threading.Thread):
    def __init__(self, rp, path_callback, *args, **kwargs):
        super(CastingThread, self).__init__(*args, **kwargs)
        self.rp = rp
        self.path_callback = path_callback
        self.result = {}

    def run(self):
        self.result = self.rp.cast(path_callback=self.path_callback)


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


# Make Ctr+C close the app
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Display exception hook in separate dialog instead of crashing
sys.excepthook = excepthook
