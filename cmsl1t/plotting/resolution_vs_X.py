from __future__ import print_function
from cmsl1t.plotting.base import BasePlotter
from cmsl1t.hist.hist_collection import HistogramCollection
from cmsl1t.hist.factory import HistFactory
import cmsl1t.hist.binning as bn
from cmsl1t.utils.draw import draw2D, label_canvas
from cmsl1t.recalc.resolution import get_resolution_function

from rootpy.context import preserve_current_style
from rootpy.plotting import Legend
from rootpy import asrootpy


class ResolutionVsXPlot(BasePlotter):
    def __init__(self, resolution_type, online_name, offline_name, versus_name):
        name = ["resolution_vs_" + versus_name, online_name, offline_name]
        super(ResolutionVsXPlot, self).__init__("__".join(name))
        self.online_name = online_name
        self.offline_name = offline_name
        self.versus_name = versus_name
        self.resolution_method = get_resolution_function(resolution_type)

    def create_histograms(self,
                          online_title, offline_title, versus_title,
                          pileup_bins, res_n_bins, res_low, res_high,
                          vs_n_bins, vs_low, vs_high,
                          ):
        """ This is not in an init function so that we can by-pass this in the
        case where we reload things from disk """
        self.online_title = online_title
        self.offline_title = offline_title
        self.versus_title = versus_title
        self.pileup_bins = bn.Sorted(pileup_bins, "pileup",
                                     use_everything_bin=True)

        name = ["resolution_vs", self.versus_name, self.online_name, self.offline_name, "pu_{pileup}"]
        name = "__".join(name)
        title = " ".join(["Resolution (", self.online_name, "vs.", self.offline_name,
                          ") against", self.versus_name, "in PU bin: {pileup}"])
        title = ";".join([title, self.offline_title, self.online_title])
        self.plots = HistogramCollection([self.pileup_bins],
                                         "Hist2D", vs_n_bins, vs_low, vs_high,
                                         res_n_bins, res_low, res_high,
                                         name=name, title=title)
        self.filename_format = name

    def fill(self, pileup, versus, offline, online):
        difference = self.resolution_method(online, offline)
        self.plots[pileup].fill(versus, difference)

    def draw(self, with_fits=True):
        for (pileup, ), hist in self.plots.flat_items_all():
            self.__do_draw(pileup, hist)
            self.__do_draw(pileup, asrootpy(hist.ProfileX()), "_profile")

    def __do_draw(self, pileup, hist, suffix=""):
        with preserve_current_style():
            # Draw each efficiency (with fit)
            ytitle = self.resolution_method.label.format(on=self.online_title, off=self.offline_title)
            canvas = draw2D(hist, draw_args={"xtitle": self.versus_title, "ytitle": ytitle})

            # Add labels
            label_canvas()

            # Save canvas to file
            name = self.filename_format.format(pileup=pileup)
            self.save_canvas(canvas, name + suffix)

    def _is_consistent(self, new):
        """
        Check the two plotters are the consistent, so same binning and same axis names
        """
        return (self.pileup_bins.bins == new.pileup_bins.bins) and \
               (self.resolution_method == new.resolution_method) and \
               (self.versus_name == new.versus_name) and \
               (self.online_name == new.online_name) and \
               (self.offline_name == new.offline_name)

    def _merge(self, other):
        """
        Merge another plotter into this one
        """
        self.plots += other.plots
        return self.plots