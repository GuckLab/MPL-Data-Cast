import h5py

import re


def is_valid_h5_file(path):
    try:
        with h5py.File(path):
            valid = True
    except BaseException:
        valid = False
    return valid


def h5_file_contains(path, location="/", attribute=None, verifier=None,
                     regexp=None):
    """Check whether the HDF5 file contains certain attributes or datastes

    Parameters
    ----------
    path: str or pathlib.Path
        path to the HDF5 file
    location: str
        location in the HDF5 structure (can be a dataset or a group)
    attribute: str
        the attribute to check
    verifier: callable
        function to check against
    regexp: str
        regular expression pattern to check against (redundant to verifier)
        using `re.fullmatch(regexp, str(h5[location].attrs[attribite]))`
    """
    contains = False
    with h5py.File(path) as h5:
        if location in h5:
            loc = h5[location]
            if attribute is None:
                # we are only checking for a location
                contains = True
                if verifier is not None:
                    raise ValueError(
                        "`verifier` specified without `attribute`!")
                if regexp is not None:
                    raise ValueError(
                        "`regexp` specified without `attribute`!")
            if attribute is not None and attribute in loc.attrs:
                attr = loc.attrs[attribute]
                if verifier is not None:
                    verified = verifier(attr)
                else:
                    verified = True
                if regexp is not None:
                    matched = re.fullmatch(regexp, str(attr)) is not None
                else:
                    matched = True
                contains = verified and matched
    return contains
