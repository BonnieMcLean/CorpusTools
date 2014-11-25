from corpustools.symbolsim.edit_distance import edit_distance
from corpustools.symbolsim.khorsi import khorsi, make_freq_base
from corpustools.symbolsim.phono_edit_distance import phono_edit_distance

def neighborhood_density(corpus, query, string_type = 'transcription', algorithm = 'edit_distance', max_distance = 1, tiername = 'transcription', count_what='type'):
    """Calculate the neighborhood density of a particular word in the corpus. 
    Parameters
    ----------
    corpus : Corpus
        The domain over which functional load is calculated.
    query : Word or list of strings
        The word whose neighborhood density to calculate.
    string_type : string
        If 'spelling', will calculate neighborhood density on spelling. If 'transcription' will calculate neighborhood density on transcriptions
    algorithm : string
        The algorithm used to determine distance
    max_distance : number, optional
        Maximum edit distance from the queried word to consider a word a neighbor.
    tiername : string
        The tiername to calculate distance on
    count_what : string
        If 'type', count neighbors in terms of their type frequency. If 'token', count neighbors in terms of their token frequency

    Returns
    -------
    float
        The number of neighbors for the queried word.
    """
    def is_neighbor(w, query, algorithm, max_distance):
        if algorithm is 'edit_distance':
            return edit_distance(w, query, 'transcription') <= max_distance
        elif algorithm == 'phonological_edit_distance':
            return phono_edit_distance(w, query, tiername, corpus.specifier) <= max_distance
        elif algorithm == 'khorsi':
            if corpus.transcription_freq_base[count_what] is None:
                corpus.transcription_freq_base[count_what] = make_freq_base(corpus,string_type,count_what)
            freq_base = corpus.transcription_freq_base[count_what]
            return khorsi(w, query, freq_base, 'transcription') >= max_distance
        
    query_word = corpus.find(query)
    if algorithm == 'edit_distance':
        neighbors = [w for w in corpus if (len(w.transcription) <= len(query_word.transcription)+max_distance
                                       and len(w.transcription) >= len(query_word.transcription)-max_distance 
                                       and is_neighbor(w, query_word, algorithm, max_distance))]
    else:
        neighbors = [w for w in corpus if is_neighbor(w, query_word, algorithm, max_distance)]


    # add option for token frequency

    # add option to return list of neighbors

    return len(neighbors)-1



def neighborhood_density_2(corpus, query, max_distance=1, use_token_frequency=False):
    """Calculate the neighborhood density of a particular word in the corpus. Generates all possible neighbors of query and checks whether each is in the corpus.

    Parameters
    ----------
    corpus : Corpus
        The domain over which functional load is calculated.
    query : Word
        The word whose neighborhood density to calculate.
    max_distance : number, optional
        Maximum edit distance from the queried word to consider a word a neighbor.
    use_token_frequency : bool, optional
        If True, count neighbors in terms of their token frequency.

    Returns
    -------
    float
        The number of neighbors for the queried word.
    """
    pass