import pathlib
import tempfile

from mpl_data_cast.mod_recipes import CatchAllRecipe


def test_basic():
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="rcp_catchall"))
    one = tmpdir / "input" / "folder" / "a.txt"
    one.parent.mkdir(parents=True)
    one.write_text("hello testing world")
    two = tmpdir / "input" / "1.txt"
    two.write_text("Another file!")

    target = tmpdir / "output"
    target.mkdir(parents=True)

    rcp = CatchAllRecipe(path_raw=tmpdir/"input", path_tar=tmpdir/"output")
    rcp.cast()

    assert (target / "folder" / "a.txt").read_text() == "hello testing world"
    assert (target / "1.txt").read_text() == "Another file!"
