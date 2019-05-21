'''
Created 13.1.2017
@author: Vit Smilauer
'''

# A typical workflow
# $ python setup.py install       test your installation locally as a root as it would be downloaded from PyPI server
# $ python setup.py install --user   test your installation locally as a user, installs under /home/user/.local/lib/
# $ python setup.py sdist         creates an archive on local computer
# $ python setup.py register      registers to PyPI server
# $ python setup.py sdist upload  creates an archive on local computer and upload to PyPI server
# $ python setup.py sdist --format=zip creates source archive on local computer

# Uninstall with $ pip uninstall edubeam . This also shows you the location of files.

# Alternatively, without default path, $ pip install --user dist/edubeam*.tar.gz
# See also https://bashelton.com/2009/04/setuptools-tutorial/#setup.py-package_dir
# See also https://docs.python.org/2/distutils/setupscript.html

import sys
import os
import re

from setuptools import setup, find_packages
from edubeam import ebinit

author = 'Borek Patzak, Jan Stransky, Vit Smilauer'

setup(name='edubeam',
      version=ebinit.version,
      description='EduBeam - Linear static analysis of 2D beams',
      license='GPL',
      author=author,
      author_email='info@oofem.org',
      packages=find_packages(),
      install_requires=['numpy', 'PyOpenGL', 'xlwt'], # 'wxPython' and 'GLUT' is not a standard distribution on pip, install manually
      include_package_data=True,
      url='http://mech.fsv.cvut.cz/edubeam',
)

