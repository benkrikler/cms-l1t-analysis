"""
Study the MET distibutions and various PUS schemes
"""

from BaseAnalyzer import BaseAnalyzer

from functools import partial
import cmsl1t.recalc.met as recalc

class Analyzer(BaseAnalyzer):
    def __init__(self,config):
        super(self,BaseAnalyzer).init("study_met",config)

        self.met_calcs=dict(
                RecalcL1EmuMet=dict(title="RE MEt, Barrel",calculate=recalc.met),
                RecalcL1EmuMetHF=dict(title="RE MEt, Barrel + Fwd",calculate=recalc.met_HF),
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
#        ])

    def prepare_for_events(self,reader):

        # histograms that look at:
        ## ET distribution vs, tower eta
        ## MET distribution vs, tower eta
        ## Efficiency curve 
        self.efficiencies = EfficiencyCollection(pileupBins=range(0, 50, 10)+[999])
        add_met_variable = partial(
            self.efficiencies.add_variable, bins=bins, thresholds=thresholds)
        map(add_met_variable, self.met_calcs)

    def fill_histograms(self,entry,event):
        pileup = event.nVertex
        if pileup < 5 or not event.passesMETFilter():
            continue
        histograms.set_pileup(pileup)

        offlineMetBE = event.sums.caloMetBE
        for name,config in self.met_calcs.items():
            onlineMet=config['calculate'](event)
            self.efficiencies[name].fill(offlineMetBE,onlineMet)

    def make_plots(self):
        pass
