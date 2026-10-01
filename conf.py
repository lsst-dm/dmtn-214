# See the Documenteer docs for how to customize conf.py:
# https://documenteer.lsst.io/technotes/

from documenteer.conf.technote import *  # noqa F401 F403

# Add sphinxcontrib.lightbox2 to the extensions list
# (Using extend to ensure we don't overwrite the list)
# Sphinx will have 'extensions' in the global scope at runtime from the import above.
extensions.extend(["sphinxcontrib.lightbox2"])
