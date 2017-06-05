import collections
import bisect
from exceptions import RuntimeError, KeyError, NotImplementedError
from copy import deepcopy
import logging
from cmsl1t.hist.factory import HistFactory
from cmsl1t.hist.binning import Base as BinningBase


__all__ = ["HistCollectionView", "HistogramCollection"]


logger = logging.getLogger(__name__)


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
        self.__dimensions = dimensions
        self.shape = tuple([len(dim) for dim in dimensions])

        if isinstance(histogram_factory, str):
            histogram_factory = HistFactory(histogram_factory,
                                            *vargs,
                                            **kwargs)
        self.values = self._prepare_collection(dimensions, histogram_factory)

    def _prepare_collection(self, dimensions, histogram_factory,
                            bin_labels=[], depth=0):
            this_dim = deepcopy(dimensions[0])
            remaining_dims = dimensions[1:]
            for bin in this_dim.iter_all():
                if remaining_dims:
                    value = self._prepare_collection(remaining_dims,
                                                     histogram_factory,
                                                     bin_labels + [bin],
                                                     depth + 1)
                    this_dim.set_value(bin, value)
                else:
                    vargs = bin_labels + [bin]
                    kwargs = {}
                    # TODO: Should fill proper bin labels here and pass through
                    hist = histogram_factory(*vargs, **kwargs)
                    this_dim.set_value(bin, hist)
            return this_dim

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
        for key, dimension in zip(keys, self.__dimensions[:n_keys]):
            bins.append(dimension.find_all_bins(key))

        # Some dimensions might return multiple values, flatten returned arrays
        bins = self._flatten_bins(bins)

        return bins

    def get_bin_contents(self, bin_list):
        if isinstance(bin_list, (str, int)):
            bin_list = [bin_list]
        value = self.values
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
        return self.shape

    def __len__(self):
        return len(self.__dimensions[0])

    def __iter__(self):
        # # In python >3.3 we should do
        # yield from self.__dimensions[0]
        for bin in self.__dimensions[0]:
            yield bin

    def iter_all(self):
        # # In python >3.3 we should do
        # yield from self.__dimensions[0]
        for bin in self.__dimensions[0].iter_all():
            yield bin
