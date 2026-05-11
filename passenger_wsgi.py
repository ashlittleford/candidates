import os
# Force math libraries to use only 1 thread to avoid hitting server process limits
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import importlib.machinery
import importlib.util
import sys


sys.path.insert(0, os.path.dirname(__file__))

def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

wsgi = load_source('wsgi', 'run.py')
application = wsgi.application
