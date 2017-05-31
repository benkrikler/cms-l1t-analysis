import collections
import bisect
from exceptions import RuntimeError, KeyError, NotImplementedError
from copy import deepcopy
import logging
from cmsl1t.hist.factory import HistFactory


logger = logging.getLogger(__name__)


class BinningBase():
    overflow = "overflow"
    underflow = "underflow"

    def __init__(self, label):
        self.label = label

    def set_contained_obj(self, contains):
        self.values = {}
        for i in range(self.n_bins) + [self.overflow, self.underflow]:
            self.values[i] = deepcopy(contains)

    def __len__(self):
        return self.n_bins

    def get_bin_contents(self, bin_index):
        contents = self.values.get(bin_index, None)
        if contents is None:
            msg = "Cannot find bin for index, {0}, for binning called '{1}'"
            logger.error(msg.format(bin_index, self.label))
            raise KeyError(bin_index)
        return contents

    def __getitem__(self, value):
        bins = self.find_bins(value)
        return [self.get_bin_contents(i) for i in bins]

    def __iter__(self):
        for i in range(self.n_bins):
            yield i


class Binning(BinningBase):
    import bisect

    def __init__(self, bin_edges, label=None):
        BinningBase.__init__(self, label)
        self.bins = sorted(bin_edges)
        self.n_bins = len(self.bins)

    def find_bins(self, value):
        if value < self.bins[0]:
            found_bin = self.underflow
        elif value >= self.bins[-1]:
            found_bin = self.overflow
        else:
            found_bin = bisect.bisect(self.bins, value) - 1
        return [found_bin]


class BinningOverlapped(BinningBase):
    def __init__(self, bins, label=None):
        BinningBase.__init__(self, label)
        self.bins = bins
        self.n_bins = len(self.bins)

    def find_bins(self, value):
        contained_in = []
        for i, (bin_low, bin_high) in enumerate(self.bins):
            if value >= bin_low and value < bin_high:
                contained_in.append(i)
        if len(contained_in) == 0:
            contained_in = [self.overflow]
        return contained_in


class BinningEtaRegions(BinningBase):
    from cmsl1t.geometry import eta_regions

    def __init__(self, label=None):
        BinningBase.__init__(self, label)
        self.n_bins = len(self.eta_regions)

    def find_bins(self, value):
        regions = []
        for region, is_contained in self.eta_regions.iteritems():
            if is_contained(value):
                regions.append(region)
        return regions


class HistCollectionView(object):
    def __init__(self, hist_list):
        self.histograms = hist_list

    def __getattr__(self, attr):
        return [getattr(hist, attr) for hist in self.histograms]

    def __method(self, method_name, *vargs, **kwargs):
        for hist in self.histograms:
            getattr(hist, method_name)(*vargs, **kwargs)

    def fill(self, *vargs, **kwargs):
        self.__method("fill", *vargs, **kwargs)

    def __iter__(self):
        for hist in self.histograms:
            yield hist

    def __len__(self):
        return len(self.histograms)


class HistogramCollection(object):
    '''
    The histogram collection needs a few things:
     - it needs to be able to essentially have binned maps of histograms
     - needs to know how to create new histograms
    '''

    def __init__(self, dimensions, histogram_factory, *vargs, **kwargs):
        '''
            Should dimensions include or exclude histogram names?
        '''
        if not isinstance(dimensions, list):
            dimensions = [dimensions]
        for dim in dimensions:
            if not isinstance(dim, BinningBase):
                raise RuntimeError("non-Dimension object given to histogram")
        self._dimensions = dimensions

        if isinstance(histogram_factory, str):
            histogram_factory = HistFactory(histogram_factory,
                                            *vargs, **kwargs)

        last_dim = None
        # Build the linked list of dimension bins objects
        for dimension in reversed(self._dimensions):
            if last_dim is None:
                # I would like to have the histogram factory passed bin labels
                # which we reformat the names and titles of the histograms with
                # Will add this in in the near future, by passing something
                # into this method
                dimension.set_contained_obj(histogram_factory())
            else:
                dimension.set_contained_obj(last_dim)
            last_dim = dimension

    @classmethod
    def _flatten_bins(self, bins):
        flattened_bins = []
        for dimension in bins:
            if len(flattened_bins) == 0:
                for index in dimension:
                    flattened_bins.append([index])
            else:
                new_bins = []
                for previous in flattened_bins:
                    new_bins += [previous + [index] for index in dimension]
                flattened_bins = new_bins
        output_bin_list = []
        for bin in flattened_bins:
            output_bin_list.append(tuple(bin))
        return output_bin_list

    def _find_bins(self, keys):
        # In python 3.3, this becomes collections.abc.Sequence
        if not isinstance(keys, collections.Sequence):
            keys = [keys]

        n_keys = len(keys)

        # Check every dimension if it contains these values
        bins = []
        for key, dimension in zip(keys, self._dimensions[:n_keys]):
            bins.append(dimension.find_bins(key))

        # Some dimensions might return multiple values, flatten returned arrays
        bins = self._flatten_bins(bins)

        return bins

    def get_bin_contents(self, bin_list):
        if isinstance(bin_list, int):
            bin_list = [bin_list]
        value = self._dimensions[0]
        for index in bin_list:
            value = value.get_bin_contents(index)
        return value

    def __getitem__(self, keys):
        '''
            Supposed to handle
                coll[x]
            and
                coll[x, y, z]
        '''
        bin_indices = self._find_bins(keys)
        objects = [self.get_bin_contents(bins) for bins in bin_indices]
        return HistCollectionView(objects)

    def shape(self):
        _shape = [len(dim) for dim in self._dimensions]
        return tuple(_shape)

    def __len__(self):
        return len(self._dimensions[0])

    def __iter__(self):
        # # In python >3.3 we should do
        # yield from self._dimensions[0]
        for bin in self._dimensions[0]:
            yield bin