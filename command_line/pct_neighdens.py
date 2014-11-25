import argparse
import os
import csv

from corpustools.corpus.io.binary import load_binary
from corpustools.neighdens.neighborhood_density import neighborhood_density


#### Parse command-line arguments
parser = argparse.ArgumentParser(description = \
         'Phonological CorpusTools: neighborhood density CL interface')
parser.add_argument('corpus_file_name', help='Name of corpus file')
parser.add_argument('query', help='Name of word to query')
parser.add_argument('-s', '--string_type', default = 'transcription', help="If 'spelling', will calculate neighborhood density on spelling. If 'transcription' will calculate neighborhood density on transcriptions.")
parser.add_argument('-a', '--algorithm', default= 'edit_distance', help="The algorithm used to determine distance")
parser.add_argument('-d', '--max_distance', type=int, default = 1, help="Maximum edit distance from the queried word to consider a word a neighbor.")
parser.add_argument('-t', '--tiername', default = 'transcription', help="The name of the tier on which to calculate distance")
parser.add_argument('-w', '--count_what', default ='type', help="If 'type', count neighbors in terms of their type frequency. If 'token', count neighbors in terms of their token frequency.")
parser.add_argument('-o', '--outfile', help='Name of output file')

args = parser.parse_args()


####

corpus = load_binary(args.corpus_file_name)[0]

result = neighborhood_density(corpus, args.query, string_type = args.string_type, algorithm = args.algorithm, max_distance = args.max_distance, tiername = args.tiername, count_what=args.count_what)

if args.outfile:
    with open(args.outfile, 'w') as outfile:
        outfile.write(str(result)) # TODO: develop output file structure
else:
    print('No output file name provided.')
    print('The neighborhood density of the given form is {}.'.format(str(result)))