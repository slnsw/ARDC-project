#!/usr/bin/env python3
"""main."""

import sys
import os
import configparser
import alto

ENV = 'DEV'
config = configparser.ConfigParser()
config.read('/opt/app/ap/config.ini')


def main():
    """main."""
    error_status = 0

    factory = alto.AltoFactory(os.path.join(config['DEV']['SAMPLES_PATH']))
    xml_files = factory.load_files(['b13797_0016.xml', 'b13797_0158.xml'])

    for xml_file in xml_files:
        print('\n\n******Page******: ' + xml_file.layout.pages[0].id + '\n\n')
        for block in xml_file.layout.pages[0].print_space:
            if type(block) == alto.TextBlock:
                for line in block:
                    for line_part in line:
                        if type(line_part) == alto.String:
                            print(line_part.content, end='')
                        elif type(line_part) == alto.Sp:
                            print(' ', end='')
            elif type(block) == alto.ComposedBlock:
                for block in block:
                    if type(block) == alto.TextBlock:
                        for line in block:
                            for line_part in line:
                                if type(line_part) == alto.String:
                                    print(line_part.content, end='')
                                elif type(line_part) == alto.Sp:
                                    print(' ', end='')
                            print('')

    return error_status


if __name__ == '__main__':
    sys.exit(main())
