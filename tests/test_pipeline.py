import pathlib
import tempfile

from mpl_data_cast import Pipeline


def make_example_data():
    td = pathlib.Path(tempfile.mkdtemp())
    d1 = td / "hans" / "peter"
    d1.mkdir(parents=True, exist_ok=True)
    d2 = td / "fliege"
    d2.mkdir(parents=True, exist_ok=True)
    (d1 / "a.txt").write_text("hello ")
    (d1 / "b.txt").write_text("world!")
    (d2 / "1.txt").write_text("lorem ")
    (d2 / "2.txt").write_text("ipsum ")
    (d2 / "3.txt").write_text("dolor sit ")
    (d2 / "4.txt").write_text("amet.")
    return td


class DummyRecipe(Pipeline):
    """A pipeline that just concatenates text files"""
    def convert_dataset(self, path_list, temp_path):
        data = ""
        for pp in path_list:
            data += pp.read_text()
        temp_path.write_text(data)

    def get_raw_data_list(self):
        data_list = []
        for pp in self.path_raw.rglob("*"):
            if pp.is_dir():
                files = sorted(pp.rglob("*.txt"))
                if files:
                    data_list.append(files)
        return data_list


def test_pipeline_init():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    pl = DummyRecipe(path_raw, path_tar)
    assert pl.tempdir.exists()
    assert pl.format == "DummyPipeline"
    assert not path_tar.exists()


def test_pipeline_cast():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    pl = DummyRecipe(path_raw, path_tar)
    pl.cast()
    text1 = (path_tar / "hans" / "peter" / "a.txt").read_text()
    assert text1 == "hello world!"
    text2 = (path_tar / "fliege" / "1.txt").read_text()
    assert text2 == "lorem ipsum dolor sit amet."


def test_pipeline_get_target_path():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    path_tar.mkdir()
    pl = DummyRecipe(path_raw, path_tar)

    tar1 = path_tar / "fliege" / "1.txt"
    assert str(pl.get_target_path(pl.get_raw_data_list()[0])) == str(tar1)

    tar2 = path_tar / "hans" / "peter" / "a.txt"
    assert str(pl.get_target_path(pl.get_raw_data_list()[1])) == str(tar2)
