import pathlib
import re
from itertools import chain

from cldfbench import Dataset as BaseDataset
import ditrans2cldf


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "malchukovditransitives"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return ditrans2cldf.cldfspec(self.cldf_dir)

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        csvdir = self.raw_dir / 'csv'
        csvdir.mkdir(parents=True, exist_ok=True)
        for sheet_path in self.raw_dir.glob('*.xlsx'):
            tmpfile = csvdir / f'{sheet_path.stem}.Sheet1.csv'
            outfile = csvdir / f'{sheet_path.stem}.csv'
            # will write to tmpfile
            self.raw_dir.xlsx2csv(sheet_path.name, outdir=csvdir)
            self.raw_dir.joinpath(tmpfile).rename(outfile)

    def cmd_readme(self, args):
        section_header = (
            'Ditransitive Constructions\n'
            '==========================\n'
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
        topics = {
            row['Parameter_ID']: row
            for row in self.etc_dir.read_csv('topics.csv', dicts=True)}

        raw_data = ditrans2cldf.load_csv_data(self.raw_dir / 'csv')

        cldf_data = ditrans2cldf.make_cldf_tables(raw_data, config)

        ditrans2cldf.add_custom_columns(args.writer.cldf, config)
        args.writer.cldf.add_sources(
            ditrans2cldf.make_bibliography(cldf_data['references']))

        for parameter in chain(cldf_data['lparameters'], cldf_data['cparameters']):
            if (topic := topics.get(parameter['ID'])):
                assert topic['Parameter_Name'] == parameter['Name'], \
                    'parameter {}: parameter changed from {} to {}'.format(
                        parameter['ID'], topic['Parameter_Name'], parameter['Name'])
                assert topic['Grammacodes']
                parameter['Grammacodes'] = re.split(r'\s*,\s*', topic['Grammacodes'])

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
        args.writer.cldf.add_columns(
            'ParameterTable',
            {
                'name': 'Grammacodes',
                'datatype': 'string',
                'separator': ';',
                'dc:extent': 'multivalued',
            })

        args.writer.objects['LanguageTable'] = cldf_data['languages']
        args.writer.objects['constructions.csv'] = cldf_data['constructions']
        args.writer.objects['ParameterTable'].extend(cldf_data['lparameters'])
        args.writer.objects['ParameterTable'].extend(cldf_data['cparameters'])
        args.writer.objects['CodeTable'].extend(cldf_data['lcodes'])
        args.writer.objects['CodeTable'].extend(cldf_data['ccodes'])
        args.writer.objects['ValueTable'] = cldf_data['lvalues']
        args.writer.objects['cvalues.csv'] = cldf_data['cvalues']
        args.writer.objects['ExampleTable'] = cldf_data['examples']
