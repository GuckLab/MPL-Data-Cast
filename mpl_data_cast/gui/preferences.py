import pathlib
from PyQt6 import uic, QtCore, QtWidgets
import pkg_resources


from ..util import is_dir_writable


class Preferences(QtWidgets.QDialog):
    """Preferences dialog"""
    feature_changed = QtCore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, parent=parent, *args, **kwargs)
        path_ui = pkg_resources.resource_filename(
            "mpl_data_cast.gui", "preferences.ui")
        uic.loadUi(path_ui, self)
        self.settings = QtCore.QSettings()
        self.parent = parent

        #: configuration keys, corresponding widgets, and defaults
        self.config_pairs = [
            ["rtdc/output_path", self.rtdc_output_path,
             pathlib.Path.cwd()],
            ["rtdc/tree_depth_limit", self.tree_depth_limit, 3],
        ]
        self.reload()

        # signals
        self.btn_apply = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.on_settings_apply)
        self.btn_cancel = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.btn_restore = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        self.btn_restore.clicked.connect(self.on_settings_restore)
        self.select_rtdc_output_path.clicked.connect(
            self.on_task_select_output_dir)
        # tab changed
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

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
            else:
                raise NotImplementedError("No rule for '{}'".format(key))

    @QtCore.pyqtSlot()
    def on_settings_apply(self):
        """Save current changes made in UI to settings and reload UI"""
        for key, widget, default in self.config_pairs:
            if isinstance(widget, QtWidgets.QCheckBox):
                value = int(widget.isChecked())
            elif isinstance(widget, QtWidgets.QLineEdit):
                value = widget.text().strip()
                if widget is self.rtdc_output_path:
                    prev_value = self.settings.value(key)
                    path = pathlib.Path(widget.text().strip())
                    if path.exists():
                        value = str(path)
                    else:
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                        msg.setText("Given path does not exist! Please "
                                    "check!\nPrevious setting will be"
                                    " restored.")
                        msg.setWindowTitle("Warning")
                        msg.exec()
                        if pathlib.Path(prev_value).exists():
                            value = prev_value
                        else:
                            msg = QtWidgets.QMessageBox()
                            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                            msg.setText("Path from previous settings does not "
                                        "exist either, original default output"
                                        " path is restored.")
                            msg.setWindowTitle("Warning")
                            msg.exec()
                            value = pathlib.Path.cwd()
            elif isinstance(widget, QtWidgets.QSpinBox):
                value = int(widget.value())
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
    def on_tab_changed(self):
        self.btn_apply.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.btn_restore.setEnabled(True)

    @QtCore.pyqtSlot()
    def on_task_select_output_dir(self) -> None:
        p = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select output directory:",
            directory=self.rtdc_output_path.text())
        if p:
            if is_dir_writable(p):
                self.rtdc_output_path.setText(str(p))
            else:
                raise ValueError(f"Directory {p} is not writable!")
