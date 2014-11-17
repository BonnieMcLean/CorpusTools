import os
import re

from corpustools.corpus.classes import SpontaneousSpeechCorpus

phone_file_extensions = ['phones','phn']
word_file_extensions = ['words','wrd']


FILLERS = set(['uh','um','okay','yes','yeah','oh','heh','yknow','um-huh',
                'uh-uh','uh-huh','uh-hum','mm-hmm'])

def inspect_directory(directory):
    #directory = corpus.directory

    for root, subdirs, files in os.walk(directory):
        print("loop\n")
        print(root,subdirs,files)

def import_spontaneous_speech_corpus(name,directory):
    corpus = SpontaneousSpeechCorpus(name,directory)

    dialogs = {}
    words = []
    phones = []
    for root, subdirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.words'):
                words.append(os.path.join(root,f))
            elif f.endswith('.phones'):
                phones.append(os.path.join(root,f))
    for p in words:
        name = os.path.splitext(os.path.split(p)[1])[0]
        for p2 in phones:
            if name == os.path.splitext(os.path.split(p2)[1])[0]:
                dialogs[name] = (p,p2)
                break
    for d, v in dialogs.items():
        data = files_to_data(*v)
        discourse_info = {'identifier':d,
                            }
        corpus.add_discourse(data, discourse_info)
    return corpus

def phone_match(one,two):
    if one != two and one not in two:
        return False
    return True

def files_to_data(word_path,phone_path):
    words = load_words(word_path)
    phones = load_phones(phone_path)
    for i, w in enumerate(words):
        if w['ur'] is None:
            continue
        expected = w['sr']
        beg = w['begin']
        end = w['end']
        found = []
        while len(found) < len(expected):
            cur_phone = phones.pop(0)
            if phone_match(cur_phone['label'],expected[len(found)]) \
                and cur_phone['end'] >= beg and cur_phone['begin'] <= end:
                    found.append(cur_phone)
            if not len(phones) and i < len(words)-1:
                print(name)
                print(w)
                raise(Exception)
        words[i]['phones'] = found
        words[i]['begin'] = found[0]['begin']
        words[i]['end'] = found[-1]['end']
    return words

def load_phones(path):
    with open(path,'r') as file_handle:
        f = re.split("#\r{0,1}\n",file_handle.read())[1]
        flist = f.splitlines()
        phones =[]
        begin = 0.0
        for l in flist:
            line = re.split("\s+\d{3}\s+",l.strip())
            end = float(line[0])
            label = re.split(" {0,1};| {0,1}\+",line[1])[0]
            phones.append({'label':label,'begin':begin,'end':end})
            begin = end
    return phones

def load_words(path):
    with open(path,'r') as file_handle:
        f = re.split(r"#\r{0,1}\n",file_handle.read())[1]
        words = []
        begin = 0.0
        flist = f.splitlines()
        for l in flist:
            line = re.split("; | \d{3} ",l.strip())
            end = float(line[0])
            word = line[1]
            if word[0] != "<" and word[0] != "{":
                citation = line[2].split(' ')
                phonetic = line[3].split(' ')
                category = line[4]
            else:
                citation = None
                phonetic = None
                category = None
            if word in FILLERS:
                category = 'UH'
            line = {'word':word,'begin':begin,'end':end,'ur':citation,'sr':phonetic,'category':category}
            words.append(line)
            begin = end
    return words

def validate_data(words,name):
    for i, w in enumerate(words):
        if i > 0:
            prev = words[i-1]
            if prev['End'] > w['Begin']:
                if w['UR'] != 'NULL':
                    if prev['UR'] != 'NULL':
                        print(name)
                        print(prev)
                        print(w)
                        raise(Exception)
                else:
                    words[i]['Begin'] = prev['End']


        if i < len(words)-1:
            foll = words[i+1]
            if foll['Begin'] < w['End']:
                if w['UR'] != 'NULL':
                    if foll['UR'] != 'NULL':
                        print(name)
                        print(foll)
                        print(w)
                        raise(Exception)
                else:
                    words[i]['End'] = foll['Begin']
        try:
            cat = Category.objects.get(Label=w['Category'])
        except Exception:
            print(name)
            print(foll)
            print(w)

            raise(Exception)
    return words
