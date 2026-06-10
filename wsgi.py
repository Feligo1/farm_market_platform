import os
import sys
import importlib.util


BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

BACKEND_WSGI = os.path.join(BACKEND_DIR, "wsgi.py")
spec = importlib.util.spec_from_file_location("farmconnect_backend_wsgi", BACKEND_WSGI)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app
