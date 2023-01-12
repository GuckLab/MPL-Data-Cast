from PyQt6 import QtWidgets, QtCore, uic
import pkg_resources
import pathlib

from ..path_tree import PathTree, list_items_in_tree


class OutputWidget(QtWidgets.QWidget):
    """Widget in the RTDC tab view dealing with the output directory.
    Contains a lineEdit, a button, and a treeview widget."""
    def __init__(self, *args, **kwargs):
        super(OutputWidget, self).__init__(*args, **kwargs)

        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "widget_output.ui")
        uic.loadUi(path_ui, self)

        self.path = None
        self.p_tree = None
        self.tree_depth_limit = 3

        self.pushButton_output_dir.clicked.connect(
            self.on_task_select_output_dir)
        self.lineEdit_output.editingFinished.connect(
            self.update_output_dir_from_lineedit)

    @QtCore.pyqtSlot()
    def on_task_select_output_dir(self) -> None:
        p = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select output directory:")
        self.update_output_dir(p)

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
            path_output = pp
        else:
            path_output = pp.parent

        self.update_output_dir(path_output)

    @QtCore.pyqtSlot()
    def update_output_dir_from_lineedit(self) -> None:
        """Executed when the output path was manually edited by the user."""
        output_dir = self.lineEdit_output.text()
        if output_dir:
            self.update_output_dir(output_dir)

    def update_output_dir(self, output_dir: str | pathlib.Path) -> None:
        """Checks if the output directory as given by the user exists and
        updates the lineEdit widget accordingly.

        Parameter
        ---------
        output_dir: str or pathlib.Path
            The directory for the output.
        """
        output_dir = pathlib.Path(output_dir)
        if output_dir.exists():
            self.path = output_dir
            self.lineEdit_output.setText(str(output_dir))
            self.update_tree()
        else:
            msg_txt = "The output directory is not valid, it does not seem" \
                      " to exist."
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText(msg_txt)
            msg.setWindowTitle("Warning")
            msg.exec()

    def update_tree(self) -> None:
        """Update the `PathTree` object based on the current root path in
        `self.path` and update the GUI to show the new tree."""
        self.p_tree = PathTree(self.path, self.tree_depth_limit)
        self.treeWidget_output.clear()
        self.treeWidget_output.setColumnCount(self.p_tree.tree_depth + 1)

        list_items_in_tree(self.p_tree,
                           self.treeWidget_output,
                           h_level=0,
                           depth_limit=self.tree_depth_limit)

        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)
