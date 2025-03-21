import pathlib

from ..util import is_dir_writable

from .widget_tree import TreeWidget


class OutputWidget(TreeWidget):
    """Widget in the RTDC tab view dealing with the output directory.
    Contains a lineEdit, a button, and a treeview widget."""
    def __init__(self, *args, **kwargs):
        super(OutputWidget, self).__init__(which="output", *args, **kwargs)

        output_path = self.settings.value("main/output_path")
        if not is_dir_writable(output_path):
            output_path = pathlib.Path.home()
        self.path = pathlib.Path(output_path)
