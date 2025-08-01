"""
Expose `lib/<pkg>` modules under the public namespace `yggdrasil.<pkg>`.

After this shim runs ...

    import lib.core_utils.event_types as X
    import yggdrasil.core_utils.event_types as Y

... return the *same* module object, so Enum identities match.
"""

import pkgutil
import sys
import types
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_lib = _root / "lib"

# 1) ensure lib/ is importable for in-repo code
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))

# 2) make yggdrasil a namespace package so sub-imports work
# if __name__ not in sys.modules:
#     sys.modules[__name__] = types.ModuleType(__name__)
this_pkg = sys.modules[__name__]
this_pkg.__path__ = [str(_lib)]  # namespace path points at lib/

# 3) alias every top-level package under lib/ -> yggdrasil.<pkg>
for finder, name, ispkg in pkgutil.iter_modules([str(_lib)]):
    if not ispkg:
        continue
    full_old = f"{name}"  # e.g. "core_utils"
    full_new = f"{__name__}.{name}"  # e.g. "yggdrasil.core_utils"

    try:
        mod = import_module(full_old)  # imports lib.core_utils
        sys.modules[full_new] = mod  # alias
    except ModuleNotFoundError:
        continue  # ignore odd files that aren't real pkgs

# 4) set package version for runtime access
try:
    __version__ = version("yggdrasil")
except PackageNotFoundError:  # local checkout without install
    from setuptools_scm import get_version

    __version__ = get_version(root=_root, relative_to=__file__)
