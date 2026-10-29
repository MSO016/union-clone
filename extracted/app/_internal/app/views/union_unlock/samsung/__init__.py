# -*- coding: utf-8 -*-
"""
SAMSUNG - Módulos Samsung Unlock
=================================
Estrutura modular para unlock FRP Samsung

Modelos suportados (ativos localmente):
- Galaxy A02 Todos (MTK BROM) ✅
- Galaxy A03s Todos (MTK BROM) ✅
- Galaxy A04 Todos (MTK BROM) ✅
- Galaxy A04e Todos (MTK BROM) ✅
- Galaxy A05 Todos (MTK BROM) ✅
- Galaxy A06 Todos (MTK BROM) ✅
- Galaxy A10s Todos (MTK BROM) ✅
- Galaxy A32 Todos (MTK BROM) ✅
- Galaxy A02s A025M (Qualcomm EDL) ✅
- Galaxy A05s A057G-U7/M/M-UB (Qualcomm EDL) ✅
- Galaxy A05s A057F/F-U9/F-UB → MIGRADO para tabela loaders
- Galaxy A20s A207F/M (Qualcomm EDL) ✅

Modelos MIGRADOS para tabela loaders (servidos via edl_sync):
- Galaxy A01 A015M        → MIGRADO
- Galaxy A11 A115F U6     → MIGRADO
- Galaxy A11 A115M U5     → MIGRADO
- Galaxy A23 A235M UB     → MIGRADO
- Galaxy A23 A235M UC     → MIGRADO
- Galaxy A23 A235M UD     → MIGRADO

Cor da Interface: Azul Samsung Forte (#1428A0)
"""

from .samsung import SamsungWidget
# from .galaxy_a01_a015m import GalaxyA01A015mWidget  # MIGRADO
from .galaxy_a02_all import GalaxyA02AllWidget
from .galaxy_a03s_all import GalaxyA03sAllWidget
from .galaxy_a04_all import GalaxyA04AllWidget
from .galaxy_a04e_all import GalaxyA04eAllWidget
from .galaxy_a05_all import GalaxyA05AllWidget
from .galaxy_a06_all import GalaxyA06AllWidget
from .galaxy_a10s_all import GalaxyA10sAllWidget
from .galaxy_a32_all import GalaxyA32AllWidget
from .galaxy_a02s_a025m import GalaxyA02sA025mWidget
# from .galaxy_a05s_a057f import GalaxyA05sA057fWidget  # MIGRADO
# from .galaxy_a05s_a057f_u9 import GalaxyA05sA057fU9Widget  # MIGRADO
# from .galaxy_a05s_a057f_ub import GalaxyA05sA057fUBWidget  # MIGRADO
from .galaxy_a05s_a057g_u7 import GalaxyA05sA057gU7Widget
from .galaxy_a05s_a057m import GalaxyA05sA057mWidget
from .galaxy_a05s_a057m_ub import GalaxyA05sA057mUBWidget
# from .galaxy_a05s_a057m_uc import GalaxyA05sA057mUCWidget  # MIGRADO
# from .galaxy_a11_a115f import GalaxyA11A115fWidget          # MIGRADO
# from .galaxy_a11_a115m import GalaxyA11A115mWidget          # MIGRADO
from .galaxy_a20s_a207f import GalaxyA20sA207fWidget
from .galaxy_a20s_a207m import GalaxyA20sA207mWidget
from .galaxy_a23_a235f_ua import GalaxyA23A235fUAWidget
# from .galaxy_a23_a235m_ub import GalaxyA23A235mUBWidget  # MIGRADO
# from .galaxy_a23_a235m_uc import GalaxyA23A235mUCWidget  # MIGRADO
from .galaxy_all_android_16 import GalaxyAllAndroid16Widget
from .galaxy_a23_a235n_u9 import GalaxyA23A235nU9Widget
# from .galaxy_a23_a235m_ud import GalaxyA23A235mUDWidget  # MIGRADO
from .galaxy_s20fe_g780g import GalaxyS20feG780gWidget
# EDL Qualcomm
# Ref: /administrativo/documentacao/05-09-2026--QCOM-FEATURES-NOVAS/ANALISE_REMOCAO_5_MODULOS_SAMSUNG_07-09-2026.md
# MIGRADO — from .galaxy_a70_a705f import GalaxyA70A705fWidget
from .galaxy_taba_t295 import GalaxyTabAT295Widget
# MIGRADO — from .galaxy_s20fe5g_g781b import GalaxyS20FE5GG781bWidget
# MIGRADO — from .galaxy_s10lite_g770f import GalaxyS10LiteG770fWidget

__all__ = [
    'SamsungWidget',
    # 'GalaxyA01A015mWidget',  # MIGRADO
    'GalaxyA02AllWidget',
    'GalaxyA03sAllWidget',
    'GalaxyA04AllWidget',
    'GalaxyA04eAllWidget',
    'GalaxyA05AllWidget',
    'GalaxyA06AllWidget',
    'GalaxyA10sAllWidget',
    'GalaxyA32AllWidget',
    'GalaxyA02sA025mWidget',
    # 'GalaxyA05sA057fWidget',  # MIGRADO
    # 'GalaxyA05sA057fU9Widget',  # MIGRADO
    # 'GalaxyA05sA057fUBWidget',  # MIGRADO
    'GalaxyA05sA057gU7Widget',
    'GalaxyA05sA057mWidget',
    'GalaxyA05sA057mUBWidget',
    # 'GalaxyA05sA057mUCWidget',  # MIGRADO
    # 'GalaxyA11A115fWidget',     # MIGRADO
    # 'GalaxyA11A115mWidget',     # MIGRADO
    'GalaxyA20sA207fWidget',
    'GalaxyA20sA207mWidget',
    'GalaxyA23A235fUAWidget',
    # 'GalaxyA23A235mUBWidget',  # MIGRADO
    # 'GalaxyA23A235mUCWidget',  # MIGRADO
    'GalaxyAllAndroid16Widget',
    'GalaxyA23A235nU9Widget',
    # 'GalaxyA23A235mUDWidget',  # MIGRADO
    'GalaxyS20feG780gWidget',
    # MIGRADO — 'GalaxyA70A705fWidget',
    'GalaxyTabAT295Widget',
    # MIGRADO — 'GalaxyS20FE5GG781bWidget',
    # MIGRADO — 'GalaxyS10LiteG770fWidget',
]
