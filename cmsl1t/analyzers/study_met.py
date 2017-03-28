"""
Study the MET distibutions and various PUS schemes
"""

from BaseAnalyzer import BaseAnalyzer

class Analyzer(BaseAnalyzer.BaseAnalyzer):
    def __init__(self):
        pass

class Analyzer(BaseAnalyzer):
    def __init__(self,config):
        super(self,BaseAnalyzer).init("study_met",config)

    def process_event(self,entry,event):
        pass

    def make_plots(self):
        pass
