import tempfile as tf
import pathlib
import shutil

from helper import retrieve_data
from mpl_data_cast.path_tree import PathTree


def test_simple_tree_from_dir():
    """Check basic attributes of a small tree"""
    with tf.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        tree = PathTree(tmpdir)
        assert isinstance(tree.tree_root, pathlib.Path)
        assert isinstance(tree.children, dict)
        assert tree.tree_depth == 0


def test_simple_tree_from_file():
    """Check basic attributes of a small tree"""
    with tf.TemporaryDirectory() as tmpdir:
        with tf.NamedTemporaryFile(dir=tmpdir) as tmpfile:
            tmpfile = pathlib.Path(str(tmpfile.name))
            tree = PathTree(tmpfile)
            assert isinstance(tree.tree_root, pathlib.Path)
            assert tree.tree_depth == 0
            assert tree.tree_root == tmpfile.parent


def test_tree_with_subdir():
    with tf.TemporaryDirectory() as tmpdir:
        with tf.TemporaryDirectory(dir=tmpdir) as tmpdir2:
            tmpdir = pathlib.Path(tmpdir)
            tmpdir2 = pathlib.Path(tmpdir2)

            tree = PathTree(tmpdir)
            assert tree.tree_depth == 1
            assert len(tree.children) == 1
            assert tmpdir2.name in tree.children.keys()
            assert isinstance(tree.children[tmpdir2.name], PathTree)


def test_tree_with_subdir_and_files(tmp_path):
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    test_file = path_in / "M001_data.rtdc"
    t_file1 = tmp_path / "M001_data.rtdc"
    shutil.copy(test_file, t_file1)
    with tf.TemporaryDirectory(dir=tmp_path) as tmpdir2:
        tmpdir2 = pathlib.Path(tmpdir2)
        t_file2 = tmpdir2 / "M002_data.rtdc"
        shutil.copy(t_file1, t_file2)

        assert t_file1.exists()
        assert t_file2.exists()
        tree = PathTree(tmp_path)

        assert tree.tree_depth == 1
        assert len(tree.get_file_list()) == 1
        child_tree = tree.children[tmpdir2.name]
        assert isinstance(child_tree, PathTree)
        assert child_tree.tree_depth == 0
        assert child_tree.get_file_list()[0] == t_file2
