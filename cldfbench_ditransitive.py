import pathlib

from cldfbench import Dataset as BaseDataset
import ditrans2cldf


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "ditransitive"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return ditrans2cldf.cldfspec(self.cldf_dir)

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        pass

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        config = ditrans2cldf.load_config_file(self.etc_dir / 'config.json')

        excel_data = ditrans2cldf.load_excel_data(self.raw_dir)

        cldf_data = ditrans2cldf.excel2cldf(excel_data, config)

        # for now drop the examples with missing language ids
        # TODO: fix this upstream
        cldf_data['examples'] = [
            example
            for example in cldf_data['examples']
            if example.get('Language_ID')]

        ditrans2cldf.add_custom_columns(args.writer.cldf, config)
        args.writer.cldf.add_sources(
            ditrans2cldf.make_bibliography(cldf_data['references']))

        args.writer.objects['LanguageTable'] = cldf_data['languages']
        args.writer.objects['constructions.csv'] = cldf_data['constructions']
        args.writer.objects['ParameterTable'].extend(cldf_data['lparameters'])
        args.writer.objects['ParameterTable'].extend(cldf_data['cparameters'])
        args.writer.objects['CodeTable'].extend(cldf_data['lcodes'])
        args.writer.objects['CodeTable'].extend(cldf_data['ccodes'])
        args.writer.objects['ValueTable'] = cldf_data['lvalues']
        args.writer.objects['cvalues.csv'] = cldf_data['cvalues']
        args.writer.objects['ExampleTable'] = cldf_data['examples']
