import math
import numpy as np

class recalcMET():
    def __init__(self,exclude=None,PUS=None,threshold=None):
        self.__exclude=exclude
        self.__PUS=PUS
        self.__threshold=threshold # Could be included into exclude, or even PUS

        self.metx = 0
        self.mety = 0
        self.__update_mag_phi()

    def __call__(self,caloTowers,pileup=None):
        self.calculate(caloTowers,pileup)
        return self.mag

    def calculate(self,caloTowers,pileup=None):
        ets = []
        phis = []
        for tower in caloTowers:
            # ieta = tower.ieta
            if self.__exclude is not None and self.__exclude(tower):
                continue
            phi = (math.pi / 36.0) * tower.iphi
            et = 0.5 * tower.iet
            if self.__threshold is not None and et < self.__threshold:
                continue
            if self.__PUS is not None:
                et= self.__PUS(tower,pileup)
            ets.append(et)
            phis.append(phi)
        self.metx = -sum(ets * np.cos(phis))
        self.mety = -sum(ets * np.sin(phis))
        self.__update_mag_phi()

    def __update_mag_phi(self):
        self.mag = math.sqrt(self.metx**2 + self.mety**2)
        self.phi= math.atan2(self.mety,self.metx)
        # TODO: Should these members be read-only properties?

l1MetFull=recalcMET()
l1MetBarrel=recalcMET(     exclude=lambda tower: abs(tower.ieta) <= 28)
l1Met28Only=recalcMET(     exclude=lambda tower: abs(tower.ieta) == 28)
l1MetBarrelNot28=recalcMET(exclude=lambda tower: abs(tower.ieta) < 28 )
l1MetNot28HF=recalcMET(    exclude=lambda tower: abs(tower.ieta) != 28)
