import re
import os
import string
import logging

from corpustools.corpus.classes import Discourse, Attribute, Corpus, Word, WordToken, Transcription
from corpustools.exceptions import DelimiterError

NUMBER_CHARACTERS = set(string.digits)

class BaseAnnotation(object):
    def __init__(self, label = None, begin = None, end = None):
        self.label = label
        self.begin = begin
        self.end = end
        self.stress = None
        self.tone = None
        self.group = None

    def __iter__(self):
        return iter(self.label)

    def __repr__(self):
        return '<BaseAnnotation "{}" from {} to {}>'.format(self.label,
                                                            self.begin,
                                                            self.end)
    def __eq__(self, other):
        return self.label == other.label and self.begin == other.begin and self.end == other.end

class Annotation(BaseAnnotation):
    def __init__(self, label = None):
        self.label = label
        self.begins = []
        self.ends = []
        self.references = []
        self.token = {}
        self.additional = {}

    def __eq__(self, other):
        return self.label == other.label and self.begins == other.begins \
                and self.ends == other.ends

    def __repr__(self):
        return '<Annotation "{}">'.format(self.label)

    def __hash__(self):
        return self.ouput_name+str(self.begins)

class AnnotationType(object):
    """
    AnnotationTypes represent information found in a corpus column.
    Base annotations are transcriptions/tiers
    Anchor annotations are spelling
    """
    def __init__(self, name, subtype, supertype, attribute = None, anchor = False,
                    token = False, base = False, speaker = None, is_default = False,):
        self.characters = set()
        self.ignored_characters = set()
        self.digraphs = set()
        self.trans_delimiter = None
        self.morph_delimiters = set()
        self.number_behavior = None
        self._list = [] #This list contains Annotations for spelling and BaseAnnotations for transcriptions
        self.name = name
        #This variable name is confusing - it represents something like "Orthography" or "Transcription", rather than
        #the name that the user would have given to the column, e.g. "canonical_pron" or "Spelling"
        #to get the user's preferred name, look self.output_name, or self.attribute
        self.subtype = subtype
        self.supertype = supertype
        self.token = token
        self.base = base #base is transcription/tier type
        self.anchor = anchor #anchor is spelling type
        self.speaker = speaker
        self.ignored = False
        self.is_default = is_default
        if self.speaker is not None:
            self.output_name = re.sub('{}\W*'.format(self.speaker),'',self.name)
        else:
            self.output_name = self.name
        if attribute is None:
            if base:
                self.attribute = Attribute(Attribute.sanitize_name(name), 'tier', name, is_default=is_default)
            else:
                self.attribute = Attribute(Attribute.sanitize_name(name), 'spelling', name, is_default=is_default)
        else:
            self.attribute = attribute

    def pretty_print(self):
        string = ('{}:\n'.format(self.name) +
                '    Ignored characters: {}\n'.format(', '.join(self.ignored_characters)) +
                '    Digraphs: {}\n'.format(', '.join(self.digraphs)) +
                '    Transcription delimiter: {}\n'.format(self.trans_delimiter) +
                '    Morpheme delimiters: {}\n'.format(', '.join(self.morph_delimiters)) +
                '    Number behavior: {}\n'.format(self.number_behavior))
        return string

    def reset(self):
        self._list = []

    def __repr__(self):
        return '<AnnotationType "{}" with Attribute "{}">'.format(self.name,
                                                        self.attribute.name)

    def __str__(self):
        return self.name

    def __getitem__(self, key):
        return self._list[key]

    def add(self, annotations, save = True):
        for a in annotations:
            self.characters.update(a)
            if save or len(self._list) < 10:
                #If save is False, only the first 10 annotations are saved
                self._list.append(a)

    @property
    def delimited(self):
        if self.delimiter is not None:
            return True
        if self.digraphs:
            return True
        return False

    def __iter__(self):
        for x in self._list:
            yield x

    def __len__(self):
        return len(self._list)

    @property
    def digraph_pattern(self):
        if len(self.digraphs) == 0:
            return None
        return compile_digraphs(self.digraphs)

    @property
    def punctuation(self):
        return self.characters & set(string.punctuation)

    @property
    def delimiter(self):
        return self.trans_delimiter

    @property
    def is_word_anchor(self):
        return not self.token and self.anchor

    @property
    def is_token_base(self):
        return self.token and self.base

    @property
    def is_type_base(self):
        return not self.token and self.base

class DiscourseData(object):
    def __init__(self, name, levels):
        self.name = name
        self.data = {x.attribute.name: x for x in levels}
        self.wav_path = None

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, item):
        return item in self.data

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def mapping(self):
        return { x.attribute.name: x.attribute for x in self.data.values() if not x.ignored}

    def collapse_speakers(self):
        newdata = {}
        shifts = {self.data[x].output_name: 0 for x in self.base_levels}
        #Sort keys by speaker, then non-base levels, then base levels

        keys = list()
        speakers = sorted(set(x.speaker for x in self.data.values() if x.speaker is not None))
        for s in speakers:
            base = []
            for k,v in self.data.items():
                if v.speaker != s:
                    continue
                if v.base:
                    base.append(k)
                else:
                    keys.append(k)
            keys.extend(base)
        for k in keys:
            v = self.data[k]
            name = v.output_name
            if name not in newdata:
                subtype = v.subtype
                supertype = v.supertype
                if subtype is not None:
                    subtype = self.data[subtype].output_name
                if supertype is not None:
                    supertype = self.data[supertype].output_name
                newdata[v.output_name] = AnnotationType(v.output_name, subtype, supertype,
                    anchor = v.anchor,token = v.token, base = v.base,
                    delimited = v.delimited)
            for ann in v:
                newann = dict()
                for k2,v2 in ann.items():
                    try:
                        newk2 = self.data[k2].output_name
                        newv2 = (v2[0]+shifts[newk2],v2[1]+shifts[newk2])

                    except KeyError:
                        newk2 = k2
                        newv2 = v2
                    newann[newk2] = newv2

                newdata[v.output_name].add([newann])
            if v.base:
                shifts[v.output_name] += len(v)
        self.data = newdata

    @property
    def token_levels(self):
        levels = []
        for k in self.data.keys():
            if self.data[k].token:
                levels.append(k)
        return levels

    @property
    def word_levels(self):
        levels = []
        for k in self.data.keys():
            if self.data[k].is_word_anchor:
                levels.append(k)
        return levels

    @property
    def base_levels(self):
        levels = []
        for k in self.data.keys():
            if self.data[k].base:
                levels.append(k)
        return levels

    def add_annotations(self,**kwargs):
        for k,v in kwargs.items():
            self.data[k].add(v)

    def level_length(self, key):
        return len(self.data[key])

def get_corpora_list(storage_directory):
    corpus_dir = os.path.join(storage_directory,'CORPUS')
    corpora = [parse_filename(x) for x in os.listdir(corpus_dir)]
    return corpora

def get_systems_list(storage_directory):
    system_dir = os.path.join(storage_directory,'FEATURE')
    systems = [x.split('.')[0] for x in os.listdir(system_dir) if x.endswith('.feature')]
    return systems

def parse_filename(filename):
    filename = filename.split('.')
    if len(filename) > 2:
        filename = '.'.join(filename[:-1])
    else:
        filename = filename[0]
    return filename

def corpus_name_to_path(storage_directory,name):
    return os.path.join(storage_directory,'CORPUS',name+'.corpus')

def compile_digraphs(digraph_list):
    digraph_list = sorted(digraph_list, key = lambda x: len(x), reverse=True)
    pattern = '|'.join(re.escape(d) for d in digraph_list)
    pattern += '|\d+|\S'
    return re.compile(pattern)

def inspect_directory(directory):
    types = ['textgrid', 'text', 'multiple']
    counter = {x: 0 for x in types}
    relevant_files = {x: [] for x in types}
    for root, subdirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[-1].lower()
            if ext == '.textgrid':
                t = 'textgrid'
            elif ext == '.txt':
                t = 'text'
            elif ext in ['.words','.wrds']:
                t = 'multiple'
            else:
                continue
            counter[t] += 1
            relevant_files[t].append(f)
    max_value = max(counter.values())
    for t in ['textgrid', 'multiple', 'text']:
        if counter[t] == max_value:
            likely_type = t
            break

    return likely_type, relevant_files

parse_numbers = re.compile('\d+|\S')

def parse_transcription(string, annotation_type):
    md = annotation_type.morph_delimiters
    if len(md) and any(x in string for x in md):
        morphs = re.split("|".join(md),string)
        transcription = []
        for i, m in enumerate(morphs):
            trans = parse_transcription(m, annotation_type)
            for t in trans:
                t.group = i
            transcription += trans
        return transcription
    ignored = annotation_type.ignored_characters

    if ignored is not None:
        string = ''.join(x for x in string if x not in ignored)

    if annotation_type.trans_delimiter is None:
        if annotation_type.digraph_pattern is not None:
            string = annotation_type.digraph_pattern.findall(string)
        else:
            string = [x for x in string]
    elif annotation_type.trans_delimiter is not None:
        string = string.split(annotation_type.trans_delimiter)
    else:
        string = parse_numbers.findall(string)
    final_string = []
    for seg in string:
        if seg == '':
            continue
        num = None
        if annotation_type.number_behavior is not None:
            if annotation_type.number_behavior == 'stress':
                num = ''.join(x for x in seg if x in NUMBER_CHARACTERS)
                seg = ''.join(x for x in seg if x not in NUMBER_CHARACTERS)
            elif annotation_type.number_behavior == 'tone':
                num = ''.join(x for x in seg if x in NUMBER_CHARACTERS)
                seg = ''.join(x for x in seg if x not in NUMBER_CHARACTERS)
            if num == '':
                num = None
            if seg == '':
                setattr(final_string[-1],annotation_type.number_behavior, num)
                continue
        a = BaseAnnotation(seg)
        if annotation_type.number_behavior is not None and num is not None:
            setattr(a, annotation_type.number_behavior, num)
        final_string.append(a)
    return final_string

def text_to_lines(path):
    delimiter = None
    with open(path, encoding='utf-8-sig', mode='r') as f:
        text = f.read()
        if delimiter is not None and delimiter not in text:
            e = DelimiterError('The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise(e)
    lines = [x.strip().split(delimiter) for x in text.splitlines() if x.strip() != '']
    return lines

def find_wav_path(path):
    name, ext = os.path.splitext(path)
    wav_path = name + '.wav'
    if os.path.exists(wav_path):
        return wav_path
    return None

def log_annotation_types(annotation_types):
    logging.info('Annotation type info')
    logging.info('--------------------')
    logging.info('')
    for a in annotation_types:
        logging.info(a.pretty_print())

def data_to_discourse2(corpus_name=None, wav_path=None, annotation_types=None):
    curr_word = list()
    annotations = dict()
    spelling_name, transcription_name = None, None
    for at in annotation_types:
        annotations[at] = list()

        if at.name == 'Orthography (default)':
            spelling_name = at.output_name
        elif at.name == 'Transcription (default)':
            transcription_name = at.output_name

        if all(isinstance(item, Annotation) for item in at._list):
            # it's a list of spellings, take each one and add it to the overall annotations list
            for item in at._list:
                if item.label:
                    annotations[at].append((item.label, None, None))

        elif all(type(item) == BaseAnnotation for item in at._list):
            #it's a list of transcription, with each segment as a BaseAnnotation
            for item in at._list:
                if item.begin is not None:
                    begin = item.begin
                if item.end is None:
                    curr_word.append(item)
                elif item.end is not None:
                    end = item.end
                    curr_word.append(item)
                    curr_word = Transcription(curr_word)
                    annotations[at].append((curr_word, begin, end))
                    curr_word = list()
        else:
            raise TypeError("AnnotationType._list cannot contain a mix of Annotations and BaseAnnotations")


    if spelling_name is None:
        spelling_name = 'Spelling'
    if transcription_name is None:
        transcription_name = 'Transcription'
    discourse = Discourse(name=corpus_name, wav_path=wav_path,
                          spelling_name=spelling_name, transcription_name=transcription_name)

    if not 'frequency' in [a.name for a in discourse.lexicon.attributes]:
        # running text will not have a frequency attribute supplied by the user
        #textgrids are also unlikely to have this attribute
        discourse.lexicon.add_attribute(Attribute('frequency', 'numeric', 'Frequency'))
        add_frequency = True
    else:
        add_frequency = False

    ind = 0
    for n in range(len(list(annotations.values())[0])):
        word_kwargs = {at.output_name: (at.attribute, annotations[at][n][0]) for at in annotations if not at.token}
        word = Word(**word_kwargs)
        try:
            word = discourse.lexicon.find(word.spelling)
            if add_frequency:
                word.frequency += 1
        except KeyError:
            discourse.lexicon.add_word(word)
        for at in annotations:
            if at.output_name == spelling_name:
                continue
            word_token_kwargs = {at.output_name: (at.attribute, annotations[at][n][0])}
            word_token_kwargs['word'] = word
            begin = annotations[at][n][1]
            end = annotations[at][n][2]
            word_token_kwargs['begin'] = begin if begin is not None else ind
            word_token_kwargs['end'] = end if end is not None else ind + 1
            word_token = WordToken(**word_token_kwargs)
            discourse.add_word(word_token)
            if at.token:
                word.wordtokens.append(word_token)
        ind += 1

    return discourse

def data_to_discourse(data, lexicon = None, call_back=None, stop_check=None):
    attribute_mapping = data.mapping()
    spelling_name, transcription_name = None, None

    for name, value in attribute_mapping.items():
        if value.att_type == 'spelling' and value.is_default:
            spelling_name = name
        elif value.att_type == 'tier' and value.is_default:
            transcription_name = name


    d = Discourse(spelling_name = spelling_name, transcription_name = transcription_name,
                  name = data.name, wav_path = data.wav_path)
    ind = 0
    if lexicon is None:
        lexicon = d.lexicon #despite the name, this is a Corpus object

    for k,v in attribute_mapping.items():
        a = data[v.name]

        if a.token and v not in d.attributes:
            d.add_attribute(v, initialize_defaults = True)

        if not a.token and v not in d.lexicon.attributes:
            lexicon.add_attribute(v, initialize_defaults = True)


    if call_back is not None:
        call_back('Processing data...')
        cur = 0

    for level in data.word_levels:
        #word_levels is a list of spelling tiers, usually of length 1
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            call_back(cur)
        for i, s in enumerate(data[level]):
            #word_kwargs = {'spelling':(attribute_mapping[level], s.label)}
            if not s.label:
                continue
            word_kwargs = {level:(attribute_mapping[level], s.label)}
            word_token_kwargs = {}
            if s.token:# is not None:
                for token_key, token_value in s.token.items():
                    att = attribute_mapping[token_key]
                    word_token_kwargs[att.name] = (att, token_value)
            if s.additional is not None:
                for add_key, add_value in s.additional.items():
                    att = attribute_mapping[add_key]
                    if data[add_key].token:
                        word_token_kwargs[att.name] = (att, add_value)
                    else:
                        word_kwargs[att.name] = (att, add_value)
            for j, r in enumerate(s.references):
                if r in data and len(data[r]) > 0:
                    seq = data[r][s.begins[j]:s.ends[j]]
                    att = attribute_mapping[r]
                    if data[r].token:
                        word_token_kwargs[att.name] = (att, seq)
                        if len(seq) > 0 and seq[0].begin is not None:
                            word_token_kwargs['begin'] = seq[0].begin
                            word_token_kwargs['end'] = seq[-1].end

                    else:
                        word_kwargs[att.name] = (att, seq)

            word = lexicon.get_or_create_word(**word_kwargs)
            word_token_kwargs['word'] = word
            if 'begin' not in word_token_kwargs:
                word_token_kwargs['begin'] = ind
                word_token_kwargs['end'] = ind + 1
            wordtoken = WordToken(**word_token_kwargs)
            word.frequency += 1
            word.wordtokens.append(wordtoken)
            d.add_word(wordtoken)
            ind += 1
    return d