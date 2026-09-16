import os
# Force math libraries to use only 1 thread to avoid hitting server process limits
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

from app import create_app

app = create_app()
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
