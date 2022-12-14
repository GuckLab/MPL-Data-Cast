from PyQt6 import QtWidgets, QtCore, uic
import pkg_resources
import pathlib


class InputPathError(BaseException):
    pass


class InputWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        self.path = None
        super(InputWidget, self).__init__(*args, **kwargs)

        QtWidgets.QMainWindow.__init__(self)
        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "widget_input.ui")
        uic.loadUi(path_ui, self)
        self.pushButton_input_dir.clicked.connect(
            self.on_task_select_input_dir)

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
        """Add dropped directory to treeview and lineedit.

        todo implement transfer of single files
        """
        urls = e.mimeData().urls()
        file_1 = urls[0]
        pp = pathlib.Path(file_1.toLocalFile())
        if pp.is_dir():
            path_input = pp
        else:
            path_input = pp.parent

        self.update_input_dir(path_input)
        # todo update lineEdit
        # todo update tree view

    def update_input_dir(self, input_dir):
        input_dir = pathlib.Path(input_dir)
        if input_dir.exists():
            self.path = input_dir
            self.lineEdit_input.setText(str(input_dir))
            # todo update treeview
        else:
            raise InputPathError("The input directory is not valid.")
