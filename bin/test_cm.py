import os
import sys
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from corpustools.corpus.classes.lexicon import Word
from corpustools.corpus.io.binary import load_binary as lb
from corpustools.symbolsim.string_similarity import string_similarity as ss
from corpustools.contextmanagers import *

corpus_name = 'Speakers'
corpus = lb('C:\\Users\\Michael\\Documents\\PCT\\CorpusTools\\CORPUS\\' + corpus_name + '.corpus')
outf_name = 'C:\\Users\\Michael\\Desktop\\' + corpus_name + '_test_out.txt'


with CanonicalVariantContext(getattr(corpus, 'lexicon'), 'transcription', 'type') as c:
    counter = 0
    for word in c:
        counter += 1
        """
        if word.spelling == 'nata':
            w1 = word
        if word.spelling == 'mata':
            w2 = word
        """
    print(counter)
            
    #a = ss(c, (w1, w2), 'khorsi')
    #print(a)


with SeparatedTokensVariantContext(getattr(corpus, 'lexicon'), 'transcription', 'type') as c:
    counter = 0
    for word in c:
        counter += 1
    print(counter)
