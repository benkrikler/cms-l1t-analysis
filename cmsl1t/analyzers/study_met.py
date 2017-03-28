"""
Study the MET distibutions and various PUS schemes
"""

from BaseAnalyzer import BaseAnalyzer
from cmsl1t.collections import EfficiencyCollection
from functools import partial
import cmsl1t.recalc.met as recalc
import numpy as np

class Analyzer(BaseAnalyzer):
    def __init__(self,config):
        super(Analyzer,self).__init__("study_met",config)

        self.met_calcs=dict(
                RecalcL1EmuMetBarrel=dict(title="RE MEt, Barrel",calculate=recalc.l1MetBarrel),
                RecalcL1EmuMetFull=dict(title="RE MEt, Barrel + Fwd",calculate=recalc.l1MetFull),
            )

#        [
#            'RecalcL1EmuMet',
#            # 'RecalcL1EmuMetHF',
#            # 'RecalcL1EmuMet28Only',
#            # 'RecalcL1EmuMetNot28',
#            # 'RecalcL1EmuMetPUS',
#            # 'RecalcL1EmuMetPUSHF',
#            # 'RecalcL1EmuMetPUS28',
#            # 'RecalcL1EmuMetPUSThresh',
#            # 'RecalcL1EmuMetPUSThreshHF',
#            # 'RecalcL1Met',
#            # 'RecalcL1Met28Only',
#        ]

    def reload_histograms(self,input_file):
        self.efficiencies=EfficiencyCollection.from_root(input_file)
        return True

    def prepare_for_events(self,reader):
        bins = np.arange(0, 200, 25)
        thresholds = [70, 90, 110]

        # histograms that look at:
        ## ET distribution vs, tower eta
        ## MET distribution vs, tower eta
        ## Efficiency curve 

        self.efficiencies = EfficiencyCollection(pileupBins=range(0, 50, 10)+[999])
        add_met_variable = partial(
            self.efficiencies.add_variable, bins=bins, thresholds=thresholds)
        map(add_met_variable, self.met_calcs)
        return True

    def fill_histograms(self,entry,event):
        pileup = event.nVertex
        if pileup < 5 or not event.passesMETFilter():
            return True
        self.efficiencies.set_pileup(pileup)

        offlineMetBE = event.sums.caloMetBE
        for name,config in self.met_calcs.items():
            onlineMet=config['calculate'](event.caloTowers,pileup)
            self.efficiencies.fill(name,offlineMetBE,onlineMet)

        return True

    def write_histograms(self):
        self.efficiencies.to_root(self.get_histogram_filename())
        return True

    def make_plots(self):
        self.efficiencies.draw_plots(self.output_folder,"png")
        return True
