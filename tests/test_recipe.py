import hashlib
import pathlib
import tempfile

from mpl_data_cast import Recipe


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


class DummyRecipe(Recipe):
    """A pipeline that just concatenates text files"""

    def convert_dataset(self, path_list, temp_path, **kwargs):
        data = ""
        for pp in path_list:
            data += pp.read_text()
        temp_path.write_text(data)

    def get_raw_data_iterator(self):
        """Return a sorted list of files"""
        data_list = []
        for pp in self.path_raw.rglob("*"):
            if pp.is_dir():
                files = sorted(pp.rglob("*.txt"))
                if files:
                    data_list.append(files)
        return sorted(data_list)


def test_pipeline_init():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    pl = DummyRecipe(path_raw, path_tar)
    assert pl.tempdir.exists()
    assert pl.format == "DummyRecipe"
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


def test_pipeline_cast_delete_after():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    pl = DummyRecipe(path_raw, path_tar)
    input_list = sorted(pl.get_raw_data_iterator())
    output_list = [pl.get_target_path(pi) for pi in input_list]
    for po in output_list:
        assert not po.exists()
    ret = pl.cast()
    assert ret["success"]
    for po in output_list:
        assert po.exists()
    # This is the actual important test. The instance should remove
    # temporary files as it transfers them.
    temp_files = sorted(pl.tempdir.rglob("*.txt"))
    assert len(temp_files) == 0


def test_pipeline_get_target_path():
    path_raw = make_example_data()
    path_tar = pathlib.Path(tempfile.mkdtemp()) / "test"
    path_tar.mkdir()
    pl = DummyRecipe(path_raw, path_tar)

    tar1 = path_tar / "fliege" / "1.txt"
    assert str(pl.get_target_path(pl.get_raw_data_iterator()[0])) == str(tar1)

    tar2 = path_tar / "hans" / "peter" / "a.txt"
    assert str(pl.get_target_path(pl.get_raw_data_iterator()[1])) == str(tar2)


def test_transfer_to_target_path_basic(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    assert Recipe.transfer_to_target_path(temp_path=pin,
                                          target_path=pout)
    assert pin.read_text() == pout.read_text() == "peter"


def test_transfer_to_target_path_check_existing(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    pout.write_text("hans")
    assert Recipe.transfer_to_target_path(temp_path=pin,
                                          target_path=pout,
                                          check_existing=True,
                                          )
    assert pin.read_text() == pout.read_text() == "peter"


def test_transfer_to_target_path_check_existing_file_size(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    pout.write_text("hans")  # has different file size -> deleted
    assert Recipe.transfer_to_target_path(temp_path=pin,
                                          target_path=pout,
                                          check_existing=False,
                                          )
    assert pin.read_text() == "peter"
    assert pout.read_text() == "peter"


def test_transfer_to_target_path_check_existing_control(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    pout.write_text("hanse")  # must have same size
    assert Recipe.transfer_to_target_path(temp_path=pin,
                                          target_path=pout,
                                          check_existing=False,
                                          )
    assert pin.read_text() == "peter"
    assert pout.read_text() == "hanse"


def test_transfer_to_target_path_delete_after(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    assert Recipe.transfer_to_target_path(temp_path=pin,
                                          target_path=pout,
                                          delete_after=True,
                                          )
    assert pout.read_text() == "peter"
    assert not pin.exists()


def test_transfer_to_target_path_hash_input(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    assert Recipe.transfer_to_target_path(
        temp_path=pin,
        target_path=pout,
        hash_input=hashlib.md5(b"peter").hexdigest())
    assert pout.read_text() == "peter"


def test_transfer_to_target_path_hash_input_control(tmp_path):
    pin = tmp_path / "test.txt"
    pin.write_text("peter")
    pout = tmp_path / "out.txt"
    assert not Recipe.transfer_to_target_path(
        temp_path=pin,
        target_path=pout,
        hash_input=hashlib.md5(b"hans").hexdigest())
    assert pin.exists()
    assert pin.read_text() == "peter"
    assert not pout.exists()
