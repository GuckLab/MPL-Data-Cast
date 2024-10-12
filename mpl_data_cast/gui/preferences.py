from importlib import resources
import pathlib
import warnings

from PyQt6 import uic, QtCore, QtWidgets

from .. import recipe as mpldc_recipe
from ..util import is_dir_writable


class Preferences(QtWidgets.QDialog):
    """Preferences dialog"""
    feature_changed = QtCore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, parent=parent, *args, **kwargs)

        ref_ui = resources.files("mpl_data_cast.gui") / "preferences.ui"
        with resources.as_file(ref_ui) as path_ui:
            uic.loadUi(path_ui, self)

        self.settings = QtCore.QSettings()
        self.parent = parent

        # Populate the recipe list
        self.available_recipes = mpldc_recipe.get_available_recipe_names()
        for rr in self.available_recipes:
            self.comboBox_recipe.addItem(rr, rr)
        #: configuration keys, corresponding widgets, and defaults
        self.config_pairs = [
            ["main/output_path", self.lineEdit_output_path,
             pathlib.Path.home()],
            ["main/recipe", self.comboBox_recipe, "CatchAll"]
        ]
        self.reload()

        # signals
        self.btn_ok = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.btn_ok.clicked.connect(self.on_settings_ok)
        self.btn_cancel = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.btn_restore = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        self.btn_restore.clicked.connect(self.on_settings_restore)
        self.pushButton_output_path.clicked.connect(
            self.on_task_select_output_dir)

    def reload(self):
        """Read configuration or set default parameters"""
        for key, widget, default in self.config_pairs:
            value = self.settings.value(key, default)
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(bool(int(value)))
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(int(value))
            elif widget is self.comboBox_recipe:
                recipe_idx = self.available_recipes.index(str(value))
                widget.setCurrentIndex(recipe_idx)
            else:
                raise NotImplementedError("No rule for '{}'".format(key))

    @QtCore.pyqtSlot()
    def on_settings_ok(self):
        """Save current changes made in UI to settings and reload UI"""
        for key, widget, default in self.config_pairs:
            if isinstance(widget, QtWidgets.QCheckBox):
                value = int(widget.isChecked())
            elif isinstance(widget, QtWidgets.QLineEdit):
                value = widget.text().strip()
                if widget is self.lineEdit_output_path:
                    if not pathlib.Path(value).exists():
                        warnings.warn(f"Path {value} does not exist, "
                                      f"defaulting to user home directory.")
                        value = str(pathlib.Path.home())
            elif isinstance(widget, QtWidgets.QSpinBox):
                value = int(widget.value())
            elif isinstance(widget, QtWidgets.QComboBox):
                value = widget.currentData()
            else:
                raise NotImplementedError("No rule for '{}'".format(key))
            self.settings.setValue(key, value)

        # reload UI to give visual feedback
        self.reload()

    @QtCore.pyqtSlot()
    def on_settings_restore(self):
        self.settings.clear()
        self.reload()

    @QtCore.pyqtSlot()
    def on_task_select_output_dir(self) -> None:
        p = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select output directory:",
            directory=self.lineEdit_output_path.text())
        if p:
            if is_dir_writable(p):
                self.lineEdit_output_path.setText(str(p))
            else:
                raise ValueError(f"Directory {p} is not writable!")
