#!/usr/bin/python
# -*- coding: utf-8 -*

#
#    EduBeam is an education project to develop a free structural
#               analysis code for educational purposes.
#
#                       (c) 2011 Borek Patzak 
#
#      Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
#
#  EduBeam is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published
#  by the Free Software Foundation, either version 3 of the License,
#  or (at your option) any later version.
#
#  EduBeam is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#

##################################################################
#
# edubeam.py file
# required files:
# ebinit.py (imported in ebfem.py file)
# ebfem.py  (imported in ebgui.py file)
# ebgui.py  (imported here)
#
##################################################################

"""
EduBeam is an education project to develop a free structural analysis code for educational purposes
"""

from ebgui import *

def main():
    OpenGL.GLUT.glutInit(sys.argv)

    logger.info( langStr('Welcome to EduBeam, ver. %s on %s', 'Vítejte v EduBeamu, ver. %s z %s') % (version,date) )
    logger.info( langStr('For more info, run:', 'Pro více informací spusťte:') + ' [python] edubeam.py -h' )

    app = wx.App(False)
    
    #show splash screen
    try:
        MySplash = MySplashScreen()
        MySplash.Show()
    except:
        pass

    frame = GLFrame(None, -1, 'EduBeam ver. %s' % version)
    #exit(0)
    app.SetTopWindow(frame)
    frame.Show(True)
    session.setGLFrame(frame)

    from ebgui import fileName
    if fileName:
        #add full path if not there
        if fileName == os.path.basename(fileName):
            fileName = os.path.join(os.getcwd(),fileName)
        frame.openFile(fileName)
        try:
            frame.fitAll()#Windows-related problem
        except:
            pass
        frame.solve()

    if pythonScriptFileName:
        #add full path if not there
        #if pythonScriptFileName == os.path.basename(pythonScriptFileName):
            #pythonScriptFileName = os.path.join(os.getcwd(),pythonScriptFileName)
        frame.execPythonScript(pythonScriptFileName)
        #print pythonScriptFileName
        #exec(pythonScriptFile)
    app.MainLoop()
    app.Destroy()
    logger.info( langStr('Thank you for using EduBeam software', 'Děkujeme za používání softwaru EduBeam') )

if __name__ == "__main__":
    main()

