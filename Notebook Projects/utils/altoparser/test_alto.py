import os
import unittest
import alto
import configparser


ENV = 'DEV'
config = configparser.ConfigParser()
config.read('/opt/app/ap/config.ini')


class AltoTestCase(unittest.TestCase):
    def setUp(self):
        factory = alto.AltoFactory(os.path.join(config['DEV']['SAMPLES_PATH']))
        xml_files = factory.load_files(['b13797_0016.xml'])
        self.alto_file = xml_files[0]

    def test_measurement_unit(self):
        self.assertEqual(self.alto_file.description.measurement_unit, 'mm10d',
                         'incorrect measurement unit')

    def test_filename(self):
        self.assertEqual(self.alto_file.description.source_image_information.filename, '../SCREEN/b13797_0016.jpg',
                         'incorrect filename')

    def test_file_identifiers(self):
        self.assertEqual(self.alto_file.description.source_image_information.file_identifiers[0].text, '1872802',
                         'incorrect file file identifiers')


if __name__ == '__main__':
    unittest.main()
