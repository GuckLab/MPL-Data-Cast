import numpy as np

from helper import retrieve_data

from mpl_data_cast.mod_recipes import RTDCRecipe

import dclab


def test_rcp_rtdc_base(tmp_path):
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")

    rcp = RTDCRecipe(path_raw=path_in, path_tar=tmp_path)
    rcp.cast()

    assert (path_in / "M001_SoftwareSettings.ini").exists()
    assert not (tmp_path / "M001_SoftwareSettings.ini").exists()

    pin = path_in / "M001_data.rtdc"
    pout = tmp_path / "M001_data.rtdc"

    with dclab.new_dataset(pin) as ds1, dclab.new_dataset(pout) as ds2:
        assert "M001_SoftwareSettings.ini" not in ds1.logs
        assert "M001_SoftwareSettings.ini" in ds2.logs
        assert np.all(ds1["deform"] == ds2["deform"])

    # Make sure compression worked (even with the ini file in it)
    assert pin.stat().st_size > pout.stat().st_size
