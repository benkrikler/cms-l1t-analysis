import math
import numpy as np
import cmsl1t.geometry as geom

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
            if self.__threshold is not None and et < self.__threshold(tower.ieta,pileup):
                continue
            if self.__PUS is not None:
                et= self.__PUS(et,tower.ieta,pileup)
            ets.append(et)
            phis.append(phi)
        self.metx = -sum(ets * np.cos(phis))
        self.mety = -sum(ets * np.sin(phis))
        self.__update_mag_phi()

    def __update_mag_phi(self):
        self.mag = math.sqrt(self.metx**2 + self.mety**2)
        self.phi= math.atan2(self.mety,self.metx)
        # TODO: Should these members be read-only properties?

def PUS_fixed(et,tower,pileup):
    et+= -0.5*round(7*pileup/100.)
    if et<0: et=0
    return et 

def PUS_fixed28(et,tower,pileup):
    if abs(tower.ieta)!=28: return et
    return PUS_fixed(et,tower,pileup)

def PUS_variable(et,tower,pileup):
    # 0.087 is the width of a tower in the barrel
    et+= -0.5*round(geom.towerEtaWidth(tower.ieta)*7*pileup/100./0.087) 
    if et<0: et=0
    return et 

def threshold_fix(ieta,pileup):
    return 0.5

def threshold_ieta(ieta,pileup):
    return 0.5*(round(abs(ieta)/10.)+1)

def threshold_ieta_PU(ieta,pileup):
    return 0.5*(round((abs(ieta)/10.+1)*pileup/10.))

l1MetFull        = recalcMET()
l1MetBarrel      = recalcMET(exclude=lambda tower: abs(tower.ieta) <= 28)
l1Met28Only      = recalcMET(exclude=lambda tower: abs(tower.ieta) == 28)
l1MetBarrelNot28 = recalcMET(exclude=lambda tower: abs(tower.ieta) <  28)
l1MetNot28HF     = recalcMET(exclude=lambda tower: abs(tower.ieta) != 28)

l1MetFull_PUS28   = recalcMET(PUS=PUS_fixed28 )
l1MetBarrel_PUS28 = recalcMET(PUS=PUS_fixed28, exclude=lambda tower: abs(tower.ieta) <= 28)
l1Met28Only_PUS28 = recalcMET(PUS=PUS_fixed28, exclude=lambda tower: abs(tower.ieta) == 28)

l1MetFull_PUSAll        = recalcMET(PUS=PUS_variable )
l1MetBarrel_PUSAll      = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) <= 28)
l1Met28Only_PUSAll      = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) == 28)
l1MetBarrelNot28_PUSAll = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) <  28)
l1MetNot28HF_PUSAll     = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) != 28)

l1MetFull_threshEtaPU        = recalcMET(PUS=PUS_variable )
l1MetBarrel_threshEtaPU      = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) <= 28)
l1Met28Only_threshEtaPU      = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) == 28)
l1MetBarrelNot28_threshEtaPU = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) <  28)
l1MetNot28HF_threshEtaPU     = recalcMET(PUS=PUS_variable,exclude=lambda tower: abs(tower.ieta) != 28)
