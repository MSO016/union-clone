# -*- coding: utf-8 -*-
"""Módulos Xiaomi - TECH UNION SOLUTIONS"""
from .xiaomi import XiaomiWidget
from .redmi_a1 import RedmiA1Widget
from .redmi_a2 import RedmiA2Widget
from .redmi_a3 import RedmiA3Widget
from .redmi_9 import Redmi9Widget
from .redmi_9a import Redmi9AWidget
from .redmi_10_2022 import Redmi102022Widget
from .redmi_12c import Redmi12CWidget
from .redmi_13c import Redmi13CWidget
from .redmi_14c import Redmi14CWidget
from .redmi_note_12s import RedmiNote12SWidget
from .redmi_note8pro_begonia import RedmiNote8ProBegoniaWidget  # BROM MTK
from .redmi_note9_merlin import RedmiNote9MerlinWidget  # BROM MTK
from .redmi_12_fire import Redmi12FireWidget  # BROM MTK
from .poco_m3_pro import PocoM3ProWidget  # BROM MTK (Kamakiri)
from .redmi_note10_5g import RedmiNote105GWidget  # BROM MTK (Kamakiri)
from .poco_c55 import PocoC55Widget  # BROM MTK (Kamakiri)
from .redmi_note11s import RedmiNote11SWidget  # BROM MTK (Kamakiri)
from .redmi_note10s import RedmiNote10SWidget  # BROM MTK (Kamakiri)
from .poco_m4_pro_4g import PocoM4Pro4GWidget  # BROM MTK (Kamakiri) - Mesmo hardware do Note 11S
# EDL Qualcomm — migrados para nuvem (aba QCOM EDL dinamica)

__all__ = [
    'XiaomiWidget',
    'RedmiA1Widget',
    'RedmiA2Widget',
    'RedmiA3Widget',
    'Redmi9Widget',
    'Redmi9AWidget',
    'Redmi102022Widget',
    'Redmi12CWidget',
    'Redmi13CWidget',
    'Redmi14CWidget',
    'RedmiNote12SWidget',
    'RedmiNote8ProBegoniaWidget',  # BROM MTK
    'RedmiNote9MerlinWidget',  # BROM MTK
    'Redmi12FireWidget',  # BROM MTK
    'PocoM3ProWidget',  # BROM MTK (Kamakiri)
    'RedmiNote105GWidget',  # BROM MTK (Kamakiri)
    'RedmiNote10SWidget',  # BROM MTK (Kamakiri)
    'PocoC55Widget',  # BROM MTK (Kamakiri)
    'RedmiNote11SWidget',  # BROM MTK (Kamakiri)
    'PocoM4Pro4GWidget',  # BROM MTK (Kamakiri) - Mesmo hardware do Note 11S
    # EDL Qualcomm — migrados para nuvem (aba QCOM EDL dinamica)
]
