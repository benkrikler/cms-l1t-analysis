from rootpy.plotting.utils import draw as r_draw
from rootpy.plotting.hist import Efficiency
from rootpy.plotting import Style, Canvas
from rootpy.context import preserve_current_style
from rootpy.ROOT import gStyle, TLatex
import rootpy.ROOT as ROOT
from exceptions import RuntimeError


"""
I would rather not have had to do it this way, but I could see no alternative.
The TColor header defines an enum for the palettes:
https://root.cern.ch/doc/master/TColor_8h.html#acb46d776ab87271c3fc10b14c50b169c
In rootpy (or pyROOT) these are accessible as attributes of ROOT however, since
the enum is not defined within the TColor class, just in the header file the
enums end up in the global ROOT namespace.  As a result, it would not really be
possible to check that a given string is actually a root palette, and not just
some method / class / variable in the ROOT namespace.  This solves this by
copying in the valid list of strings from the above link so that we can
validate that a requested palette actually exists in ROOT.
"""
__known_root_pallettes = set(["DeepSea", "GreyScale",
                              "DarkBodyRadiator", "BlueYellow",
                              "RainBow", "InvertedDarkBodyRadiator",
                              "Bird", "Cubehelix",
                              "GreenRedViolet", "BlueRedYellow",
                              "Ocean", "ColorPrintableOnGrey",
                              "Alpine", "Aquamarine",
                              "Army", "Atlantic",
                              "Aurora", "Avocado",
                              "Beach", "BlackBody",
                              "BlueGreenYellow", "BrownCyan",
                              "CMYK", "Candy",
                              "Cherry", "Coffee",
                              "DarkRainBow", "DarkTerrain",
                              "Fall", "FruitPunch",
                              "Fuchsia", "GreyYellow",
                              "GreenBrownTerrain", "GreenPink",
                              "Island", "Lake",
                              "LightTemperature", "LightTerrain",
                              "Mint", "Neon",
                              "Pastel", "Pearl",
                              "Pigeon", "Plum",
                              "RedBlue", "Rose",
                              "Rust", "SandyTerrain",
                              "Sienna", "Solar",
                              "SouthWest", "StarryNight",
                              "Sunset", "TemperatureMap",
                              "Thermometer", "Valentine",
                              "VisibleSpectrum", "WaterMelon",
                              "Cool", "Copper",
                              "GistEarth", "Viridis"])


def root_palette(value, max, min=0):
    colour_index = float(value - min) / float(max - min) * gStyle.GetNumberOfColors()
    return gStyle.GetColorPalette(int(colour_index))


def __prepare_canvas(canvas_args):
    style = gStyle
    style.SetOptStat(0)

    canvas = Canvas(**canvas_args)
    canvas.SetGridx(True)
    canvas.SetGridy(True)
    canvas.title = ""
    return canvas, style


def __clean(hists):
    cleaned_hists = []
    for hist in hists:
        if isinstance(hist, Efficiency):
            hist = hist.graph
        cleaned_hists.append(hist)
    return cleaned_hists


def __apply_colour_map(hists, colourmap, colour_values, change_colour):
    # Clean change_colour
    change_colour = [c.lower() for c in change_colour]

    with preserve_current_style():
        # Resolve the requested pallette if it's not a function
        if isinstance(colourmap, str):
            if colourmap in __known_root_pallettes:
                gStyle.SetPalette(getattr(ROOT, "k" + colourmap))
                colourmap = root_palette
            else:
                raise RuntimeError("Unknown palette requested: " + colourmap)

        # Set the colour of each hist
        max = len(hists)
        for value, hist in enumerate(hists):
            if colour_values:
                value, max = colour_values(value)
            colour = colourmap(value, max)
            if "line" in change_colour:
                hist.linecolor = colour
            if "marker" in change_colour:
                hist.markercolor = colour


def draw(hists, colourmap="RainBow", colour_values=None,
         change_colour=("line", "marker"), canvas_args={}, draw_args={}):
    canvas, style = __prepare_canvas(canvas_args)
    hists = __clean(hists)
    __apply_colour_map(hists, colourmap, colour_values, change_colour)
    xaxis = hists[0].axis(0)
    yaxis = hists[0].axis(1)
    hists[0].title = ""
    r_draw(hists, canvas, same=True, xaxis=xaxis, yaxis=yaxis, **draw_args)
    return canvas


def label_canvas(sample_title=None, run=None, isData=False):
    latex = TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)

    cms = "#bf{CMS} #it{Preliminary}"
    if sample_title:
        cms += sample_title
    latex.DrawLatex(0.15, 0.92, cms)

    run_summary = "(13 TeV)"
    if run:
        run_summary += run
    latex.SetTextAlign(31)
    latex.DrawLatex(0.92, 0.92, run_summary)
