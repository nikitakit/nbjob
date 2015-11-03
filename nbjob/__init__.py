# As a package centered around Jupyter notebooks, the source code of nbjob is
# stored in *.ipynb files instead of *.py files
# This requires special machinery for importing notebooks, which we enable
# inside nbjob only.
try:
    get_ipython()
except NameError:
    raise ImportError('nbjob can only be imported inside a Jupyter notebook, not a regular python session')

import ipykernel
if 'ZMQInteractiveShell' not in str(type(get_ipython())):
    raise ImportError('nbjob can only be imported inside a Jupyter notebook, and not any other IPython session')

from . import notebook_import_hooks

# Now we can import the actual source from a notebook
# TODO(nikita): potentially fix namespace pollution
from .init import *