# -*- coding: utf-8 -*-
"""
MOTO - Módulos Motorola Unlock
==============================
Estrutura modular para unlock FRP Motorola

Modelos suportados:
- Moto E7 (MTK BROM) - MT6765/MT6762 - Malta_64
- Moto E7 Power (MTK BROM) - MT6765/MT6762
- Moto E22 (MTK BROM)
- Moto E22i (MTK BROM)
- Moto G05 (MTK BROM)
- Moto G15 (MTK BROM)
- Moto G22 (MTK BROM) - MT6765 - hawaiip - 🧪 EM TESTE
- Moto G23 (MTK Preloader) - MT6768 - penangf - 🧪 EM TESTE
- Moto G13 (MTK Preloader) - MT6768 - penangf - 🧪 EM TESTE
- MDM SPD/MTK (Fastboot) - Aparelhos antigos - 🧪 EM TESTE
- FRP OLD (Factory Mode) - G5/G6/G7 - 🧪 EM TESTE
"""

from .motorola import MotorolaWidget
from .moto_e7 import MotoE7Widget
from .moto_e7_power import MotoE7PowerWidget
from .moto_e22 import MotoE22Widget
from .moto_e22i import MotoE22iWidget
from .moto_g05 import MotoG05Widget
from .moto_g15 import MotoG15Widget
from .moto_g22 import MotoG22Widget
# from .moto_g23 import MotoG23Widget  # REMOVIDO — migrado para documentação
# from .moto_g13 import MotoG13Widget  # REMOVIDO — migrado para documentação
from .mdm_spd_mtk import MdmSpdMtkWidget
from .moto_frp_old import MotoFrpOldWidget

__all__ = [
    'MotorolaWidget',
    'MotoE7Widget',
    'MotoE7PowerWidget',
    'MotoE22Widget',
    'MotoE22iWidget',
    'MotoG05Widget',
    'MotoG15Widget',
    'MotoG22Widget',
    # 'MotoG23Widget',  # REMOVIDO
    # 'MotoG13Widget',  # REMOVIDO
    'MdmSpdMtkWidget',
    'MotoFrpOldWidget',
]
