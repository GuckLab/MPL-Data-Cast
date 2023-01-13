import tempfile as tf
import pathlib
import shutil

import pytest

from helper import retrieve_data
from mpl_data_cast.path_tree import PathTree, PathError


def test_simple_tree_from_dir():
    """Check basic attributes of a small tree"""
    with tf.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        tree = PathTree(tmpdir, depth_limit=10)
        assert isinstance(tree.tree_root, pathlib.Path)
        assert isinstance(tree.children, dict)
        assert tree.tree_depth == 1


def test_simple_tree_from_file():
    """Check PathTree generation with just one file."""
    with tf.TemporaryDirectory() as tmpdir:
        with tf.NamedTemporaryFile(dir=tmpdir) as tmpfile:
            tmpfile = pathlib.Path(str(tmpfile.name))
            tree = PathTree(tmpfile)
            assert isinstance(tree.tree_root, pathlib.Path)
            assert tree.tree_depth == 1
            assert tree.tree_root == tmpfile.parent


def test_wrong_input_raises_errors(tmp_path):
    """Check that errors are raised in case the input for the PathTree
    constructor is wrong."""
    with pytest.raises(TypeError):
        _ = PathTree(r"some/path/to/dir")
    with pytest.raises(PathError):
        _ = PathTree(pathlib.Path(r"some/path/somewhere"))


def test_tree_with_subdir():
    """Check PathTree generation with a subfolder"""
    with tf.TemporaryDirectory() as tmpdir:
        with tf.TemporaryDirectory(dir=tmpdir) as tmpdir2:
            tmpdir = pathlib.Path(tmpdir)
            tmpdir2 = pathlib.Path(tmpdir2)

            tree = PathTree(tmpdir)
            assert tree.tree_depth == 2
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

        assert tree.tree_depth == 2
        assert len(tree.get_file_list()) == 1
        child_tree = tree.children[tmpdir2.name]
        assert isinstance(child_tree, PathTree)
        assert child_tree.tree_depth == 1
        assert child_tree.get_file_list()[0] == t_file2


def test_tree_with_hidden_file(tmp_path):
    """Check that PathTree ignores hidden files which start with a '.'"""
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    test_file = path_in / "M001_data.rtdc"
    t_file1 = tmp_path / "M001_data.rtdc"
    # and a "hidden" file
    t_file2 = tmp_path / ".M001_data.rtdc"
    shutil.copy(test_file, t_file1)
    shutil.copy(test_file, t_file2)
    with tf.TemporaryDirectory(dir=tmp_path) as tmpdir2:
        tmpdir2 = pathlib.Path(tmpdir2)
        t_file3 = tmpdir2 / "M002_data.rtdc"
        shutil.copy(t_file1, t_file3)

        assert t_file1.exists()
        assert t_file2.exists()
        assert t_file3.exists()
        tree = PathTree(tmp_path)

        assert tree.tree_depth == 2
        assert len(tree.get_file_list()) == 1
        child_tree = tree.children[tmpdir2.name]
        assert isinstance(child_tree, PathTree)
        assert child_tree.tree_depth == 1
        assert child_tree.get_file_list()[0] == t_file3


def test_path_in_tree(tmp_path):
    """Check that the __contains__ functionality works"""
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    test_file = path_in / "M001_data.rtdc"
    t_file1 = tmp_path / "M001_data.rtdc"
    shutil.copy(test_file, t_file1)
    with tf.TemporaryDirectory(dir=tmp_path) as tmpdir2:
        tmpdir2 = pathlib.Path(tmpdir2)
        with tf.TemporaryDirectory(dir=tmpdir2) as tmpdir3:
            tmpdir3 = pathlib.Path(tmpdir3)

            tree = PathTree(tmp_path)
            assert tree.tree_depth == 3
            assert tmpdir2 in tree
            assert tmpdir3 in tree


def test_retrieve_full_tree(tmp_path):
    """Check that the function `retrieve_full_path_tree()` acutally returns
    a PathTree object with all subdirectories in full depth."""
    with tf.TemporaryDirectory(dir=tmp_path) as tmpdir2:
        tmpdir2 = pathlib.Path(tmpdir2)
        with tf.TemporaryDirectory(dir=tmpdir2) as tmpdir3:
            _ = pathlib.Path(tmpdir3)

            tree = PathTree(tmp_path, depth_limit=2)
            assert tree.tree_depth == 2

            full_tree = tree.retrieve_full_path_tree()
            assert full_tree.tree_depth == 3
            assert full_tree.tree_root.samefile(tree.tree_root)


def test_small_path_tree(tmp_path):
    """Have a shallow PathTree object and check that the children on the
    deepest level do not have PathTree objects as children, but only a list
    of subdirectories in `PathTree.list_child_dirs`."""
    with tf.TemporaryDirectory(dir=tmp_path) as tmpdir2:
        tmpdir2 = pathlib.Path(tmpdir2)
        with tf.TemporaryDirectory(dir=tmpdir2) as tmpdir3:
            tmpdir3 = pathlib.Path(tmpdir3)

            tree = PathTree(tmp_path, depth_limit=2)
            assert tree.tree_depth == 2
            child_tree = tree.children[tmpdir2.name]
            assert not child_tree.children
            assert child_tree.list_child_dirs
            assert child_tree.list_child_dirs[0] == tmpdir3.name

            # check whether the __contains__ magic function was implemented
            # correctly
            assert tmpdir2 in tree
            assert tmpdir3 in tree
            assert tmpdir3 in child_tree
