"""
.. module:: collections.efficiency
    :synopsis: Module for creating efficiency(turnon)-curves

.. moduleauthor:: Luke Kreczko
"""
from collections import defaultdict
from . import HistogramsByPileUpCollection
import rootpy.plotting as rplt 
from rootpy import asrootpy
from ROOT import TEfficiency,TLatex,gStyle
from cmsl1t.utils.iterators import pairwise
import logging

logger = logging.getLogger(__name__)


class _EfficiencyCurve(object):

    def __init__(self, name, bins, threshold):
        self.name=name
        self._pass = rplt.Hist(bins, name=name + '_pass')
        self._total = rplt.Hist(bins, name=name + '_total')
        self._dist = rplt.Hist(bins, name=name + '_dist')
        self._threshold = threshold
        self._efficiency = None

    def fill(self, recoValue, l1Value, weight=1.):
        """ Fills the histograms used for efficiency calculation
        :param recoValue: the reconstructed quanity
        :type recoValue: float
        :param l1Value: the L1 Trigger quantity
        :type l1Value: float
        :param weight: weight to fill the histograms with, default=1.0
        :type weight: float
        """
        self._total.fill(recoValue, weight)
        self._dist.fill(l1Value, weight)
        if l1Value > self._threshold:
            self._pass.fill(recoValue, weight)

    def calculate_efficiency(self):
        self._efficiency = asrootpy(TEfficiency(self._pass, self._total))
        self._efficiency.SetName(self._total.GetName() + '_eff')

    def get_efficiency(self):
        if not self._efficiency:
            self.calculate_efficiency()
        return self._efficiency

    def merge(self,another_eff_curve):
        """ Dont forget to call calculate_efficiency() once all merges are finished"""
        if isinstance(another_eff_curve,int):
            return
        self._pass.Add(another_eff_curve._pass)
        self._total.Add(another_eff_curve._total)
        self._dist.Add(another_eff_curve._dist)

class EfficiencyCollection(HistogramsByPileUpCollection):
    '''
        The EfficiencyCollection allows for easy creation and access to turon-on
        curves (efficiency curves). For each variable it stores (for each
        pileup bin) 3 objects:
         - the true distribution
         - the observed distribution
         - their ratio (efficiency)

        The EfficiencyCollection is a 3D collection of histogram name, pileUp and
        thresholds:
        >>> histograms = EfficiencyCollection(pileUpBins=0, 13, 20, 999])
        >>> histograms.add_variable('JetPt', thresholds = [30, 50, 70, 100])
        >>> histograms.set_pileup(pileUp)
        >>> histograms.fill('JetPt', jetPtReco, jetPtL1)

    '''

    def __init__(self, pileupBins=[0, 13, 20, 999]):
        self._dimensions = 3
        self._thresholds = {}
        self._bins = {}
        HistogramsByPileUpCollection.__init__(
            self, pileupBins=pileupBins, dimensions=self._dimensions)
        self._pileUp = 0
        self._pileUpBins = pileupBins
        self.variables=set()

    def add_variable(self, variable, bins, thresholds):
        """ This function adds a variable to be tracked by this collection.
        :param variable: The variable name
        :type name: str.
        :param bins: The bins to be used for the variable
        :type bins: list.
        :param thresholds: A list of thresholds for L1 values
        :type thresholds: list.
        """
        # TODO: this will no longer work since 1st dimension is pileup
        if variable in self.variables:
            logger.warn('Variable {0} already exists!')
            return
        self.variables.add(variable)
        self._thresholds[variable] = thresholds
        self._bins[variable] = bins
        hist_names = []
        add_name = hist_names.append

        for puBinLower, puBinUpper in pairwise(self._pileUpBins):
            for threshold in thresholds:
                name = '{0}_threshold_gt{1}_pu{2}To{3}'.format(
                    variable, threshold, puBinLower, puBinUpper)
                if not self[puBinLower][variable][threshold]:
                    add_name(name)
                    self[puBinLower][variable][
                        threshold] = _EfficiencyCurve(name, bins, threshold)
        logger.debug('Created {0} histograms: {1}'.format(
            len(hist_names), ', '.join(hist_names)))

    def fill(self, hist_name, recoValue, l1Value, w=1.0):
        h = self[self._pileUp][hist_name]
        if not h:
            logger.error('Histogram {0} does not exist'.format(hist_name))
            return
        if hist_name not in self._thresholds:
            logger.warn(
                'No valid current thresholds.')
        for threshold in self._thresholds[hist_name]:
            h[threshold].fill(recoValue, l1Value, w)

    def _calculateEfficiencies(self):
        for puBinLower, _ in pairwise(self._pileUpBins):
            for hist in self[puBinLower].keys():
                for threshold in self._thresholds[hist]:
                    self[puBinLower][hist][threshold].calculate_efficiency()

    def to_root(self, output_file):
        self._calculateEfficiencies()
        HistogramsByPileUpCollection.to_root(self, output_file)

    @staticmethod
    def from_root(input_file):
        instance=HistogramsByPileUpCollection.from_root(self, input_file)
        # Need to recalculate efficiency curves in case combined histogram files have been read back in
        instance._calculateEfficiencies()

    def summarise(self):
        '''
            Sums histograms across PU bins
        '''
        logger.info("Summarizing plots")
        for variable in self.variables:
            bins=self._bins[variable]
            for threshold in self._thresholds[variable]:
                name = '{0}_threshold_gt{1}'.format(variable, threshold)
                summed=_EfficiencyCurve(name, bins, threshold)
                for pu_hists in self.values():
                    summed.merge(pu_hists[variable][threshold])
                summed.calculate_efficiency()
                self["sum"][variable][threshold] = summed



    def draw_plots(self,output_folder,img_type):
        self.output_folder=output_folder
        self.draw_extension=img_type
        # TODO: implement the following:
        # if self.do_fits: self.fit_plots()

        for variable in self.variables:
            # Draw the efficiency curves for integrated pile-up for the different levels
            name="efficiency_{var}".format(var=variable)
            self._draw_efficiency_curves(name, leg_header=variable
                    ,leg_labels=[ "> "+str(thresh) for thresh in self._thresholds[variable]]
                    ,key_list=[ ("sum",variable,threshold) for threshold in self._thresholds[variable] ])
            for threshold in self._thresholds[variable]:
                # Draw the efficiency curves for pile-up bins for the different levels
                thresh_name=name+"_threshold-{thresh}".format(thresh=threshold)
                self._draw_efficiency_curves(thresh_name, leg_header="{var} > {val}".format(var=variable,val=threshold)
                    ,leg_labels=[str(low)+"#leq pu <"+str(high) for low,high in pairwise(self._pileUpBins) ]
                    ,key_list=[ (pileup,variable,threshold) for pileup,_ in pairwise(self._pileUpBins) ])

    def _draw_efficiency_curves(self,save_as,key_list,leg_header=None,leg_labels=None):
        canvas=rplt.Canvas()
        legend=rplt.Legend(len(key_list),header=leg_header)
        # Draw on every curve
        for i,keys in enumerate(key_list):
            label=", ".join(map(str,keys))
            if leg_labels:
                label=leg_labels[i]
            hist=self[keys[0]][keys[1]][keys[2]].get_efficiency()
            if isinstance(hist,int): continue
            self.SetColor(hist,i,len(key_list))
            if i==0: hist.Draw("ap")
            else:    hist.Draw("psame")
            legend.AddEntry(hist,label)
        legend.Draw()
        DrawCmsStamp()
        canvas.Print(self._get_plot_name(save_as))

#----------------------------------------------------------------
#TODO: These should probably be in some base class
#TODO: Many of these things really want access to some global configuration variables
#----------------------------------------------------------------

    def _get_plot_name(self,name_kernel):
        """ 
        TODO: This should probably be in some base class
        """
        import os.path
        return os.path.join(self.output_folder,name_kernel+"."+self.draw_extension)

    @staticmethod
    def SetColor(hist,index,n_indices,setFill=False):

        def CalculateColor(index,n_indices):
            modifier=0
            colour=1
            fraction = (index+0.5)/float(n_indices)

            if index > n_indices-1 or index < 0 or n_indices-1 < 0: colour = 1
            else:
                colorIndex = (fraction * (1.0-2.0*modifier) + modifier) * gStyle.GetNumberOfColors();
                colour = gStyle.GetColorPalette(int(colorIndex));
            return colour

        colour=CalculateColor(index,n_indices)
        hist.SetLineColor(colour)
        hist.SetMarkerColor(colour)
        if setFill: hist.SetFillColor(colour)
        else:       hist.SetFillColor(0)

def DrawCmsStamp():
    latex=TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextAlign(12)
    latex.DrawLatexNDC(gStyle.GetPadLeftMargin(),0.92,"#bf{CMS} #it{Preliminary} 2016 Data")
    latex.SetTextAlign(32)
    latex.DrawLatexNDC(1-gStyle.GetPadRightMargin(),0.92,"(13 TeV)")
