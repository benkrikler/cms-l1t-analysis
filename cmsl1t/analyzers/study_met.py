"""
Study the MET distibutions and various PUS schemes
"""

from BaseAnalyzer import BaseAnalyzer

class Analyzer(BaseAnalyzer):
    def __init__(self,config):
        super(self,BaseAnalyzer).init("study_met",config)

    def reload_histograms(self,input_file):
        self.efficiencies=EfficiencyCollection.from_root(input_file)
        return True

    def prepare_for_events(self,reader):
        pass

    def fill_histograms(self,entry,event):
        pass

    def make_plots(self):
        pass
