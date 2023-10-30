#!/opt/homebrew/bin/python3.9
import cartonml as carton
import numpy as np
from pathlib import Path
import re


# {'source_language': array(['Hindi', 'Chinese'], dtype='<U7'), 
# 'target_language': array(['French', 'English'], dtype='<U7'), 
# 'input': array([['जीवन एक चॉकलेट बॉक्स की तरह है।'],
#        ['生活就像一盒巧克力。']], dtype='<U31')}

# A permalink to the model
MODEL_URL = "https://carton.pub/facebook/m2m100_418M/69c5e31a5a0ff6d2719afe677dbe57022828789a5c2e586a5b66d2fc37cddb07"


def clean_results(text):
    output = []
    if not text.strip():
        return ''
    # for l in text.split('\n'):
    for l in text:
        line = l.strip()
        if not line:
            output.append('')
        if line.startswith('P '):
            output.append('\\p ' + line.replace('P ', ''))
        elif line.startswith('c ') or line.startswith('C '):
            output.append('\\c ' + line.replace('c ', '').replace('C ', ''))
        elif line[0] in "1234567890":
            output.append(re.sub(r'(\d+)\S)(.*)', r'\\v \1 \2', line).replace('  ', ' '))
        elif line[0] in ['Q']:
            output.append('\\q' + line[1:])
        else:
            output.append('\\s ' + line)

    return '\n'.join(output)


def pick_pronouns(text):
    return re.sub(r'\[neut\:[^|]+\|([^\]]+)\]', r'\1', text).replace('masc:', '')


def pick_spelling(text):
    return re.sub(r'\[us\:([^|]+)\|[^\]]+\]', r'\1', text)


def replace_tags(text):
    return text.replace('\\', 'MARKER')


def chunk_chapters(text):
    return text.replace('\\c ', '@@\\c ').split('@@')


def clean_extra_markers(text):
    text = text.replace('\\wj*', '').replace('\\wj', '')
    return text

def prep_text(iname):
    return chunk_chapters(clean_extra_markers(pick_spelling(iname.read_text())))


def clean_results2(text):
    text = re.sub(r'([0-9 ]+)(\S)', r'\1 \2', text).replace('  ', ' ')
    return text


async def main():
    # Load the model
    source_dir = Path('./Open-English-Bible-master/source/')
    odir = Path('output')
    # io = (source_dir / Path('41-Mark.usfm.db'), odir/ Path('41OIBMRK.SFM'))
    io = (source_dir / Path('62-1 John.usfm.db'), odir/ Path('62OIB1JN.SFM'))
    if not io[0].is_file():
        print("Input file doesn't exist")
        exit()
    model = await carton.load(MODEL_URL)
    sl = np.array(['English'])
    tl = np.array(['Indonesian'])
       # input_text = np.array([['Good morning. Can I have some coffee please?', "I'd like an Americano. Black. No Sugar"]])
    # Set up inputs
    # inputs = {
    #    "source_language": await model.info.examples[0].inputs["source_language"].get(),
    #    "target_language": await model.info.examples[0].inputs["target_language"].get(),
    #    "input": await model.info.examples[0].inputs["input"].get(),
    # }
    output = []
    raw_out = []
    for chapter in prep_text(io[0])[1:]:
        cpt = []
        for line in pick_pronouns(chapter).split('\n'):
            parts = line.strip().split(' ', maxsplit=1)
            if len(parts) < 2:
                cpt.append(' '.join(parts))
            else:
                if not parts[0].startswith('\\'):
                    parts[1] = parts[0] + ' ' + parts[1]
                input_text = np.array([parts[1]])
                inputs = {'source_language': sl, "target_language": tl, "input": input_text}

                # Run the model
                results = await model.infer(inputs)
                #raw = results['output'][0]
                #raw_out.append('\n'.join(raw))
                #res = clean_results(raw)
                if not parts[0].startswith('\\'):
                    cpt.append(clean_results2(results['output'][0]).replace('  ', ' '))
                else:
                    cpt.append((parts[0] + ' ' + clean_results2(results['output'][0])).replace('  ', ' '))
            print(cpt[-1])
        output.append('\n'.join(cpt))
    io[1].write_text('\n\n'.join(output))
    Path('raw.txt').write_text('\n\n'.join(raw_out))

    # Print the expected results
    # print({
    #    "output": await model.info.examples[0].sample_out["output"].get(),
    # })


import asyncio
asyncio.run(main())
