import logging

logger = logging.getLogger(__name__)


# detector regions in eta
eta_regions = {
    # barrel
    'B': lambda x: abs(x) < 1.479,
    # endcap
    'E': lambda x: abs(x) >= 1.479 and abs(x) <= 3.0,
    # barrel or endcap
    'BE': lambda x: abs(x) <= 3.0,
    # hadron forward
    'HF': lambda x: abs(x) > 3.0,
}

# could add aliases


def is_in_region(region, eta, regions=eta_regions):
    if region not in regions:
        msg = 'Unknown detector region {0}'.format(region)
        logger.error(msg)
        raise KeyError(msg)

    return regions[region](eta)


__etaSizes_21onwards = [
        0.09, 0.1, 0.113, 0.129, 0.15, 0.178,
        0.15, 0.35, 0.5, 0.5, 0.5, 0.5
        ]


def towerEtaWidth(ieta):
    """
    Get the relative width of each tower compared to towers in the barrel
    :param ieta: the index of the tower
    :type int
    """
    width = 0.087
    if abs(ieta) > 20:
        width = __etaSizes_21onwards[abs(ieta)-21]
    return width
