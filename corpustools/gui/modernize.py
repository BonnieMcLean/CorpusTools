import random
from corpustools.corpus.classes.lexicon import Segment
from corpustools import __version__ as currentPCTversion

#it would be better to import these attributes from .models.InventoryModel, but this creates a circular import problem
inventory_attributes = {'_data':list(), 'segs':dict(), 'features':list(), 'possible_values':list(), 'stresses':list(),
                        'consColumns': set(['Column 1']), 'vowelColumns': set(['Column 1']),
                        'vowelRows': set(['Row 1']), 'consRows':set(['Row 1']),
                        'cons_column_data': {'Column 1': [0,{},None]}, 'cons_row_data': {'Row 1': [0,{},None]},
                        'vowel_column_data': {'Column 1': [0,{},None]}, 'vowel_row_data': {'Row 1': [0,{},None]},
                        'uncategorized': list(), 'all_rows': dict(),
                        'all_columns': dict(),'vowel_column_offset': int(), 'vowel_row_offset': int(),
                        'cons_column_header_order':dict(),'cons_row_header_order':dict(),
                        'vowel_row_header_order':dict(),'vowel_column_header_order': dict(),
                        'consList': list(), 'vowelList': list(),
                        'vowel_features': None, 'cons_features': None, 'voice_feature': None, 'rounded_feature': None,
                        'diph_feature': None, 'isNew': True}

def isNotSupported(corpus):
    if corpus.name.lower() == 'iphod':
        return True
    else:
        return False

def need_update(corpus):
    if hasattr(corpus, '_version') and corpus._version == currentPCTversion:
        return False
    else:
        setattr(corpus, '_version', currentPCTversion)
        return True

def modernize_inventory_attributes(inventory):
    for attribute,default in inventory_attributes.items():
        if not hasattr(inventory, attribute):
            setattr(inventory,attribute,default)
    if not inventory.segs and inventory._data:
        inventory.segs = inventory._data.copy()
        inventory._data = list()
    if hasattr(inventory, 'vowel_feature'):
        inventory.vowel_features = [inventory.vowel_feature]
        del inventory.vowel_feature
    return inventory

def modernize_features(inventory, specifier):
    #In some older versions of PCT, the FeatureMatrix returns Segments, instead of feature lists
    seg1 = random.choice([seg for seg in inventory.segs.values() if not seg.symbol=='#'])
    if isinstance(seg1.features, Segment):
        for seg in inventory:
            inventory[seg.symbol].features = specifier.matrix[seg.symbol]
    return inventory