import io, os, sys, types

import nbformat
from IPython.core.interactiveshell import InteractiveShell
import traitlets.config.loader

def find_notebook(fullname, path=None):
    """find a notebook, given its fully qualified name and an optional path
    
    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
        
    # HACK for development purposes
    if fullname.rsplit('.', 1)[0] == 'nbjob_dev':
        path = None

    # only trigger on import into the nbjob namespace
    if fullname.rsplit('.', 1)[0] != 'nbjob' and fullname.rsplit('.', 1)[0] != 'nbjob_dev':
        return
    
    name = fullname.rsplit('.', 1)[-1]
    
    if not path:
        path = ['']
        path.append(os.path.dirname(__file__))

    for d in path:
        if isinstance(d, traitlets.config.loader.LazyConfigValue):
            continue
            
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path
        
class NotebookLoader(object):
    """Module Loader for IPython Notebooks"""
    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path
    
    def load_module(self, fullname):
        """import a notebook as a module"""
        path = find_notebook(fullname, self.path)
        
        #print ("importing IPython notebook from %s" % path)
                                       
        # load the notebook object
        with io.open(path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, nbformat.NO_CONVERT)
        
        
        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        sys.modules[fullname] = mod
        
        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__
        
        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    inp = cell.source
                    stop = False
                    if "#" + "NBIMPORT_STOP" in inp:
                        inp = inp.split("#" + "NBIMPORT_STOP")[0]
                        stop = True
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(inp)
                    # run the code in themodule
                    exec(code, mod.__dict__)
                    # stop, if needed
                    if stop:
                        break
        finally:
            self.shell.user_ns = save_user_ns
        return mod

class NotebookFinder(object):
    """Module finder that locates IPython Notebooks"""
    def __init__(self):
        self.loaders = {}
        self.find_notebook = find_notebook
    
    def find_module(self, fullname, path=None):
        nb_path = self.find_notebook(fullname, path)
        if not nb_path:
            return
        
        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)
        
        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]

sys.meta_path.append(NotebookFinder())