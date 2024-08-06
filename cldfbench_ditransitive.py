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
        for sheet_path in self.raw_dir.glob('*.xlsx'):
            self.raw_dir.xlsx2csv(sheet_path.name)
            self.raw_dir.joinpath(f'{sheet_path.stem}.Sheet1.csv').rename(
                sheet_path.with_suffix('.csv'))

    def cmd_readme(self, args):
        section_header = (
            'Ditransitrive Constructions\n'
            '===========================\n'
            '\n')
        section_content = self.raw_dir.read('intro.md')
        return f'{section_header}\n{section_content}'

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        config = ditrans2cldf.load_config_file(self.etc_dir / 'config.json')
        map_icons = {
            row['ID']: row
            for row in self.etc_dir.read_csv('map-icons.csv', dicts=True)
            if row.get('Map_Icon')}

        raw_data = ditrans2cldf.load_csv_data(self.raw_dir)

        cldf_data = ditrans2cldf.make_cldf_tables(raw_data, config)

        ditrans2cldf.add_custom_columns(args.writer.cldf, config)
        args.writer.cldf.add_sources(
            ditrans2cldf.make_bibliography(cldf_data['references']))

        # FIXME: I need a better story for map icons
        for code in cldf_data['lcodes']:
            if (map_icon := map_icons.get(code['ID'])):
                assert map_icon['Name'] == code['Name'], (
                    'map icon {}: code value changed from {} to {}'.format(
                        code['ID'], map_icon['Name'], code['Name']))
                assert map_icon['Parameter_ID'] == code['Parameter_ID'], (
                    'map icon {}: parameter changed from {} to {}'.format(
                        code['ID'], map_icon['Parameter_ID'], code['Parameter_ID']))
                code['Map_Icon'] = map_icon['Map_Icon']

        args.writer.cldf.add_columns('CodeTable', 'Map_Icon')

        args.writer.objects['LanguageTable'] = cldf_data['languages']
        args.writer.objects['constructions.csv'] = cldf_data['constructions']
        args.writer.objects['ParameterTable'].extend(cldf_data['lparameters'])
        args.writer.objects['ParameterTable'].extend(cldf_data['cparameters'])
        args.writer.objects['CodeTable'].extend(cldf_data['lcodes'])
        args.writer.objects['CodeTable'].extend(cldf_data['ccodes'])
        args.writer.objects['ValueTable'] = cldf_data['lvalues']
        args.writer.objects['cvalues.csv'] = cldf_data['cvalues']
        args.writer.objects['ExampleTable'] = cldf_data['examples']
