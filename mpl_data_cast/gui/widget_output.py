from PyQt6 import QtWidgets, QtCore, uic
import pkg_resources
import pathlib


class OutputPathError(BaseException):
    pass


class OutputWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        self.path = None
        super(OutputWidget, self).__init__(*args, **kwargs)

        QtWidgets.QMainWindow.__init__(self)
        path_ui = pkg_resources.resource_filename("mpl_data_cast.gui",
                                                  "widget_output.ui")
        uic.loadUi(path_ui, self)
        self.pushButton_output_dir.clicked.connect(
            self.on_task_select_output_dir)

    @QtCore.pyqtSlot()
    def on_task_select_output_dir(self):
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

    def update_output_dir(self, output_dir):
        output_dir = pathlib.Path(output_dir)
        if output_dir.exists():
            self.path = output_dir
            self.lineEdit_output.setText(str(output_dir))
            # todo update treeview
        else:
            raise OutputPathError("The output directory is not valid.")
