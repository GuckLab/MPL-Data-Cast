from PyQt6 import QtWidgets, QtCore, uic
import pkg_resources
import pathlib


class InputPathError(BaseException):
    pass


class InputWidget(QtWidgets.QWidget):
    """Widget in the RTDC tab view dealing with the input directory.
    Contains a lineEdit, a button, and a treeview widget."""
    def __init__(self, *args, **kwargs):
        self.path = None
        super(InputWidget, self).__init__(*args, **kwargs)

        QtWidgets.QMainWindow.__init__(self)
        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "widget_input.ui")
        uic.loadUi(path_ui, self)
        self.pushButton_input_dir.clicked.connect(
            self.on_task_select_input_dir)
        self.lineEdit_input.editingFinished.connect(
            self.update_input_dir_from_lineedit)

    @QtCore.pyqtSlot()
    def on_task_select_input_dir(self):
        p = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select input directory:")
        self.update_input_dir(p)

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
            path_input = pp
        else:
            path_input = pp.parent

        self.update_input_dir(path_input)

    def update_input_dir_from_lineedit(self):
        """Executed when the input path was manually edited by the user."""
        output_dir = self.lineEdit_input.text()
        if output_dir:
            self.update_input_dir(output_dir)

    def update_input_dir(self, input_dir):
        """Checks if the input directory as given by the user exists and
        updates the lineEdit widget accordingly.
        Raises InputPathError if the directory does not exist.

        Parameter
        ---------
        input_dir: str or pathlib.Path
            The directory for the input.
        """
        input_dir = pathlib.Path(input_dir)
        if input_dir.exists():
            self.path = input_dir
            self.lineEdit_input.setText(str(input_dir))
            # todo update treeview
        else:
            raise InputPathError("The input directory is not valid, it "
                                 "does not seem to exist.")
