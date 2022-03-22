import dclab
import dclab.cli


from ..recipe import Recipe


class RTDCRecipe(Recipe):
    def convert_dataset(self, path_list, temp_path):
        """Compress the dataset using dclab"""
        # first compress the .rtdc file
        dclab.cli.compress(path_out=temp_path, path_in=path_list[0])
        # the rest of the files should be log files
        if len(path_list) > 1:
            with dclab.RTDCWriter(temp_path) as hw:
                for pp in path_list[1:]:
                    lines = pp.read_text.split("\n")
                    lines = [ll.rstrip() for ll in lines]
                    hw.store_log(pp.name, lines)

    def get_raw_data_list(self):
        """Get list of .rtdc files including associated files"""
        raw_data_paths = []
        for pp in self.path_raw.rglob("*.rtdc"):
            path_list = [pp]
            # search for matching SoftwareSettings.ini files
            if pp.name.startswith("M"):
                pini = pp.with_name(
                    pp.name.split("_")[0]+"_SoftwareSettings.ini")
                if pini.exists():
                    path_list.append(pini)
            raw_data_paths.append(path_list)
        return raw_data_paths
