#!/opt/homebrew/bin/python3.9
from pathlib import Path
import re

idir = Path('output')
odir = Path('pdf')


def convert_file(text):
    text = re.sub(r'\\c ', '= Pasal ', text)
    text = re.sub(r'\\s ', '== ', text)
    text = re.sub(r'\\p\s?',r'\n\n', text)
    text = re.sub(r'\\v (\d+)', r'#super[\1]', text)
    text = re.sub(r'\\q(\d*)(.*)', r'\n#pad(left: 2 * \1pt)[\2]', text).replace('2 * pt', '2pt') 
    return text



if __name__ == '__main__':
    for file in idir.glob('*.SFM'):
        out_name = str(file.name)
        text = convert_file(file.read_text())
        Path(odir / Path(out_name.replace('.SFM', '.typ'))).write_text(text)

    print("DONE")
