from PyQt6 import QtWidgets, QtCore, uic
from importlib import resources
import pathlib

from ..path_tree import PathTree, list_items_in_tree
from ..util import is_dir_writable


class TreeWidget(QtWidgets.QWidget):
    def __init__(self, which="tree", *args, **kwargs):
        """Widget handling tree views for directories"""
        super(TreeWidget, self).__init__(*args, **kwargs)
        ref_ui = resources.files("mpl_data_cast.gui") / "widget_tree.ui"
        with resources.as_file(ref_ui) as path_ui:
            uic.loadUi(path_ui, self)

        self.which = which
        self.groupBox.setTitle(self.which.capitalize())
        self.pushButton_dir.setText(f"Select {self.which} directory")
        self.path = None
        self.p_tree = None
        self.settings = QtCore.QSettings()
        self.tree_depth_limit = int(self.settings.value(
            "main/tree_depth_limit", 3))
        self.update_tree_dir(str(pathlib.Path.home()))

        self.pushButton_dir.clicked.connect(
            self.on_task_select_tree_dir)
        self.lineEdit_dir.editingFinished.connect(
            self.update_tree_dir_from_lineedit)

    @QtCore.pyqtSlot()
    def on_task_select_tree_dir(self) -> None:
        p = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption=f"Select {self.which} directory:",
            directory=str(self.path) if self.path else None)
        if p:
            self.update_tree_dir(p)

    def dragEnterEvent(self, e) -> None:
        """Whether files are accepted"""
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e) -> None:
        """Add dropped directory to treeview and lineedit."""
        urls = e.mimeData().urls()
        file_1 = urls[0]
        pp = pathlib.Path(file_1.toLocalFile())
        if pp.is_dir():
            path_tree = pp
        else:
            path_tree = pp.parent

        self.update_tree_dir(path_tree)

    @QtCore.pyqtSlot()
    def update_tree_dir_from_lineedit(self) -> None:
        """Executed when the tree path was manually edited by the user."""
        tree_dir = self.lineEdit_dir.text()
        if tree_dir:
            self.update_tree_dir(tree_dir)

    def update_tree_dir(self, tree_dir: str | pathlib.Path) -> None:
        """Checks if the tree directory as given by the user exists and
        updates the lineEdit widget accordingly.

        Parameter
        ---------
        tree_dir: str or pathlib.Path
            The directory for the tree.
        """
        if is_dir_writable(tree_dir):
            tree_dir = pathlib.Path(tree_dir)
            self.path = tree_dir
            self.lineEdit_dir.setText(str(tree_dir))
            self.update_tree()
        else:
            msg_txt = f"The {self.which} directory '{tree_dir}' is not " \
                      f"valid. Please select a different directory."
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText(msg_txt)
            msg.setWindowTitle(f"{self.which.capitalize()} directory invalid")
            msg.exec()

    def update_tree(self) -> None:
        """Update the `PathTree` object based on the current root path in
        `self.path` and update the GUI to show the new tree."""
        self.p_tree = PathTree(self.path, self.tree_depth_limit)
        self.treeWidget.clear()
        self.treeWidget.setColumnCount(self.p_tree.tree_depth + 1)

        list_items_in_tree(self.p_tree,
                           self.treeWidget,
                           h_level=0,
                           depth_limit=self.tree_depth_limit)

        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
