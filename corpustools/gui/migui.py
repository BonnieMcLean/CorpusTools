from collections import OrderedDict

from corpustools.mutualinfo.mutual_information import mi_env_filter, pointwise_mi
from .imports import *
from .environments import EnvironmentSelectWidget
from .widgets import (BigramWidget, RadioSelectWidget, TierWidget, ContextWidget, SaveFileWidget)
from .windows import FunctionWorker, FunctionDialog
from corpustools.exceptions import PCTError, PCTPythonError
from corpustools.contextmanagers import (CanonicalVariantContext,
                                        MostFrequentVariantContext,
                                        SeparatedTokensVariantContext,
                                        WeightedVariantContext)
from corpustools import __version__

class MIWorker(FunctionWorker):
    def run(self):
        kwargs = self.kwargs
        self.results = []
        context = kwargs.pop('context')
        if context == ContextWidget.canonical_value:
            cm = CanonicalVariantContext
        elif context == ContextWidget.frequent_value:
            cm = MostFrequentVariantContext
        elif context == ContextWidget.separate_value:
            cm = SeparatedTokensVariantContext
        elif context == ContextWidget.relative_value:
            cm = WeightedVariantContext
        with cm(kwargs['corpus'], kwargs['sequence_type'],
                kwargs['type_token'], frequency_threshold=kwargs['frequency_cutoff']) as c:
            try:
                envs = kwargs.pop('envs', None)

                if envs is not None:    # if env is set, c(orpus context) is 'extracted'
                    context_output_path = kwargs.pop('context_output_path')  # context_output_path for env context export
                    c = mi_env_filter(c, envs, context_output_path)
                    kwargs['in_word'] = False

                for pair in kwargs['segment_pairs']:
                    res = pointwise_mi(c, pair,
                                       halve_edges = kwargs['halve_edges'],
                                       in_word = kwargs['in_word'],
                                       stop_check = kwargs['stop_check'],
                                       call_back = kwargs['call_back'])
                    if self.stopped:
                        break
                    self.results.append(res)
            except PCTError as e:
                self.errorEncountered.emit(e)
                return
            except Exception as e:
                e = PCTPythonError(e)
                self.errorEncountered.emit(e)
                return
        if self.stopped:
            self.finishedCancelling.emit()
            return
        self.dataReady.emit(self.results)



class MIDialog(FunctionDialog):
    header = ['Corpus',
              'PCT ver.',
              'Analysis name',
              'First segment',
              'Second segment',
              'Domain',
              'Halved edges',
              'Transcription tier',
              'Frequency type',
              'Pronunciation variants',
              'Minimum word frequency',
              'Environments',
              'Result']

    _about = [('This function calculates the mutual information for a bigram'
                    ' of any two segments, based on their unigram and bigram'
                    ' frequencies in the corpus.'),
                    '',
                    #'References: ',
                    ]

    name = 'mutual information'

    def __init__(self, parent, settings, corpus, inventory, showToolTips):
        FunctionDialog.__init__(self, parent, settings, MIWorker())

        self.corpus = corpus
        self.inventory = inventory
        self.showToolTips = showToolTips

        miFrame = QFrame()
        milayout = QHBoxLayout()

        self.segPairWidget = BigramWidget(self.inventory)

        milayout.addWidget(self.segPairWidget)

        optionLayout = QFormLayout()

        self.tierWidget = TierWidget(corpus,include_spelling=False)

        optionLayout.addRow(self.tierWidget)

        self.typeTokenWidget = RadioSelectWidget('Type or token frequency',
                                            OrderedDict([('Count types','type'),
                                            ('Count tokens','token')]))

        actions = None
        self.variantsWidget = ContextWidget(self.corpus, actions)

        optionLayout.addWidget(self.variantsWidget)

        optionLayout.addWidget(self.typeTokenWidget)
        
        ##----------------------
        minFreqFrame = QGroupBox('Minimum frequency')
        box = QFormLayout()
        self.minFreqEdit = QLineEdit()
        box.addRow('Minimum word frequency:',self.minFreqEdit)

        minFreqFrame.setLayout(box)

        optionLayout.addWidget(minFreqFrame)
        ##----------------------
        
        self.inWordCheck = QCheckBox('Set domain to word')
        optionLayout.addWidget(self.inWordCheck)

        self.halveEdgesCheck = QCheckBox('Halve word boundary count')
        self.halveEdgesCheck.setChecked(True)
        optionLayout.addWidget(self.halveEdgesCheck)

        optionFrame = QGroupBox('Options')
        optionFrame.setLayout(optionLayout)

        milayout.addWidget(optionFrame)
        miFrame.setLayout(milayout)

        ##---------------------- Environment selection frame (envFrame) consists of: check box, selection widget, savefile widget
        envFrame = QGroupBox('Environment (optional)')

        envLayout = QFormLayout()

        self.envCheck = QCheckBox('Set an environment filter')
        self.envCheck.clicked.connect(self.setEnv)

        self.envWidget = EnvironmentSelectWidget(inventory, middle = False, single_env=True)
        self.envWidget.setTitle('')
        self.envWidget.setEnabled(False)

        fileFrame = QGroupBox('Output list of contexts to a file')
        fileLayout = QHBoxLayout()
        fileFrame.setLayout(fileLayout)
        self.saveFileWidget = SaveFileWidget('Select file location', 'Text files (*.txt)')
        self.saveFileWidget.setEnabled(False)
        fileLayout.addWidget(self.saveFileWidget)

        envLayout.addWidget(self.envCheck)
        envLayout.addWidget(self.envWidget)
        envLayout.addWidget(fileFrame)

        envFrame.setLayout(envLayout)

        milayout.addWidget(envFrame)
        ##----------------------

        self.layout().insertWidget(0, miFrame)

        if self.showToolTips:
            self.tierWidget.setToolTip(("<FONT COLOR=black>"
                                    'Choose which tier mutual information should'
                                    ' be calculated over (e.g., the whole transcription'
                                    ' vs. a tier containing only [+voc] segments).'
                                    ' New tiers can be created from the Corpus menu.'
                                    "</FONT>"))
            self.segPairWidget.setToolTip(("<FONT COLOR=black>"
            'Choose bigrams for which to calculate the'
                                ' mutual information of their bigram and unigram probabilities.'
            "</FONT>"))
            inwordToolTip = ("<FONT COLOR=black>"
            'Set the domain for counting unigrams/bigrams set to the '
                        'word rather than the unigram/bigram; ignores adjacency '
                        'and word edges (#).'
            "</FONT>")
            self.inWordCheck.setToolTip(inwordToolTip)

            halveEdgesToolTip = ("<FONT COLOR=black>"
            'make the number of edge characters (#) equal to '
                        'the size of the corpus + 1, rather than double the '
                        'size of the corpus - 1.'
            "</FONT>")
            self.halveEdgesCheck.setToolTip(halveEdgesToolTip)

    def generateKwargs(self):
        self.kwargs = {}
        segPairs = self.segPairWidget.value()
        if len(segPairs) == 0:
            reply = QMessageBox.critical(self,
                    "Missing information", "Please specify at least one bigram.")
            return None
        envs = self.envWidget.value()
        if len(envs) > 0 and self.envCheck.checkState():
            self.kwargs['envs'] = envs
            self.kwargs['display_envs'] = {e: d for (e, d) in zip(envs, self.envWidget.displayValue())}
        ##------------------
        try:
            frequency_cutoff = float(self.minFreqEdit.text())
        except ValueError:
            frequency_cutoff = 0.0
        ##-------------------
        self.kwargs['corpus'] = self.corpus
        self.kwargs['context'] = self.variantsWidget.value()
        self.kwargs['type_token'] = self.typeTokenWidget.value()
        self.kwargs['segment_pairs'] = [tuple(y for y in x) for x in segPairs]
        self.kwargs['in_word'] = self.inWordCheck.isChecked()
        self.kwargs['halve_edges'] = self.halveEdgesCheck.isChecked()
        self.kwargs['frequency_cutoff'] = frequency_cutoff
        self.kwargs['sequence_type'] = self.tierWidget.value()
        self.kwargs['context_output_path'] = self.saveFileWidget.value() if self.saveFileWidget.value() != '' else ''
        return self.kwargs

    def setResults(self,results):
        self.results = []
        seg_pairs = [tuple(y for y in x) for x in self.segPairWidget.value()]
        if self.inWordCheck.isChecked():
            dom = 'Word'
        else:
            dom = 'Unigram/Bigram'
        try:
            frequency_cutoff = float(self.minFreqEdit.text())
        except ValueError:
            frequency_cutoff = 0.0
        if not self.envWidget.displayValue():
            environments = 'None'
        else:
            environments = ' ; '.join([x for x in self.envWidget.displayValue()])
        for i, r in enumerate(results):
            self.results.append({'Corpus': self.corpus.name,
                                'PCT ver.': __version__,#self.corpus._version,
                                'Analysis name': self.name.capitalize(),
                                'First segment': seg_pairs[i][0],
                                'Second segment': seg_pairs[i][1],
                                'Domain': dom,
                                'Halved edges': self.halveEdgesCheck.isChecked(),
                                'Transcription tier': self.tierWidget.displayValue(),
                                'Frequency type': self.typeTokenWidget.value().title(),
                                'Pronunciation variants': self.variantsWidget.value().title(),
                                'Minimum word frequency': frequency_cutoff,
                                'Environments': environments,
                                'Result': r})

    def setEnv(self):
        if self.envCheck.checkState():
            self.envWidget.setEnabled(True)
            self.saveFileWidget.setEnabled(True)
            self.inWordCheck.setEnabled(False)
        else:
            self.envWidget.setEnabled(False)
            self.saveFileWidget.setEnabled(False)
            self.inWordCheck.setEnabled(True)
