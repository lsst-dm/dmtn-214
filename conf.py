# See the Documenteer docs for how to customize conf.py:
# https://documenteer.lsst.io/technotes/

from documenteer.conf.technote import *  # noqa F401 F403

html_js_files = globals().get('html_js_files', []) + ['zoom.js']

if '_static' not in html_static_path:
    html_static_path.append('_static')
