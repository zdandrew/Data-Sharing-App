#pdaota.wsgi
import sys 
sys.path.insert(0, '/var/www/html/pdaota/')
  
from pdaota import app as application