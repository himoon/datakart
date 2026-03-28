from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("datakart")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

from .core.datagokr import Datagokr
from .core.ecos import Ecos
from .core.fss import Fss
from .core.jusogokr import Jusogokr
from .core.kakao import Kakao
from .core.kis import Kis
from .core.naver import Naver
from .core.naver_ad import NaverAd
from .core.sgis import Sgis

__all__ = [
    "Datagokr",
    "Ecos",
    "Fss",
    "Jusogokr",
    "Kakao",
    "Kis",
    "Naver",
    "NaverAd",
    "Sgis",
]
