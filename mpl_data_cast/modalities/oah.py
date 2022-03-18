import h5py

from ..helper import is_valid_h5_file, h5_file_contains
from ..pipeline import Pipeline


class DHMPipeline(Pipeline):
    """Matlab file format (TopogMap.mat) for DHM data"""

    def convert_dataset(self, path_list, temp_path):
        """Convert DHM .mat data to qpformat HDF5 format"""
        with h5py.File(path_list[0]) as mat, h5py.File(temp_path, "w") as h5:
            topog = mat["topogMap"][:]
            # make sure we have a 3D stack
            if len(topog.shape) == 2:
                topog.reshape(1, topog.shape[0], -1)
            for ii in range(topog.shape[0]):
                ds = h5.create_dataset(
                    name=str(ii),
                    chunks=topog[ii].shape,
                    data=topog[ii],
                    fletcher32=True,
                )
                ds.attrs["numerical aperture"] = mat["NA"][:].item()
                ds.attrs["wavelength"] = mat["lambda"][:].item() * 1e-6
                ds.attrs["pos x"] = mat["positionVal"][0].item() * 1e-6
                ds.attrs["pos y"] = mat["positionVal"][1].item() * 1e-6
                ds.attrs["focus"] = mat["positionVal"][2].item() * 1e-6
                ds.attrs["pixel size"] = mat["res"][:].item() * 1e-6
                ds.attrs["medium index"] = 1.333
                if "frameRate" in mat:
                    dt = 1 / mat["frameRate"][:].item()
                    ds.attrs["time"] = ii * dt

    def get_raw_data_list(self):
        datalist = []
        for pp in sorted(self.path_raw.rglob("*.mat")):
            if (is_valid_h5_file(pp)
                and h5_file_contains(pp, "topogMap")
                and h5_file_contains(pp, "res")
                    and h5_file_contains(pp, "lambda")):
                datalist.append([pp])
        return datalist
