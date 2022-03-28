import pathlib
import tempfile
import zipfile


def retrieve_data(zip_file):
    """Extract contents of data zip file and return data files
    """
    zpath = pathlib.Path(__file__).resolve().parent / "data" / zip_file
    # unpack
    arc = zipfile.ZipFile(str(zpath))

    # extract all files to a temporary directory
    edest = tempfile.mkdtemp(prefix=zpath.name)
    arc.extractall(edest)
    return pathlib.Path(edest)
