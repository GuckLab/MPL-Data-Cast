import numpy as np

from helper import retrieve_data

from mpl_data_cast.mod_recipes import RTDCRecipe

import dclab


def test_pipeline_cast_convert_error(tmp_path):
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    name = "M002_data.rtdc"
    (path_in / name).touch()  # an invalid rtdc file

    rcp = RTDCRecipe(path_raw=path_in, path_tar=tmp_path)
    result = rcp.cast()
    assert not result["success"]
    assert len(result["errors"]) == 1
    assert name in str(result["errors"][0][0])
    assert not (tmp_path / name).exists()


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


def test_rcp_rtdc_with_other_files(tmp_path):
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    # an additional file that should be copied
    (path_in / "additional.docx").touch()

    rcp = RTDCRecipe(path_raw=path_in, path_tar=tmp_path)
    rcp.cast()

    assert (tmp_path / "additional.docx").exists()
