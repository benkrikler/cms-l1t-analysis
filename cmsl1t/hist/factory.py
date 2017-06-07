from cmsl1t.hist import BaseHistogram
import logging
import rootpy.plotting.hist as rootpy_hists
from exceptions import RuntimeError
from copy import deepcopy


logger = logging.getLogger(__name__)


class HistFactory():
    """
    A simple interface to build histograms from known sources
    Instances of this class can be called to create concrete instance of
    the requested histogram type, with the passed options
    """

    def __init__(self, hist_type, *vargs, **kwargs):
        """
        Initialise the factory.
        If the variable build_err to False if the requested histogram cannot be
        found.

        Parameters:
        hist_type -- (str) The name of the class of objects this factory builds.
                     Should be a standard ROOT object, exist in the
                     rootpy.plotting.hist package, or be a custom hist deriving
                     from cmsl1t.hist.BaseHistogram
        *vargs, **kwargs -- These are captured and passed to the objects'
                            __init__ methods at instantiation. Useful for
                            passing binning specifications, axis names, etc.
        """
        self.hist_type = hist_type
        self.vargs = vargs
        self.kwargs = kwargs

        self.build_err = ""
        self._prepare_hist_class()

    def _prepare_hist_class(self):
        import rootpy.ROOT as ROOT

        histograms = []
        for hist in BaseHistogram.__subclasses__():
            if hist.__name__ == self.hist_type:
                histograms.append(hist)
        if hasattr(rootpy_hists, self.hist_type):
            histograms.append(getattr(rootpy_hists, self.hist_type))
        elif hasattr(ROOT, self.hist_type):
            histograms.append(getattr(ROOT, self.hist_type))
        if len(histograms) == 0:
            msg = "No valid histogram type called: '{0}'"
            msg = msg.format(self.hist_type)
            logger.error(msg)
            self.build_err = msg
            return
        elif len(histograms) > 1:
            msg = "Multiple histogram types are called: '{0}'"
            msg = msg.format(self.hist_type)
            logger.error(msg)
            self.build_err = msg
            return

        self.hist_class = histograms[0]

    def build(self, *new_vargs, **new_kwargs):
        """
        Actually build an instance of the requested histogram object.
        Arguments passed to this method will be combined with those passed to
        the initialisation method.

        If new_kwargs contains the keyword labels, this will be used to format
        the name and title strings of the produced histogram, and then removed
        from new_kwargs

        Parameters:
        new_vargs -- appended to vargs that were passed to the factory's init
        new_kwargs -- updates the kwargs that were passed to the factory's init
        """
        if self.build_err:
            raise RuntimeError(self.build_err)

        vargs = deepcopy(self.vargs) + new_vargs
        kwargs = deepcopy(self.kwargs)
        kwargs.update(new_kwargs)

        if "labels" in kwargs:
            for attr in ["title", "name"]:
                if attr in kwargs:
                    new_attr = kwargs[attr].format(**kwargs["labels"])
                    kwargs[attr] = new_attr

        if "labels" in kwargs:
            kwargs.pop('labels')

        hist = self.hist_class(*vargs, **kwargs)
        return hist

    def __call__(self, *vargs, **kwargs):
        """
        See documentation for build method
        """
        return self.build(*vargs, **kwargs)
