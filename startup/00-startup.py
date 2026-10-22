"""ISS analysis profile: XView GUI on top of the Tiled-backed databroker.

Launched through ``pixi run start`` in the profile directory (or
``bsan --runtime-env=pixi``), which sets ``QT_API=pyqt6`` and
``MPLBACKEND=qtagg`` before IPython starts.
"""
import os
import sys
import time as ttime

print(ttime.ctime() + ' >>>> ' + __file__)

# Qt binding for qtpy / matplotlib; the pixi `start` task already sets this.
os.environ.setdefault('QT_API', 'pyqt6')
os.environ.setdefault('MPLBACKEND', 'qtagg')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import urllib3
from qtpy import QtCore, QtWidgets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The QApplication has to exist before any GUI module is imported (Qt6 aborts
# when a QPixmap/QIcon is created without one).
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):  # Qt5 only; Qt6 is always high-DPI aware
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

# Qt6 has no desktop theme on conda-forge and falls back to Fusion, whose flat
# buttons look disabled; use the same readable stylesheet as XLive.
try:
    from isstools.elements.qt_style import apply_iss_style
    apply_iss_style(app)
except ImportError:
    pass

# Run the Qt event loop from the IPython prompt so the GUI stays responsive.
get_ipython().enable_gui('qt')
plt.ion()

# ---------------------------------------------------------------- data access
# `Broker.named('iss')` resolves the Tiled profile called "iss" on this host
# (the same mechanism nslsii.configure_base uses in the collection profile) and
# wraps the "raw" catalog in the databroker v1 API that xview expects.
from databroker import Broker, catalog as _tiled_catalogs

try:
    db = Broker.named('iss')
except Exception as e:
    print(f'Failed to open ISS databroker: {e}')
    db = None

if db is not None and hasattr(db, 'reg'):
    # Legacy (databroker v1 / mongo) deployments need the ISS asset handlers;
    # with Tiled the handlers live in the service and `db.reg` does not exist.
    try:
        from xas.handlers import register_all_handlers
        register_all_handlers(db)
    except Exception as e:
        print(f'Could not register ISS handlers: {e}')

try:
    db_archive_catalog = _tiled_catalogs['iss']
except Exception as e:
    print(f'Failed to open ISS archive catalog: {e}')
    db_archive_catalog = None

try:
    db_catalog = _tiled_catalogs['iss-local']
except Exception as e:
    print(f'Failed to open ISS local catalog: {e}')
    db_catalog = None

# Processed-spectra catalog: the mongo-backed `get_spectrum_catalog` from
# xview.spectra_db is not available with databroker 2; keep the slot so the
# GUI signature is unchanged.
db_proc = None

# ------------------------------------------------------------------------ GUI
sys.stdout.write('\33]0;XView terminal\a')
sys.stdout.flush()

from xview import xview as _xview_module

xview_gui = _xview_module.XviewGui(db=db,
                                   db_proc=db_proc,
                                   db_archive_catalog=db_archive_catalog,
                                   db_catalog=db_catalog)


def xview():
    """Bring the XView window back if it was closed."""
    xview_gui.show()


xview()
print(f'XView startup complete at {ttime.ctime()}')
