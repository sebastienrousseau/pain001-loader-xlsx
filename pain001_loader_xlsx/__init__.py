# SPDX-License-Identifier: Apache-2.0

"""Excel (.xlsx / .xlsm) loader plugin for the pain001 ISO 20022 library.

The single public entry point is :class:`pain001_loader_xlsx.loader.XlsxLoader`,
discovered by ``pain001`` via the ``pain001.loaders`` entry-point group
declared in this package's ``pyproject.toml``.

Direct usage is supported but unnecessary for the common case:

.. code-block:: bash

   pip install pain001 pain001-loader-xlsx
   pain001 -t pain.001.001.03 -d payments.xlsx
"""

from pain001_loader_xlsx.loader import XlsxLoader

__version__ = "0.0.53"
__all__ = ["XlsxLoader", "__version__"]
