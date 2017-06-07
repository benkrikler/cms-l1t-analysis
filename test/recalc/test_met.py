import unittest
import numpy as np
from cmsl1t.recalc.met import l1Met28Only
import math


class TestCaloTower(object):

    def __init__(self, ieta, iet, iphi):
        self.ieta = ieta
        self.iet = iet

        self.phi = (math.pi / 36.0) * iphi
        self.et = 0.5 * iet
        self.iphi = iphi
        self.ex = self.et * math.cos(self.phi)
        self.ey = self.et * math.sin(self.phi)


class TestRecalcMET(unittest.TestCase):

    def test_l1Met28Only(self):
        c1 = TestCaloTower(28, 30, 0)
        c2 = TestCaloTower(22, 30, 0)
        met = l1Met28Only([c1, c2])
        self.assertEqual(met.x, -c1.ex)
        self.assertEqual(met.y, -c1.ey)
