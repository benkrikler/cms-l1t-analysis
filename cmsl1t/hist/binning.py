import bisect
from exceptions import KeyError
from copy import deepcopy
import logging


logger = logging.getLogger(__name__)


class Base():
    """
    Base class for binning objects.
    Derived classes should only need to implement the find_bins() method.

    Terminology:
     - key: the unbinned variable passed in to obtain a given bin
     - index: the bin index (could be an int, or a string for overflow,
              underflow, or everything
     - value: the object that every bin contains, typically another Binning
              object or a histogram itself
    """
    overflow = "overflow"
    underflow = "underflow"
    everything = "everything"

    def __init__(self, n_bins, label, use_everything_bin=False):
        """ Initialise the value map (with empty values, at this point)

        Keyword arguments:
        use_everything_bin -- also include an inclusive, integral bin
        """
        self.use_everything_bin = use_everything_bin
        self.label = label
        self.n_bins = n_bins
        keys = range(self.n_bins) + [self.overflow, self.underflow]
        if use_everything_bin:
            keys += [self.everything]
        self.values = {}
        for i in keys:
            self.values[i] = None

    def set_all_values(self, value):
        for key in self.values:
            self.values[key] = deepcopy(value)

    def set_value(self, bin, value):
        self.values[bin] = value

    def __len__(self):
        return self.n_bins

    def get_bin_contents(self, bin_index):
        contents = self.values.get(bin_index, "DoesntExist")
        if contents is "DoesntExist":
            msg = "Cannot find bin for index, {0}, for binning called '{1}'"
            logger.error(msg.format(bin_index, self.label))
            raise KeyError(bin_index)
        return contents

    def find_all_bins(self, key):
        """
        Find all bins containing this key
        """
        bins = self.find_bins(key)
        if self.use_everything_bin:
            bins.append(self.everything)
        return bins

    def __getitem__(self, key):
        """
        Returns a list of the values whose bin contains this key
        """
        bins = self.find_all_bins(key)
        return [self.get_bin_contents(i) for i in bins]

    def __iter__(self):
        """
        Iterate over all normal bins
        """
        for i in range(self.n_bins):
            yield i

    def iter_all(self):
        """
        Iterate over all bins, including everthing, underflow, and overflow
        """
        for i in self.values:
            yield i


class Sorted(Base):
    """
    Implements non-overlapping bins defined by a list of lower bin edges
    """
    import bisect

    def __init__(self, bin_edges, label, use_everything_bin=False):
        Base.__init__(self, len(bin_edges), label,
                      use_everything_bin=use_everything_bin)
        self.bins = sorted(bin_edges)

    def find_bins(self, key):
        if key < self.bins[0]:
            found_bin = self.underflow
        elif key >= self.bins[-1]:
            found_bin = self.overflow
        else:
            found_bin = bisect.bisect(self.bins, key) - 1
        return [found_bin]


class GreaterThan(Base):
    """
    Implements overlapping bins, defined by a list of lower bin edges.
    For a given key the returned bin must be defined by a lower-edge that is
    less than the key
    """
    def __init__(self, bins, label, use_everything_bin=False):
        Base.__init__(self, len(bins), label,
                      use_everything_bin=use_everything_bin)
        self.bins = bins

    def find_bins(self, key):
        contained_in = []
        for i, threshold in enumerate(self.bins):
            if key >= threshold:
                contained_in.append(i)
        if len(contained_in) == 0:
            contained_in = [self.overflow]
        return contained_in


class Overlapped(Base):
    """
    Implements arbitrarily overlapping bins
    A bin contains a given key if the bins lower-edge is less than the key, and
    its upper-edge is greater
    """
    def __init__(self, bins, label, use_everything_bin=False):
        Base.__init__(self, len(bins), label,
                      use_everything_bin=use_everything_bin)
        self.bins = bins

    def find_bins(self, key):
        contained_in = []
        for i, (bin_low, bin_high) in enumerate(self.bins):
            if key >= bin_low and key < bin_high:
                contained_in.append(i)
        if len(contained_in) == 0:
            contained_in = [self.overflow]
        return contained_in


class EtaRegions(Base):
    """
    Implements binning in eta regions
    See the description of eta_regions in cmsl1t.geometry.
    """
    from cmsl1t.geometry import eta_regions

    def __init__(self, label="eta_region", use_everything_bin=False):
        Base.__init__(self, len(self.eta_regions), label,
                      use_everything_bin=use_everything_bin)

    def find_bins(self, key):
        regions = []
        for region, is_contained in self.eta_regions.iteritems():
            if is_contained(key):
                regions.append(region)
        return regions
