import pathlib

from .widget_tree import TreeWidget


class InputWidget(TreeWidget):
    """Widget in the RTDC tab view dealing with the output directory.
    Contains a lineEdit, a button, and a treeview widget."""
    def __init__(self, *args, **kwargs):
        super(InputWidget, self).__init__(which="input", *args, **kwargs)

        self.path = pathlib.Path.cwd()
