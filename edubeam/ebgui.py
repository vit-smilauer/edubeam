# -*- coding: utf-8 -*

#
#          EduBeam is an education project to develop a free structural
#                   analysis code for educational purposes.
#
#                             (c) 2011 Borek Patzak 
#
#       EduBeam is free software; you can redistribute it and/or modify it 
#         under the terms of the GNU General Public License as published 
#        by the Free Software Foundation; either version 2 of the License, 
#                        or (at your option) any later version.
#
# EduBeam is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details. You should have received a copy of 
# the GNU General Public License along with File Hunter; if not, write to 
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

##################################################################
#
# ebgui.py file
# defines EduBeam GUI
#
##################################################################

"""
EduBeam Graphical User Interface module providing GUI functionality
"""

from ebfem import *
import ebinit

try:
    #on Ubuntu with unity desktop, run apt-get remove appmenu-gtk*, otherwise Menubar is gone 
    import wx.adv
    import wx
    from wx import glcanvas
    import wx.lib.sheet as sheet
    import wx.lib.stattext as stattext
except ImportError as e:
    logger.fatal( langStr('Required dependency wx not present, install it manually. %s'%e, 'Požadovaná závislost wx nenalezena, nainstalujte ručně wx %s'%e) )
    raise ImportError

try:
    from OpenGL.GL import *
    try: # needed for windows exe
        from ctypes import util
        import OpenGL.platform.win32
        from OpenGL.platform import win32
        import OpenGL.arrays.ctypesarrays
        import OpenGL.arrays.numpymodule
        import OpenGL.arrays.lists
        import OpenGL.arrays.numbers
        import OpenGL.arrays.formathandler
    except:
        pass
    import OpenGL.GLUT
    import OpenGL.GLU
except ImportError as e:
    import traceback
    traceback.print_exc()
    logger.fatal( langStr('Required dependency OpenGL not present, install it manually. %s'%e, 'Požadovaná závislost OpenGL nenalezena, nainstalujte ručně OpenGL. %s'%e) )
    raise e





##################################################################
#
# frames and graphics positions and sizes
#
##################################################################
minHeight      = 500
canvasSize     = (400, minHeight) # main drawing area with a grid
minContextSize = (220, minHeight) # minimum size of left Context window
panelSize      = (215, minHeight-15) #size of left panel
mainBoxSize    = (210, minHeight-15) #size of box in the left panel
panelPos       = (5, 5) #panel position in left Context
btPos1   = (10, minHeight-50)
btSize1  = (95, 27)
btPos2   = (110, minHeight-50)
btSize2  = (75, 27)
labelPos = (0, 0)
labelTextPos = (10, 20)
labelEntPos  = (100, 20)


#selection mask
NODE_MASK    = 1 << 0
ELEMENT_MASK = 1 << 1


##################################################################
#
# auxiliary functions
#
##################################################################
def glDefaultColor():
   """Sets glColor to defalt value"""
   r,g,b = globalSettings.defaultColor
   glColor(r,g,b)


def projectCoordinates(x,y):
    """Project window coords to gl coord"""
    modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX);
    if not any(modelMatrix): # Windows related problem, in the beginning when mouse is over canvas, modelMatrix is full of zeros resulting in OpenGL ValueError
        return None
    projMatrix =  glGetDoublev(GL_PROJECTION_MATRIX);
    viewport = glGetIntegerv(GL_VIEWPORT)
    winX = x;
    winY = viewport[3] - y;
    mc = OpenGL.GLU.gluUnProject(winX,winY,0,modelMatrix,projMatrix,viewport)
    return mc

# auxiliary function to convert model coordinates to window coordinates
def projectM2WCoordinates(x,y,z):
    """Project window coords to gl coord"""
    modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX);
    projMatrix =  glGetDoublev(GL_PROJECTION_MATRIX);
    viewport = glGetIntegerv(GL_VIEWPORT)
    wc = OpenGL.GLU.gluProject(x,y,z,modelMatrix,projMatrix,viewport)
    return wc

# glut based graphical string printing 
def glPrintString(x, y, z, string, adj=3):
    """GL function for strings display"""
    glRasterPos3f(x, y, z)
    # move raster position slightly to improve readability
    glBitmap (0,0,0,0,adj,adj,None)
    for i in string:
        arg = OpenGL.GLUT.GLUT_BITMAP_HELVETICA_12
        fontSize = str(globalSizesScales.fontSize)
        if fontSize == '10':
            arg = OpenGL.GLUT.GLUT_BITMAP_HELVETICA_10
        elif fontSize == '18':
            arg = OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18
        OpenGL.GLUT.glutBitmapCharacter(arg, ord(i))

def glCircle(x,y,z,r,n=12):
    """draw circle with center x,y,z and radius r as n-polygon"""
    if n<3: n=3
    glBegin(GL_LINE_LOOP)
    for i in xrange(n):
        phi = i*2*math.pi/n
        glVertex3f(x+r*math.cos(phi),y,z+r*math.sin(phi))
    glEnd()

def computeAngleFromCosSin(cos,sin):
    """Computes value of angle from its sin and cos"""
    angle = math.acos(cos)
    if sin <0: angle = 2*math.pi - angle
    return angle

def glArrow(x,y,z,xSize,zSize,w=0.1,h=0.2):
    """draw arrow with tip at x,y,z, length size, head width size*w
    and head height size*h, rotated with angle"""
    size = math.sqrt(xSize*xSize+zSize*zSize)
    if(size!=0.):
        c = xSize/size
        s = zSize/size
    else:
        c=0.
        s=0.
    glBegin(GL_LINES)
    glVertex3f(x,y,z)
    glVertex3f(x+c*(-size),y,z+s*(-size))
    glVertex3f(x,y,z)
    glVertex3f(x+c*(-size)*h-s*size*w,y,z+s*(-size)*h+c*size*w)
    glVertex3f(x,y,z)
    glVertex3f(x+c*(-size)*h-s*(-size*w),y,z+s*(-size)*h+c*(-size*w))
    glEnd()

def glArrowMoment(x,y,z,size,w=0.2,h=0.4,r=0.1,n=9):
    """draw moment arrow with center at x,y,z, radius size and clockwise if size<0, anticlockwise otherwise"""
    glBegin(GL_LINE_STRIP)
    for i in xrange(n+1):
        angle = (i if size<0 else -i)*math.pi*3/2./n
        glVertex3f(x+size*math.cos(angle),y,z+size*math.sin(angle))
    glEnd()
    s = abs(size)
    glBegin(GL_LINES)
    glVertex3f(x,y,z+s)
    glVertex3f(x+s*h*(1 if size<0 else -1),y,z+s*(+1+w-r))
    glVertex3f(x,y,z+s)
    glVertex3f(x+s*h*(1 if size<0 else -1),y,z+s*(+1-w-r))
    glEnd()

#convert numbers like -0.00 to 0.00
def posZero(a, precision=2):
    b=round(a,precision)
    if b == -b:
        return fabs(a)
    else:
        return a

class WidgetWithHelp:
    """Abstract class for generic widget type with help message.
    The help message is displayed in glframe statusbar (this behavior can be easily changed in future). See e.g. StaticTextWithHelp class for inheritance details.

    :param help: keyword argument containing help message to display
    :type help: str
    """
    def __init__(self,help=''):
        self.help = help
        self.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)
    def onMouseOver(self, event):
        session.glframe.sb.SetStatusText(self.help)
        event.Skip()
    def onMouseLeave(self, event):
        session.glframe.sb.SetStatusText('')
        event.Skip()

class StaticTextWithHelp(stattext.GenStaticText, WidgetWithHelp):
    """Static text with help
    
    :param args: args passed to wx.lib.stattext.GenStaticText class
    :param kw: keyword args passes to wx.lib.stattext.GenStaticText class
    :param help: keyword argument containing help message to display
    :type help: str
    """
    def __init__(self,*args,**kw):
        help = kw.pop('help','')
        stattext.GenStaticText.__init__(self,*args,**kw)
        WidgetWithHelp.__init__(self,help)

class CheckBoxWithHelp(wx.CheckBox, WidgetWithHelp):
    """Check box with help
    
    :param args: args passed to wx.CheckBox class
    :param kw: keyword args passes to wx.CheckBox class
    :param help: keyword argument containing help message to display
    :type help: str
    """
    def __init__(self,*args,**kw):
        help = kw.pop('help','')
        wx.CheckBox.__init__(self,*args,**kw)
        WidgetWithHelp.__init__(self,help)

class TextCtrlWithHelp(wx.TextCtrl, WidgetWithHelp):
    """TextCtrl with help
    
    :param args: args passed to wx.TextCtrl class
    :param kw: keyword args passes to wx.TextCtrl class
    :param help: keyword argument containing help message to display
    :type help: str
    """
    def __init__(self,*args,**kw):
        help = kw.pop('help','')
        wx.TextCtrl.__init__(self,*args,**kw)
        WidgetWithHelp.__init__(self,help)

class ComboBoxWithHelp(wx.ComboBox, WidgetWithHelp):
    """ComboBox with help
    
    :param args: args passed to wx.ComboBox class
    :param kw: keyword args passes to wx.ComboBox class
    :param help: keyword argument containing help message to display
    :type help: str
    """
    def __init__(self,*args,**kw):
        help = kw.pop('help','')
        wx.ComboBox.__init__(self,*args,**kw)
        WidgetWithHelp.__init__(self,help)


##################################################################
#
# Splash screen
#
##################################################################

class MySplashScreen(wx.adv.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, parent=None):
        name = os.path.join(ebdir,'splash.png')
        if not os.path.isfile(name):
            return
        aBitmap = wx.Image(name = name).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 2000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()
#----------------------------------------------------------------------#

    def OnExit(self, evt):
        self.Hide()
        evt.Skip()  # Make sure the default handler runs too...
#----------------------------------------------------------------------#
def createPostProcesorBox (self, parent, id, glframe):
    return LinearStaticPostProcessBox(parent, id, glframe)
LinearStaticSolver.postProcesorBox = createPostProcesorBox

def createPostProcesorBox (self, parent, id, glframe):
    return LinearStabilityPostProcessBox(parent, id, glframe)
LinearStabilitySolver.postProcesorBox = createPostProcesorBox

##################################################################
#
# Context
#
##################################################################
class Context(wx.Panel):
    """A context panel - on the left side"""
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE,
                 name='context'):
        wx.Panel.__init__(self, parent, id, pos=pos, size=size, style=style, name=name)
        self.SetMinSize(minContextSize)
        #
        self.parent = parent
        self.materialBox     = MaterialBox(self, wx.NewId(), parent, 'add')
        self.materialEditBox = MaterialBox(self, wx.NewId(), parent, 'edit')
        self.materialDelBox  = MaterialBox(self, wx.NewId(), parent, 'del')
        #
        self.crossSectBox     = CrossSectBox(self, wx.NewId(), parent, 'add')
        self.crossSectEditBox = CrossSectBox(self, wx.NewId(), parent, 'edit')
        self.crossSectDelBox  = CrossSectBox(self, wx.NewId(), parent, 'del')
        #
        self.nodeBox     = NodeBox(self, wx.NewId(), parent, 'add')
        self.nodeEditBox = NodeBox(self, wx.NewId(), parent, 'edit')
        self.nodeDelBox  = NodeBox(self, wx.NewId(), parent, 'del')
        #
        self.elemBox     = ElemBox(self, wx.NewId(), parent, 'add')
        self.elemEditBox = ElemBox(self, wx.NewId(), parent, 'edit')
        self.elemDelBox  = ElemBox(self, wx.NewId(), parent, 'del')
        #
        self.loadCaseBox     = LoadCaseBox(self, wx.NewId(), parent, 'add')
        self.loadCaseEditBox = LoadCaseBox(self, wx.NewId(), parent, 'edit')
        self.loadCaseDelBox  = LoadCaseBox(self, wx.NewId(), parent, 'del')
        #
        self.nodalLoadBox     = NodalLoadBox(self,wx.NewId(), parent, 'add')
        self.nodalLoadEditBox = NodalLoadBox(self,wx.NewId(), parent, 'edit')
        self.nodalLoadDelBox  = NodalLoadBox(self,wx.NewId(), parent, 'del')
        #
        self.pDsplBox     = PrescribedDsplBox(self,wx.NewId(), parent, 'add')
        self.pDsplEditBox = PrescribedDsplBox(self,wx.NewId(), parent, 'edit')
        self.pDsplDelBox  = PrescribedDsplBox(self,wx.NewId(), parent, 'del')
        #
        self.elementLoadBox     = ElementLoadBox(self,wx.NewId(), parent, 'add')
        self.elementLoadEditBox = ElementLoadBox(self,wx.NewId(), parent, 'edit')
        self.elementLoadDelBox  = ElementLoadBox(self,wx.NewId(), parent, 'del')
        #
        self.transformMeshBox   = TransformMeshBox(self,wx.NewId(), parent)
        self.modifyNodesBox     = ModifyNodesBox(self,wx.NewId(), parent)
        #
        self.postProcessBox = session.solver.postProcesorBox(self,wx.NewId(), parent)
        self.selectSolverBox = SelectSolverBox(self,wx.NewId(), parent)
        #
        self.scaleBox = ScaleBox(self, wx.NewId(), parent)
        self.gridBox = GridBox(self, wx.NewId(), parent)
        self.colorSetupBox=ColorSetupBox(self,wx.NewId(), parent)
        #
        self.pythonBox = PythonBox(self, wx.NewId(), parent)
        self.currentBox = None
        #
        self.hideAll()
        self.Bind(wx.EVT_MOTION, lambda x: self.parent.sb.SetStatusText(''))

    def hideAll(self):
        self.materialBox.disable()
        self.materialEditBox.disable()
        self.materialDelBox.disable()
        #
        self.crossSectBox.disable()
        self.crossSectEditBox.disable()
        self.crossSectDelBox.disable()
        #
        self.nodeBox.disable()
        self.nodeEditBox.disable()
        self.nodeDelBox.disable()
        #
        self.elemBox.disable()
        self.elemEditBox.disable()
        self.elemDelBox.disable()
        #
        self.loadCaseBox.disable()
        self.loadCaseEditBox.disable()
        self.loadCaseDelBox.disable()
        #
        self.nodalLoadBox.disable()
        self.nodalLoadEditBox.disable()
        self.nodalLoadDelBox.disable()
        #
        self.pDsplBox.disable()
        self.pDsplEditBox.disable()
        self.pDsplDelBox.disable()
        #
        self.elementLoadBox.disable()
        self.elementLoadEditBox.disable()
        self.elementLoadDelBox.disable()
        #
        self.transformMeshBox.disable()
        self.modifyNodesBox.disable()
        #
        self.postProcessBox.disable()
        self.selectSolverBox.disable()
        self.scaleBox.disable()
        self.gridBox.disable()
        self.colorSetupBox.disable()
        self.pythonBox.disable()
        # Default focus for canvas  
        self.parent.canvas.SetFocus()
        #
        self.currentBox = None

    #emptyItem=0 do not add anything, emptyItem=1 add empty item and do not focus on it, emptyItem=2 add empty item and focus on it
    def updateCombo(self, name, domainEntities, item='', emptyItem=0, inInstance=None, directValue=''):
        dictNew = {}
        for key, value in domainEntities.items():
            if inInstance:
                if not isinstance(domainEntities[key], inInstance):
                   continue
            dictNew[key] = value
        name.Clear()
        if emptyItem:
            name.Append('')
        for s in sorted(dictNew.keys(), key=lambda n: natural_key(n)):
            name.Append(s)
        if emptyItem==2:
            name.SetValue('')
            return
        if item:
            name.SetValue(giveLabel(dictNew, item))
        if directValue:
            name.SetValue(directValue)


    def showMaterialBox(self):
        self.materialBox.enable()

    def showCrossSectBox(self):
        self.crossSectBox.enable()

    def showNodeBox(self):
        self.nodeBox.enable()

    def showElemBox(self):
        self.elemBox.enable()

    def showLoadCaseBox(self):
        self.loadCaseBox.enable()

    def showNodalLoadBox(self):
        self.nodalLoadBox.enable()

    def showPDsplBox(self):
        self.pDsplBox.enable()

    def showElementLoadBox(self):
        self.elementLoadBox.enable()

    def showMaterialEditBox(self):
        self.materialEditBox.enable()

    def showCrossSectEditBox(self):
        self.crossSectEditBox.enable()

    def showNodeEditBox(self):
        self.nodeEditBox.enable()

    def showElemEditBox(self):
        self.elemEditBox.enable()

    def showLoadCaseEditBox(self):
        self.loadCaseEditBox.enable()

    def showNodalLoadEditBox(self):
        self.nodalLoadEditBox.enable()

    def showPDsplEditBox(self):
        self.pDsplEditBox.enable()

    def showElementLoadEditBox(self):
        self.elementLoadEditBox.enable()

    def showMaterialDelBox(self):
        self.materialDelBox.enable()

    def showCrossSectDelBox(self):
        self.crossSectDelBox.enable()

    def showNodeDelBox(self):
        self.nodeDelBox.enable()

    def showElemDelBox(self):
        self.elemDelBox.enable()

    def showLoadCaseDelBox(self):
        self.loadCaseDelBox.enable()

    def showNodalLoadDelBox(self):
        self.nodalLoadDelBox.enable()

    def showPDsplDelBox(self):
        self.pDsplDelBox.enable()

    def showElementLoadDelBox(self):
        self.elementLoadDelBox.enable()

    def showTransformMeshBox(self):
        self.transformMeshBox.enable()

    def showModifyNodesBox(self):
        self.modifyNodesBox.enable()

    def showPostProcessBox(self):
        self.hideAll()
        self.postProcessBox.enable()
        

    def showSelectSolverBox(self):
        self.selectSolverBox.enable()

    def showScaleBox(self):
        self.scaleBox.enable()

    def showGridBox(self):
        self.gridBox.enable()

    def showColorSetupBox(self):
        self.colorSetupBox.enable()

    def showPythonBox(self):
        self.pythonBox.enable()


##################################################################
#
# GLFrame
#
##################################################################
class GLFrame(wx.Frame):
    """A simple class for using OpenGL with wxPython."""

    def __init__(self, parent, id, title, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE,
                 name='frame'):
        #
        # Forcing a specific style on the window.
        # Should this include styles passed?
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super(GLFrame, self).__init__(parent, id, title, pos, size, style, name)
        #super(GLFrame, self).__init__()
        self.dpi  = 35.0 # unit view length in window pixels.
        self.view = (-5.5, 5.5, -5.5, 5.5)
        #
        #handler to register left mouse event
        self.mouseLeftCB = None
        self.mouseMoveCB = None
        self.mouseSelectionCB = None
        self.sb = self.CreateStatusBar() # A Statusbar in the bottom of the window
        #selection cursor
        self.viewMode = True
        self.selectionCursor = wx.Cursor(wx.CURSOR_HAND)
        self.displayCursor   = wx.Cursor(wx.CURSOR_ARROW)
        self.selectionMode = NODE_MASK | ELEMENT_MASK
        self.multipleSelectionFlag = True
        self.selection = []
        self.selectionBeginPC = [0, 0, 0]

        # Setting up the menu.
        filemenu = wx.Menu()
        menuItem = wx.MenuItem(filemenu, -1, langStr('&New', '&Nový'), langStr('New problem', 'Nová úloha'))
        filemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.newFileMenu, menuItem)
        menuItem = wx.MenuItem(filemenu, -1, langStr('&Open', '&Otevřít')+'\tCtrl+O', langStr('Open an existing file', 'Otevřít existující soubor'))
        filemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.openFileMenu, menuItem)
        menuItem = wx.MenuItem(filemenu, -1, langStr('&Save', '&Uložit')+'\tCtrl+S', langStr('Save the file', 'Uložit do souboru'))
        filemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.saveFileMenu, menuItem)
        menuItem = wx.MenuItem(filemenu, -1, langStr('&Save as', '&Uložit jako')+'\tShift+Ctrl+S', langStr('Save the file as', 'Uložit do souboru jako'))
        filemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.saveFileAsMenu, menuItem)
        menuItem = wx.MenuItem(filemenu, -1, langStr('&Export graphics', '&Exportovat grafiku'), langStr('Save graphics to file', 'Uložit grafiku do souboru'))
        filemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.exportGraphics, menuItem)
        #
        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        #filemenu.Append(wx.ID_ABOUT, '&About',' Information about this program')
        filemenu.AppendSeparator()
        menuitem = filemenu.Append(wx.ID_EXIT,langStr('E&xit', 'U&končit')+'\tCtrl+Q',langStr('Terminate the program', 'Ukončit program'))
        self.Bind(wx.EVT_MENU, self.OnQuit, menuitem)
        #  
        # Creating the menubar.
        
        menuBar = wx.MenuBar(wx.MB_DOCKABLE)
        #menuBar = wx.MenuBar()
        menuBar.Append(filemenu,langStr('&File','&Soubor')) # Adding the 'filemenu' to the MenuBar
        #
        editmenu = wx.Menu()
        menuItem = wx.MenuItem(editmenu, -1, langStr('Undo', 'Zpět') + '\tCtrl+Z')
        editmenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.undo, menuItem)
        menuItem = wx.MenuItem(editmenu, -1, langStr('Redo', 'Vpřed') + '\tCtrl+Y')
        editmenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.redo, menuItem)
        editmenu.AppendSeparator()
        #
        imp = wx.Menu()
        menuItem = imp.Append(-1, langStr('Add material', 'Přidat materiál')+'\tCtrl+M')
        self.Bind(wx.EVT_MENU, self.addMaterial, menuItem)
        menuItem = imp.Append(-1, langStr('Add cross section', 'Přidat průřez')+'\tCtrl+R')
        self.Bind(wx.EVT_MENU, self.addCrossSect, menuItem)
        menuItem = imp.Append(-1, langStr('Add &node', 'Přidat &uzel')+'\tCtrl+N')
        self.Bind(wx.EVT_MENU, self.addNode, menuItem)
        menuItem = imp.Append(-1, langStr('Add element', 'Přidat prvek')+'\tCtrl+E')
        self.Bind(wx.EVT_MENU, self.addElement, menuItem)
        menuItem = imp.Append(-1, langStr('Add load case', 'Přidat zatěžovací stav')+'\tCtrl+D')
        self.Bind(wx.EVT_MENU, self.addLoadCase, menuItem)
        menuItem = imp.Append(-1, langStr('Add nodal load', 'Přidat uzlové zatížení')+'\tCtrl+F')
        self.Bind(wx.EVT_MENU, self.addNodalLoad, menuItem)
        menuItem = imp.Append(-1, langStr('Add prescribed displacement', 'Přidat předepsané přemístění')+'\tCtrl+I')
        self.Bind(wx.EVT_MENU, self.addPrescribedDspl, menuItem)
        menuItem = imp.Append(-1, langStr('Add element load', 'Přidat prvkové zatížení')+'\tCtrl+L')
        self.Bind(wx.EVT_MENU, self.addElementLoad, menuItem)
        editmenu.Append(-1, langStr('Add ...', 'Přidat ...'), imp)
        #
        imp = wx.Menu()
        menuItem = imp.Append(-1, langStr('Edit material', 'Upravit materiál')+'\tShift+Alt+M')
        self.Bind(wx.EVT_MENU, self.editMaterial, menuItem)
        menuItem = imp.Append(-1, langStr('Edit cross section', 'Upravit průřez')+'\tShift+Alt+R')
        self.Bind(wx.EVT_MENU, self.editCrossSect, menuItem)
        menuItem = imp.Append(-1, langStr('Edit node', 'Upravit uzel')+'\tShift+Alt+N')
        self.Bind(wx.EVT_MENU, self.editNode, menuItem)
        menuItem = imp.Append(-1, langStr('Edit element', 'Upravit prvek')+'\tShift+Alt+E')
        self.Bind(wx.EVT_MENU, self.editElement, menuItem)
        menuItem = imp.Append(-1, langStr('Edit load case', 'Upravit zatěžovací stav')+'\tShift+Alt+D')
        self.Bind(wx.EVT_MENU, self.editLoadCase, menuItem)
        menuItem = imp.Append(-1, langStr('Edit nodal load', 'Upravit uzlové zatížení')+'\tShift+Alt+F')
        self.Bind(wx.EVT_MENU, self.editNodalLoad, menuItem)
        menuItem = imp.Append(-1, langStr('Edit prescribed displacement', 'Upravit předepsané přemístění')+'\tShift+Alt+I')
        self.Bind(wx.EVT_MENU, self.editPrescribedDspl, menuItem)
        menuItem = imp.Append(-1, langStr('Edit element load', 'Upravit prvkové zatížení')+'\tShift+Alt+L')
        self.Bind(wx.EVT_MENU, self.editElementLoad, menuItem)
        editmenu.Append(-1, langStr('Edit ...', 'Upravit ...'), imp)
        #
        imp = wx.Menu()
        menuItem = imp.Append(-1, langStr('Delete material', 'Smazat materiál')+'\tCtrl+Shift+M')
        self.Bind(wx.EVT_MENU, self.delMaterial, menuItem)
        menuItem = imp.Append(-1, langStr('Delete cross section', 'Smazat průřez')+'\tCtrl+Shift+R')
        self.Bind(wx.EVT_MENU, self.delCrossSect, menuItem)
        menuItem = imp.Append(-1, langStr('Delete node', 'Smazat uzel')+'\tCtrl+Shift+N')
        self.Bind(wx.EVT_MENU, self.delNode, menuItem)
        menuItem = imp.Append(-1, langStr('Delete element', 'Smazat prvek')+'\tCtrl+Shift+E')
        self.Bind(wx.EVT_MENU, self.delElement, menuItem)
        menuItem = imp.Append(-1, langStr('Delete load case', 'Smazat zatěžovací stav')+'\tCtrl+Shift+D')
        self.Bind(wx.EVT_MENU, self.delLoadCase, menuItem)
        menuItem = imp.Append(-1, langStr('Delete nodal load', 'Smazat uzlové zatížení')+'\tCtrl+Shift+F')
        self.Bind(wx.EVT_MENU, self.delNodalLoad, menuItem)
        menuItem = imp.Append(-1, langStr('Delete prescribed displacement', 'Smazat předepsané přemístění')+'\tCtrl+Shift+I')
        self.Bind(wx.EVT_MENU, self.delPrescribedDspl, menuItem)
        menuItem = imp.Append(-1, langStr('Delete element load', 'Smazat prvkové zatížení')+'\tCtrl+Shift+L')
        self.Bind(wx.EVT_MENU, self.delElementLoad, menuItem)
        menuItem = imp.Append(-1, langStr('Delete all', 'Smazat všechno'))
        self.Bind(wx.EVT_MENU, self.delAll, menuItem)
        editmenu.Append(-1, langStr('Delete ...', 'Smazat'), imp)
        # meshing ...
        imp = wx.Menu()
        menuItem = imp.Append(-1, langStr('Copy/Translate', 'Kopíruj/Přesuň')+'\tCtrl+Shift+T')
        self.Bind(wx.EVT_MENU, self.transformMesh, menuItem)
        menuItem = imp.Append(-1, langStr('Modify nodes', 'Uprav uzly')+'\tCtrl+Shift+N')
        self.Bind(wx.EVT_MENU, self.modifyNodes, menuItem)
        editmenu.Append(-1, langStr('Modify mesh...', 'Úprava sítě...'), imp)
        
        #
        menuItem = editmenu.Append(-1, langStr('Scales', 'Měřítka')+'\tCtrl+H')
        self.Bind(wx.EVT_MENU, self.setScales, menuItem)
        menuItem = editmenu.Append(-1, langStr('Grid settings', 'Nastavení mřížky')+'\tCtrl+G')
        self.Bind(wx.EVT_MENU, self.setGrid, menuItem)
        menuItem = editmenu.Append(-1, langStr('Color settings', 'Barvy')+'\tCtrl+C')
        self.Bind(wx.EVT_MENU, self.setColors, menuItem)
        #
        menuItem = editmenu.Append(-1, 'Python\tCtrl+Shift+Alt+P')
        self.Bind(wx.EVT_MENU, self.showPython, menuItem)
        #
        menuBar.Append(editmenu,langStr('&Edit', '&Upravit')) # Adding the 'edit menu' to the MenuBar
        #
        viewmenu = wx.Menu()
        menuItem = viewmenu.Append(-1, langStr('Fit all', 'Přizpůsobit oknu'))
        self.Bind(wx.EVT_MENU, self.fitAll, menuItem)
        self.GridDisplayCheck = viewmenu.Append(-1, langStr('Show grid\tCtrl+1', 'Zobrazit mřížku\tCtrl+1'), langStr('Show Grid', 'Zobrazit mřížku'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleGrid, self.GridDisplayCheck)
        self.GridDisplayCheck.Check(globalFlags.gridDisplayFlag)
        self.SnapGridCheck = viewmenu.Append(-1, langStr('Snap to grid\tCtrl+2', 'Chytat na mřížku\tCtrl+2'), langStr('Snap to Grid','Chytat body na mřížku'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleSnap, self.SnapGridCheck)
        self.SnapGridCheck.Check(globalFlags.snapGridFlag)
        self.LabelDisplayCheck = viewmenu.Append(-1, langStr('Show labels\tCtrl+3', 'Zobrazit jména\tCtrl+3'), langStr('Show labels', 'Zobrazit jména'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleLabels, self.LabelDisplayCheck)
        self.LabelDisplayCheck.Check(globalFlags.labelDisplayFlag)
        self.NodeDisplayCheck = viewmenu.Append(-1, langStr('Show nodes\tCtrl+4', 'Zobrazit uzly\tCtrl+4'), langStr('Show nodes', 'Zobrazit uzly'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleNodes, self.NodeDisplayCheck)
        self.NodeDisplayCheck.Check(globalFlags.nodeDisplayFlag)
        self.BCDisplayCheck = viewmenu.Append(-1, langStr('Show BCs\tCtrl+5', 'Zobrazit okrajové podmínky\tCtrl+5'), langStr('Show boundary conditions', 'Zobrazit okrajové podmínky'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleBCs, self.BCDisplayCheck)
        self.BCDisplayCheck.Check(globalFlags.bcDisplayFlag)
        self.LoadDisplayCheck = viewmenu.Append(-1, langStr('Show Loads\tCtrl+6', 'Zobrazit zatížení\tCtrl+6'), langStr('Show loads', 'Zobrazit zatížení'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleLoads, self.LoadDisplayCheck)
        self.LoadDisplayCheck.Check(globalFlags.loadDisplayFlag)
        self.IntVarsValuesDisplayCheck = viewmenu.Append(-1, langStr('Show values\tCtrl+7', 'Zobrazit hodnoty\tCtrl+7'), langStr('Show values', 'Zobrazit hodnoty'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleValues, self.IntVarsValuesDisplayCheck)
        self.IntVarsValuesDisplayCheck.Check(globalFlags.valuesDisplayFlag)
        
        self.AxesDisplayCheck = viewmenu.Append(-1, langStr('Show axes\tCtrl+7', 'Zobrazit osy\tCtrl+7'), langStr('Show axes', 'Zobrazit osy'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleAxes, self.AxesDisplayCheck)
        self.AxesDisplayCheck.Check(globalFlags.axesDisplayFlag)
        # bp
        self.SelectionModeCheck = viewmenu.Append(-1, langStr('Selection mode\tCtrl+0', 'Režim výběru\tCtrl+0'), langStr('Selection mode', 'Režim výběru'), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleSelectionMode, self.SelectionModeCheck)
        self.SelectionModeCheck.Check(False)
        
        #
        menuBar.Append(viewmenu, langStr('&View', '&Zobrazit')) # Adding the 'view menu' to the MenuBar
        #
        solvemenu = wx.Menu()
        #menuItem = solvemenu.Append(-1, '&Check')
        #self.Bind(wx.EVT_MENU, self.checkSolve, menuItem)
        menuItem = wx.MenuItem(solvemenu, -1, langStr('&Solve\tCtrl+A', '&Výpočet úlohy\tCtrl+A'), langStr('Solve the problem', 'Vypočítat úlohu'))
        solvemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.solve, menuItem)
        menuItem = wx.MenuItem(solvemenu, -1, langStr('PostProcessor\tCtrl+P', 'PostProcessor\tCtrl+P'), langStr('Postprocess the problem', 'Zobrazit výsledky'))
        solvemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.postProcess, menuItem)
        menuItem = wx.MenuItem(solvemenu, -1, langStr('Select solver\tCtrl+W', 'Vybrat problém\tCtrl+W'), langStr('Select problem type', 'Vybrat typ úlohy'))
        solvemenu.Append(menuItem)
        self.Bind(wx.EVT_MENU, self.selectSolver, menuItem)

        #
        menuBar.Append(solvemenu, langStr('&Solve', '&Výpočet')) # Adding the 'Solve' to the MenuBar
        #
        help = wx.Menu()
        menuitem = help.Append(wx.ID_ABOUT, langStr('&About', '&O aplikaci'))
        self.Bind(wx.EVT_MENU, self.OnAboutBox, menuitem)
        menuBar.Append(help, langStr('&Help','&Nápověda'))# Adding the 'help menu' to the MenuBar
        #
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        
        ### Create glFrame toolBar###
        self.toolBar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL|wx.TB_FLAT|wx.TB_DOCKABLE)
        self.loadCaseChoice = ComboBoxWithHelp( self.toolBar, wx.NewId(), size=(200, -1), value=session.domain.activeLoadCase.label, choices=list(session.domain.loadCases.keys()), style=wx.CB_DROPDOWN, help = langStr('Load Case','Zatěžovací stav') )
        self.loadCaseChoice.Bind(wx.EVT_COMBOBOX,self.onChangeLoadCaseChoice)
        self.toolBar.AddControl(self.loadCaseChoice)
        self.toolBar.Realize()
        self.SetToolBar(self.toolBar) # Adding the ToolBar to the Frame content.

        #self.updateLoadCaseChoice()

        self.GLinitialized = False
        attribList = (glcanvas.WX_GL_RGBA, # RGBA
                      glcanvas.WX_GL_DOUBLEBUFFER, # Double Buffered
                      glcanvas.WX_GL_DEPTH_SIZE, 24) # 24 bit
        attribList = () #!!!
        
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.canvas = glcanvas.GLCanvas(self, attribList=attribList, size=canvasSize)
        
        if wx.MAJOR_VERSION >= 3:
            self.glContext = glcanvas.GLContext(self.canvas)
        self.context = Context(self, -1, size=(-1,-1), style=wx.SIMPLE_BORDER)
        self.sizer2.Add(self.context, proportion=0, flag=wx.EXPAND)
        self.sizer2.Add(self.canvas, proportion=1, flag=wx.EXPAND)
        self.sizer1.Add(self.sizer2, proportion=1, flag=wx.EXPAND)
        self.term = wx.TextCtrl(self, size=(-1,100), value = '', style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY) 
        #self.sizer1.AddSpacer(10) # to prevent overlaping of self.term and self.context
        self.sizer1.Add(self.term, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        self.SetSizerAndFit(self.sizer1)
        
        #self.canvas = glcanvas.GLCanvas(self, attribList=attribList, size=canvasSize)
        #self.context = Context(self, -1, size=(100,100), style=wx.SIMPLE_BORDER)
        #self.term = wx.TextCtrl(self, size=(-1,100), value = '', style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY) 
        #self.panel = wx.Panel(self, -1)
        #topSplitter = wx.SplitterWindow(self.panel)
        #hSplitter = wx.SplitterWindow(topSplitter)
        #hSplitter.SplitVertically(self.context, self.canvas)
        #hSplitter.SetSashGravity(0.5)
        #topSplitter.SplitHorizontally(hSplitter, self.term)
        #topSplitter.SetSashGravity(0.5)
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(topSplitter, 1, wx.EXPAND)
        #self.SetSizer(sizer)
        
        #redirect output
        if redirectTerm:
            sys.stdout = self.term
            sys.stderr = self.term
        #
        # Set the event handlers
        self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.canvas.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.canvas.Bind(wx.EVT_PAINT, self.processPaintEvent)
        self.canvas.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseScroll)
        #fixes mouse wheel zooming under Windows (problem of wxWidgets)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseScroll) 
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeft)
        self.canvas.Bind(wx.EVT_LEFT_UP  , self.OnMouseLeft)
        self.canvas.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseRight)
        #store full file name for Ctrl+S purposes
        self.fullFileName = ''
        # Default focus for canvas
        self.canvas.SetFocus()
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        #exit(0)
        # previews
        self.previewWhat = None
        self.previewKw = {}

    class MyPopupMenu(wx.Menu):  
        def __init__(self, parent, vc):
            wx.Menu.__init__(self)
            #
            self.parent = parent 
            self.vc = vc
            #
            name = langStr('Undo','Zpět')
            canUndo = session.canUndo()
            if canUndo:
                name += ': ' + session.giveNameOfUndo()
            item = wx.MenuItem(self, wx.NewId(), name )
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.parent.undo, item)
            item.Enable(canUndo)
            name = langStr('Redo','Vpřed')
            canRedo = session.canRedo()
            if canRedo:
                name += ': ' + session.giveNameOfRedo()
            item = wx.MenuItem(self, wx.NewId(), name )
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.parent.redo, item)
            item.Enable(canRedo)
            self.AppendSeparator()
            #
            #try to get closes object and adapt content
            (type, entity)=self.parent.findClosestComponent(self.vc[0], self.vc[2], 0.2)
            if type is Node:
                self.label = entity.label
                item = wx.MenuItem(self, wx.NewId(), langStr('Edit node %s','Editovat uzel %s') % self.label)  
                self.AppendItem(item)  
                self.Bind(wx.EVT_MENU, self.EditNode, item)  
                item = wx.MenuItem(self, wx.NewId(), langStr('Add load to node %s','Přidat zatížení k uzlu %s') % self.label)  
                self.AppendItem(item)  
                self.Bind(wx.EVT_MENU, self.AddNodalLoad, item)  
            if type is Element:
                self.label = entity.label
                item = wx.MenuItem(self, wx.NewId(), langStr('Edit element %s','Editovat prvek %s') % self.label)  
                self.AppendItem(item)  
                self.Bind(wx.EVT_MENU, self.EditElement, item)  
                item = wx.MenuItem(self, wx.NewId(), langStr('Add element load to element %s','Přidat prvkové zatížení k prvku %s') % self.label)  
                self.AppendItem(item)  
                self.Bind(wx.EVT_MENU, self.AddElementLoad, item) 
            if type is not None:
                self.AppendSeparator()
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Fit all','Zobraz vše'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.parent.fitAll, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom in', 'Zvětši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.parent.zoomIn, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom out','Zmenši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.parent.zoomOut, item)  

        def EditNode (self, event):
            self.parent.context.hideAll()
            self.parent.context.showNodeEditBox()
            self.parent.context.nodeEditBox.SetNodeLabel (self.label)

        def EditElement (self, event):
            self.parent.context.hideAll()
            self.parent.context.showElemEditBox()
            self.parent.context.elemEditBox.SetElementLabel (self.label)

        def AddNodalLoad(self, event):
            self.parent.context.hideAll()
            self.parent.context.showNodalLoadBox()
            self.parent.context.nodalLoadBox.SetNodeLabel (self.label)

        def AddElementLoad(self, event):
            self.parent.context.hideAll()
            self.parent.context.showElementLoadBox()
            self.parent.context.elementLoadBox.SetElementLabel (self.label)

        def OnClose(self, event):  
            self.parent.Close()  

    #
    # Canvas Proxy Methods

    def getGLExtents(self):
        """Get the extents of the OpenGL canvas."""
        return self.canvas.GetClientSize()

    def SwapBuffers(self):
        """Swap the OpenGL buffers."""
        self.canvas.SwapBuffers()

    #
    # wxPython Window Handlers

    def OnQuit(self, event):
        #close also open spreadsheet if exists
        if self.context.postProcessBox.spreadSheet:
            self.context.postProcessBox.spreadSheet.Destroy()
        self.context.pythonBox.quitShellFrames()
        from ebio import saveConfiguration
        saveConfiguration((globalSettings, globalGridSettings, globalSizesScales, globalFlags))
        # dialog to check unsaved file
        if not session.isSaved():
            dlg = wx.MessageDialog(self, langStr('Save file %s?', 'Uložit soubor %s?') % str(self.fullFileName), style=wx.CANCEL|wx.YES_NO|wx.ICON_QUESTION)#wx.YES_NO)
            result = dlg.ShowModal()
            if result == wx.ID_NO:
                pass # do nothing special
            elif result == wx.ID_YES:
                self.saveFileMenu(event)
            elif result == wx.ID_CANCEL:
                return
        logger.quit()
        self.Destroy() # frame

    def drawTrackRect(self, x1,z1,x2,z2):

        # set drawing mode to front-buffer
        glEnable(GL_COLOR_LOGIC_OP);
        glLogicOp(GL_XOR);
        # drawing different rubber-banding rectangle
        # depending on the mouse movement x-direction
        if(x1 < x2):
            glColor4f(0.0, 0.0, 1.0, 0.5);
        else:
            glColor4f(1.0, 0.0, 0.0, 0.5);

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
        # OpenGL window coordinates are different from GDI's
        #glRectd(x1, y1, x2, y2);
        glBegin(GL_LINE_LOOP)
        glVertex3f(x1,0.0,z1)
        glVertex3f(x2,0.0,z1)
        glVertex3f(x2,0.0,z2)
        glVertex3f(x1,0.0,z2)
        #glVertex3f(x1,0.0,z1)
        #glVertex3f(x2,0.0,z2)
        #glVertex3f(x1,0.0,z2)
        #glVertex3f(x1,0.0,z1)
        glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
        glFlush(); # must flush here
        glDisable(GL_COLOR_LOGIC_OP);

    def OnMouseMove(self, event):
        x, y = event.GetPosition()
        vc = projectCoordinates(x, y)
        if not vc: # related to Windows problem documented in projectCoordinates function
            return
        if event.Moving():
            if self.mouseMoveCB:
                self.mouseMoveCB(vc)
        elif event.ShiftDown() and event.Dragging():
            # zooming
            dir = y-self.lastmousexy[1]
            if dir>0:
                self.zoomIn()
            else:
                self.zoomOut()
        #
        elif (event.ControlDown() or event.MiddleIsDown()) and event.Dragging():
            # panning
            #panx=vc[0]-self.lastmousevc[0]
            #pany=vc[1]-self.lastmousevc[1]
            #panz=vc[2]-self.lastmousevc[2]
            panx =((x-self.lastmousexy[0])/self.dpi)
            panz =((y-self.lastmousexy[1])/self.dpi)
            #
            (viewLeft, viewRight, viewBottom, viewTop) = self.view
            viewLeft = viewLeft-panx
            viewRight = viewRight-panx
            viewBottom = viewBottom+panz
            viewTop = viewTop+panz
            self.view = (viewLeft, viewRight, viewBottom, viewTop)
            #
            # refresh gl scene
            size = self.getGLExtents()
            self.OnReshape(size.width, size.height)
            self.canvas.Refresh(False)
        elif (event.LeftIsDown() and event.Dragging() ):
            glDrawBuffer(GL_FRONT);
            #erase old one
            self.drawTrackRect(self.selectionBeginPC[0], self.selectionBeginPC[2],self.lastmousevc[0], self.lastmousevc[2])            
            #draw rectangle 
            self.drawTrackRect(self.selectionBeginPC[0], self.selectionBeginPC[2],vc[0], vc[2])
            #print "drawTrackRect (",self.selectionBeginPC[0], self.selectionBeginPC[2],vc[0], vc[2],")"
            glDrawBuffer(GL_BACK);

        # remember current position as last position
        self.lastmousevc = vc
        self.lastmousexy = (x,y)
        #get closest snap point
        if globalFlags.snapGridFlag:
            snapx = math.ceil((vc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridSnap[0]-0.5)*globalGridSettings.gridSnap[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((vc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridSnap[1]-0.5)*globalGridSettings.gridSnap[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = vc[0]
            snapz = vc[2]
        #
        self.sb.SetStatusText ('[x: {0:f}, z: {1:f}]'.format(snapx,snapz))


    def OnMouseLeft(self, event):
        #self.canvas.SetFocus()#Do not focus here - keyboard shortcuts need to focus other widgets than canvas
        x, y = event.GetPosition()
        vc = projectCoordinates(x, y)
        #remember last position
        self.lastmousevc=vc
        self.lastmousexy=(x,y)
        if (event.LeftDown() and self.viewMode):
           # copy display buffer to a texture to enable fast drawing of zoom rectagle over fixed buffer texture
           #glBindTexture(GL_TEXTURE_2D, 1)
           #(x,y,width, height)=glGetIntegerv(GL_VIEWPORT)
           #glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, width,height)
           self.selectionBeginPC = vc
           #view mode
           if event.ControlDown():
              self.mousemode=1 #paning
           elif event.ShiftDown():
              self.mousemode=2 #zooming
           else:
              # click - handle if registered handler
              if self.mouseLeftCB:
                 self.mouseLeftCB(vc)
        elif (event.LeftDown() and not self.viewMode):
           #selection mode
           self.selectionBeginPC = vc
           self.selectionBeginMC = self.lastmousexy
           vc1 = projectCoordinates(x-5,y-5)
           vc2 = projectCoordinates(x+5,y+5)
           bbox = BBox(vc1, vc2)
           #if event.ControlDown(): # add to selection
           #    pass
           #else:
           #    self.selection = []
           #self.createSelection(self.selection, bbox, self.selectionMode)
           #if self.mouseSelectionCB: self.mouseSelectionCB(self.selection)
        elif (event.LeftUp() and not self.viewMode):
           #selection mode
           #filter out the LeftUp and LeftDown on the same position
           if (self.selectionBeginMC != self.lastmousexy): 
              bbox = BBox((min(self.selectionBeginPC[0], vc[0]), min(self.selectionBeginPC[1], vc[1]), min(self.selectionBeginPC[2], vc[2])),
                          (max(self.selectionBeginPC[0], vc[0]), max(self.selectionBeginPC[1], vc[1]), max(self.selectionBeginPC[2], vc[2])))
           else:
               vc1 = projectCoordinates(x-10,y-10)
               vc2 = projectCoordinates(x+10,y+10)
               bbox = BBox(vc1, vc2)
           
           self.createSelection(bbox, self.selectionMode)
           try:
               logger.info( langStr("Selected: ", "Výběr: ") + ", ".join(s.label for s in self.selection) ) # TODO
               if self.mouseSelectionCB: self.mouseSelectionCB(self.selection)
           except:
               None
        elif event.RightUp():
            #
            panx = vc[0]-self.panOrigin[0]
            pany = vc[1]-self.panOrigin[1]
            panz = vc[2]-self.panOrigin[2]
            #
            (viewLeft, viewRight, viewBottom, viewTop) = self.view
            viewLeft = viewLeft-panx
            viewRight = viewRight-panx
            viewBottom = viewBottom+panz
            viewTop = viewTop+panz
            self.view=(viewLeft, viewRight, viewBottom, viewTop)
        #
        #refresh gl scene
        size = self.getGLExtents()
        self.OnReshape(size.width, size.height)
        self.canvas.Refresh(False)

    def OnMouseRight(self, event):
        x, y = event.GetPosition()
        vc = projectCoordinates(x, y)
        self.canvas.PopupMenu(self.MyPopupMenu(self, vc), event.GetPosition())
            
    def fitAll(self, event=None):
        init = True
        delta = 0.0
        for n in session.domain.nodes.values():
            (x,y,z) = n.coords
            if init:
                minx = x
                minz = z
                maxx = x
                maxz = z
                init = False
            else:
                minx = min(minx,x)
                maxx = max(maxx,x)
                minz = min(minz,z)
                maxz = max(maxz,z)
        if not init:
            delta = max(maxx-minx, maxz-minz)

        #get window size
        size = self.getGLExtents()
        if (not init) and (delta>0.0):
            f = delta*0.1
            minx = minx-f
            maxx = maxx+f
            minz = minz-f
            maxz = maxz+f
            #
            # set up view
            self.view = (minx,maxx,-maxz,-minz)
            #update dpi
            self.dpi = max((min(float(size.width)/(maxx-minx), float(size.height)/(maxz-minz))), 1.0)
        #
        # refresh gl scene
        self.OnReshape(size.width, size.height)
        self.canvas.Refresh(False)
        self.canvas.SetFocus()

    def resetSolverAndPostprocessBox(self, event=None):
        session.solver.reset()
        self.context.postProcessBox.reset()
        if self.context.postProcessBox.spreadSheet:
            self.context.postProcessBox.spreadSheet.Destroy()

    def autoScale(self, event=None):
        if not session.solver.isSolved:
            logger.warning( langStr('Problem has not been solved yet ...', 'Úloha ještě není vypočtena ...') )
            return
        ratio = 0.2 # maximal displayed value has size ratio*dim
        dim = session.domain.giveMaxDim()
        maxw,maxf = 1.e-6, 1.e-6 # max deflection, max internal force, set to prevent zero division
        for elem in session.domain.elements.values():
            u,w = elem.computeDefl(session.solver.giveActiveSolutionVector())
            w = max(max([abs(i) for i in u]),max([abs(i) for i in w]))
            if w > maxw:
                maxw = w
            distances, N, labelMask = elem.computeNormalForce(session.solver.giveActiveSolutionVector())
            distances, V, labelMask = elem.computeShearForce(session.solver.giveActiveSolutionVector())
            distances, M = elem.computeMoment(session.solver.giveActiveSolutionVector())
            f = max(max([abs(i) for i in N]),max([abs(i) for i in V]),max([abs(i) for i in M]))
            if f > maxf:
                maxf = f
        globalSizesScales.deformationScale = ratio*dim/maxw
        self.context.scaleBox.defGeom.SetValue(str('{0:.3g}'.format(float(globalSizesScales.deformationScale))))
        globalSizesScales.intForceScale = ratio*dim/maxf
        self.context.scaleBox.intForces.SetValue(str('{0:.3g}'.format(float(globalSizesScales.intForceScale))))
        self.context.postProcessBox.defGeom.SetValue(str('{0:.3g}'.format(float(globalSizesScales.deformationScale))))
        self.context.postProcessBox.intForces.SetValue(str('{0:.3g}'.format(float(globalSizesScales.intForceScale))))
        #
        self.canvas.Refresh(False)

    def zoomIn(self, event=None):
        self.dpi = self.dpi*1.1
        #refresh gl scene
        size = self.getGLExtents()
        self.OnReshape(size.width, size.height)
        self.canvas.Refresh(False)      

    def zoomOut(self, event=None):
        self.dpi = self.dpi/1.1
        #refresh gl scene
        size = self.getGLExtents()
        self.OnReshape(size.width, size.height)
        self.canvas.Refresh(False)      
        
    def OnMouseScroll(self, event):
        if not self.canvas == self.FindFocus():
            return event.Skip()
        direction = event.GetWheelRotation()
        if direction>0: 
            self.zoomIn()
        else:
            self.zoomOut()

    def onChangeLoadCaseChoice(self, event=None):
        session.domain.changeActiveLoadCaseTo(self.loadCaseChoice.GetValue())
        session.solver.lcsChanged() # notify solver
        #update autoscale in post processor
        if session.solver.isSolved:
            self.autoScale(event)
        #update opened spreadsheet
        if self.context.postProcessBox.spreadSheet:
            self.context.postProcessBox.ResultsToSpreadsheet(event)
            self.Raise()
        #Update selections for load cases
        if self.context.pDsplEditBox:
            self.context.pDsplEditBox.onLoadCaseChange(event)
        if self.context.pDsplDelBox:
            self.context.pDsplDelBox.onLoadCaseChange(event)
        if self.context.nodalLoadEditBox:
            self.context.nodalLoadEditBox.onLoadCaseChange(event)
        if self.context.nodalLoadDelBox:
            self.context.nodalLoadDelBox.onLoadCaseChange(event)
        if self.context.elementLoadEditBox:
            self.context.elementLoadEditBox.onLoadCaseChange(event)
        if self.context.elementLoadDelBox:
            self.context.elementLoadDelBox.onLoadCaseChange(event)
            
        self.canvas.Refresh(False)

    def processEraseBackgroundEvent(self, event):
        """Process the erase background event."""
        pass # Do nothing, to avoid flashing on MSWin

    def processSizeEvent(self, event):
        """Process the resize event."""
        #if self.canvas.GetContext():
        if self.canvas:  #!!!
        #if self.glContext:
            print('Need to update', self.glContext)
            #self.canvas.draw()
            #self.Update()
            #self.Show()
            #self.canvas.SetCurrent(self.glContext)
            #self.canvas.Show()
            #self.canvas.Update() 
            #self.canvas.Refresh(False)
            
            # Make sure the frame is shown before calling SetCurrent.
            #self.Show()
            #self.canvas.SetCurrent()
            ##
            #size = self.getGLExtents()
            #self.OnReshape(size.width, size.height)
            #self.canvas.Refresh(False)
        event.Skip()

    def processPaintEvent(self, event):
        """Process the drawing event."""
        self.canvas.SetCurrent(glcanvas.GLContext(self.canvas))
        try:
            glDrawBuffer(GL_BACK);#Windows-related problem of zeros in GL_BACK
        except:
            pass
        #
        # This is a 'perfect' time to initialize OpenGL ... only if we need to
        if not self.GLinitialized:
            self.OnInitGL()
            self.GLinitialized = True
        #
        self.OnDraw()
        event.Skip()

    def addMaterial (self, event):
        self.context.hideAll()
        self.context.showMaterialBox()

    def addCrossSect (self, event):
        self.context.hideAll()
        self.context.showCrossSectBox()

    def addNode (self, event):
        self.context.hideAll()
        self.context.showNodeBox()

    def addElement (self, event):
        self.context.hideAll()
        self.context.showElemBox()

    def addLoadCase (self, event):
        self.context.hideAll()
        self.context.showLoadCaseBox()

    def addNodalLoad (self, event):
        self.context.hideAll()
        self.context.showNodalLoadBox()

    def addPrescribedDspl (self, event):
        self.context.hideAll()
        self.context.showPDsplBox()

    def addElementLoad (self, event):
        self.context.hideAll()
        self.context.showElementLoadBox()

    def editMaterial (self, event):
        self.context.hideAll()
        self.context.showMaterialEditBox()

    def editCrossSect (self, event):
        self.context.hideAll()
        self.context.showCrossSectEditBox()

    def editNode (self, event):
        self.context.hideAll()
        self.context.showNodeEditBox()

    def editElement (self, event):
        self.context.hideAll()
        self.context.showElemEditBox()

    def editLoadCase (self, event):
        self.context.hideAll()
        self.context.showLoadCaseEditBox()

    def editNodalLoad (self, event):
        self.context.hideAll()
        self.context.showNodalLoadEditBox()

    def editPrescribedDspl (self, event):
        self.context.hideAll()
        self.context.showPDsplEditBox()

    def editElementLoad (self, event):
        self.context.hideAll()
        self.context.showElementLoadEditBox()

    def delMaterial (self, event):
        self.context.hideAll()
        self.context.showMaterialDelBox()

    def delCrossSect (self, event):
        self.context.hideAll()
        self.context.showCrossSectDelBox()

    def delNode (self, event):
        self.context.hideAll()
        self.context.showNodeDelBox()

    def delElement (self, event):
        self.context.hideAll()
        self.context.showElemDelBox()

    def delLoadCase (self, event):
        self.context.hideAll()
        self.context.showLoadCaseDelBox()

    def delNodalLoad (self, event):
        self.context.hideAll()
        self.context.showNodalLoadDelBox()

    def delPrescribedDspl (self, event):
        self.context.hideAll()
        self.context.showPDsplDelBox()

    def delElementLoad (self, event):
        self.context.hideAll()
        self.context.showElementLoadDelBox()

    def transformMesh (self, event):
        self.context.hideAll()
        self.context.showTransformMeshBox()

    def modifyNodes (self, event):
        self.context.hideAll()
        self.context.showModifyNodesBox()

    def delAll (self, event):
        session.domain.reset(isUndoable=True)
        self.updateLoadCaseChoice()
        self.canvas.Refresh(False)

    def toggleGrid(self, event):
        globalFlags.gridDisplayFlag = self.GridDisplayCheck.IsChecked()
        self.canvas.Refresh(False)

    def toggleSnap(self, event):
        globalFlags.snapGridFlag = self.SnapGridCheck.IsChecked()
        #self.canvas.Refresh(False)

    def toggleLabels(self, event):
        globalFlags.labelDisplayFlag = self.LabelDisplayCheck.IsChecked()
        self.canvas.Refresh(False)

    def toggleNodes(self, event):
        globalFlags.nodeDisplayFlag = self.NodeDisplayCheck.IsChecked()
        self.canvas.Refresh(False)
    
    def toggleBCs(self, event):
        globalFlags.bcDisplayFlag = self.BCDisplayCheck.IsChecked()
        self.canvas.Refresh(False)
    
    def toggleLoads(self, event):
        globalFlags.loadDisplayFlag = self.LoadDisplayCheck.IsChecked()
        self.canvas.Refresh(False)
        
    def toggleValues(self, event):
        globalFlags.valuesDisplayFlag = self.IntVarsValuesDisplayCheck.IsChecked()
        self.canvas.Refresh(False)
        

    def toggleAxes(self, event):
        globalFlags.axesDisplayFlag = self.AxesDisplayCheck.IsChecked()
        self.canvas.Refresh(False)

    def toggleSelectionMode(self, event):
        self.viewMode = not self.SelectionModeCheck.IsChecked()
        if self.viewMode:
           # selection on
           self.canvas.SetCursor(self.displayCursor)
        else:
           # selection off -> display mode
           self.canvas.SetCursor(self.selectionCursor)

    def toggleUniLoadSize(self, event):
        i = globalSizesScales.useUniLoadSize
        globalSizesScales.useUniLoadSize = 0 if i else 1
        self.canvas.Refresh(False)

    def setSelectionMode(self, selectionMask, multipleSelectionFlag=True):
        # selectionMask allows to select components (nodes, elements) participating in selection
        # multipleSelectionFlag set to True allows selection of multiple objects
        self.viewMode = False
        self.selectionMode = selectionMask
        self.multipleSelectionFlag = multipleSelectionFlag
        self.canvas.SetCursor(self.selectionCursor)

    def resetSelection(self):
        self.selection=[]

    def addToSelection(self, obj):
        try:
            # look if node already selected
            i = self.selection.index(obj)
        except ValueError:
            self.selection.append(obj)

    def setViewMode(self):
        self.viewMode = True
        self.canvas.SetCursor(self.displayCursor)
        
        
    def updateLoadCaseChoice(self):
        self.loadCaseChoice.Clear()
        self.loadCaseChoice.AppendItems([key for key in sorted(session.domain.loadCases.iterkeys())])
        self.loadCaseChoice.SetValue( session.domain.activeLoadCase.label if session.domain.activeLoadCase else '' )
       
    def checkSolve(self, event):
        pass

    def solve(self, event=None):
        logger.info( langStr('Solving the problem', 'Počítám úlohu') )
        session.solver.solve()
        self.autoScale(event)

    def postProcess(self, event):
        self.context.hideAll()
        self.context.showPostProcessBox()

    def selectSolver(self, event):
        self.context.hideAll()
        self.context.showSelectSolverBox()

    def setScales(self, event):
        self.context.hideAll()
        self.context.showScaleBox()

    def setGrid(self, event):
        self.context.hideAll()
        self.context.showGridBox()

    def setColors(self, event):
        self.context.hideAll()
        self.context.showColorSetupBox()
       
    def showPython(self, event):
        self.context.hideAll()
        self.context.showPythonBox()

    def setFrameTitle(self, originalChanged):
        if originalChanged == 0:
            self.SetTitle('EduBeam ver. %s %s' % (version, str(self.fullFileName) ))
        else:
            self.SetTitle('*EduBeam ver. %s %s' % (version, str(self.fullFileName) ))

    def openFile(self, path):
        self.context.postProcessBox.reset()
        self.context.hideAll()
        globalFlags.deformationDisplayFlag = False
        globalFlags.intForcesDisplayFlag = [False,False,False,False]
        if session.load(path):
            dlg = wx.MessageDialog(self, langStr('Error opening file\n', 'Chyba při otvírání souboru\n') + str(error))
            dlg.ShowModal()
            return True
        session.resetCommnads()
        self.fullFileName = path
        self.sb.SetStatusText(langStr('File load OK', 'Soubor se nahrál správně'))
        self.modify = False
        self.updateLoadCaseChoice()
        self.canvas.Refresh(False)
        session.solver.reset()
        return False
    
    def execPythonScript(self, fileName):
        if fileName == os.path.basename(fileName):
            fileName = os.path.join(os.getcwd(),fileName)
        try:
            execfile(fileName)
        except Exception as err:
            print ("External file %s exception:" %fileName)
            print (err)
        
    def newFileMenu(self, event):
        #close also open spreadsheet if exists
        if not session.isSaved():
            dlg = wx.MessageDialog(self, langStr('Save file %s?', 'Uložit soubor %s?') % str(self.fullFileName), style=wx.CANCEL|wx.YES_NO|wx.ICON_QUESTION)#wx.YES_NO)
            result = dlg.ShowModal()
            if result == wx.ID_NO:
                pass # do nothing special
            elif result == wx.ID_YES:
                self.saveFileMenu(event)
            elif result == wx.ID_CANCEL:
                return
        if self.context.postProcessBox.spreadSheet:
            self.context.postProcessBox.spreadSheet.Destroy()
        self.context.postProcessBox.reset()
        self.context.hideAll()
        session.domain.reset()
        session.resetCommnads()
        self.sb.SetStatusText(langStr('New problem created', 'Nová úloha vytvořena'))
        self.modify = False
        self.canvas.Refresh(False)
        self.fullFileName = ''
        self.SetTitle('EduBeam ver. %s' % (version))
    
    def openFileMenu(self, event):
        wcd = langStr('Xml files (*.xml)|*.xml;*.XML;*.Xml|Oofem files (*.oofem)|*.oofem;*.OOFEM;*.Oofem|All files (*)|*', 'Xml soubory (*.xml)|*.xml;*.XML;*.Xml|Oofem soubory (*.oofem)|*.oofem;*.OOFEM;*.Oofem|Všechny soubory (*)|*')
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message=langStr('Choose a file', 'Vyber soubor'), defaultDir=dir, defaultFile='',
                                 wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            try:
                self.openFile(path)
            except IOError as error:
                dlg = wx.MessageDialog(self, langStr('Error opening file\n', 'Chyba při otvírání souboru\n') + str(error))
                dlg.ShowModal()
            self.setFrameTitle(0)
        open_dlg.Destroy()

    def saveFileMenu(self, event):
        if not self.fullFileName: # there is no filename associated
            self.saveFileAsMenu(event)
        else:
            if session.save(self.fullFileName):
                dlg = wx.MessageDialog(self, langStr('Error saving file\n', 'Chyba při ukládání souboru\n') + str(error))
                dlg.ShowModal()
                return True
            self.sb.SetStatusText( langStr('Session successfully saved to file %s','Úloha úspěšně uložena do souboru %s') % (str(self.fullFileName)) )
            self.modify = False
            self.canvas.Refresh(False)
        session.setAsSaved()
        self.setFrameTitle(0)
        return False

    def saveFileAsMenu(self, event):
        wcd = langStr('Xml files (*.xml)|*.xml;*.XML;*.Xml|Oofem files (*.oofem)|*.oofem;*.OOFEM;*.Oofem|All files (*)|*', 'Xml soubory (*.xml)|*.xml;*.XML;*.Xml|Oofem soubory (*.oofem)|*.oofem;*.OOFEM;*.Oofem|Všechny soubory (*)|*')
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message=langStr('Enter a file for saving', 'Zadej soubor pro uložení'), defaultDir=dir, defaultFile='',
                                 wildcard=wcd, style=wx.SAVE|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            if open_dlg.GetFilterIndex() == 0: # chosen xml
                pl = path.lower()
                if not pl.endswith('.xml'):
                    path += ".xml" # append .xml if missing
            elif open_dlg.GetFilterIndex() == 1: # chosen oofem
                pl = path.lower()
                if not pl.endswith('.oofem'):
                    path += ".oofem" # append .oofem if missing
            if os.path.isfile(path): # if the file already exists
                dlg = wx.MessageDialog(self, langStr('File %s already exists. Overwrite?\n', 'Soubor %s již existuje. Přepsat?\n') % path, style=wx.YES_NO)
                if dlg.ShowModal() == wx.ID_NO:
                    return
                dlg.Destroy()
            if session.save(path):
                dlg = wx.MessageDialog(self, langStr('Error saving file\n', 'Chyba při ukládání souboru\n') + str(error))
                dlg.ShowModal()
                return True
            self.fullFileName = path
            self.sb.SetStatusText('')
            self.modify = False
            self.canvas.Refresh(False)
            session.setAsSaved()
            self.setFrameTitle(0)
        open_dlg.Destroy()
    
    def exportGraphics(self, event):
        wcd = langStr('png files (*.png)|*.png|All files (*)|*', 'png soubory (*.png)|*.png|Všechny soubory (*)|*')
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message=langStr('Choose a file', 'Vyber soubor'), defaultDir=dir, defaultFile='',
                                 wildcard=wcd, style=wx.SAVE|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            if not path.endswith('.png'):
                path += '.png'

            self.canvas.Refresh(False)
            size = self.getGLExtents()
            view = glGetIntegerv(GL_VIEWPORT)
            img = wx.EmptyImage(view[2], view[3] )
            glPixelStorei(GL_PACK_ALIGNMENT, 1) ;
            pixels = glReadPixels(0, 0, view[2], view[3], GL_RGB, GL_UNSIGNED_BYTE)
            img.SetData( pixels )
            img = img.Mirror(False)
            try:
                img.SaveFile(path, wx.BITMAP_TYPE_PNG)
            except IOError as error:
                dlg = wx.MessageDialog(self, langStr('Error opening file\n', 'Chyba při otvírání souboru\n') + str(error))
                dlg.ShowModal()
            #
            except UnicodeDecodeError as error:
                dlg = wx.MessageDialog(self, langStr('Error opening file\n', 'Chyba při otvírání souboru\n') + str(error))
                dlg.ShowModal()

    def findClosestComponent(self,x,z,mind=1e30,type=None,onlyActiveLC=True):
        minl2 = mind
        ret  = None
        retType = None
        if type is None or type is Node:
            for node in session.domain.nodes.values():
                c = node.coords
                l2 = (c[0]-x)*(c[0]-x) + (c[2]-z)*(c[2]-z)
                if l2<minl2:
                    minl2 = l2
                    ret = node
                    retType = Node
        if type is None or type is Element:
            for elem in session.domain.elements.values():
                cc = elem.computeCenter()
                l2 = (0.5*(cc[0]-x)*(cc[0]-x) + (cc[2]-z)*(cc[2]-z) )
                if l2<minl2:
                    minl2 = l2
                    ret = elem
                    retType = Element
        if type is NodalLoad:
            retType = NodalLoad
            node = self.findClosestNode(x,z,mind)
            if node:
                loads = session.domain.giveNodalLoadsOnNode(node,onlyActiveLC)
                if loads:
                    ret = loads[-1]
        if type is PrescribedDisplacement:
            retType = PrescribedDisplacement
            node = self.findClosestNode(x,z,mind)
            if node:
                pDspls = session.domain.givePrescribedDsplsOnNode(node,onlyActiveLC)
                if pDspls:
                    ret = pDspls[-1]
        if type is ElementLoad:
            retType = ElementLoad
            elem = self.findClosestElement(x,z,mind)
            if elem:
                loads = session.domain.giveElementLoadsOnElement(elem,onlyActiveLC)
                if loads:
                    ret = loads[-1]
        return retType, ret

    def findClosestNode(self,x,z,mind=1e30):
        return self.findClosestComponent(x,z,mind,Node)[1]

    def findClosestElement(self,x,z,mind=1e30):
        return self.findClosestComponent(x,z,mind,Element)[1]

    def findClosestNodalLoad(self,x,z,mind=1e30,onlyActiveLC=True):
        return self.findClosestComponent(x,z,mind,NodalLoad,onlyActiveLC)[1]

    def findClosestPrescribedDspl(self,x,z,mind=1e30,onlyActiveLC=True):
        return self.findClosestComponent(x,z,mind,PrescribedDisplacement,onlyActiveLC)[1]

    def findClosestElementLoad(self,x,z,mind=1e30,onlyActiveLC=True):
        return self.findClosestComponent(x,z,mind,ElementLoad,onlyActiveLC)[1]

    def giveSelectionModeName(self,selectionMode):
        temp = []
        if selectionMode & NODE_MASK:
            temp.append( langStr('nodes', 'uzly') )
        if selectionMode & ELEMENT_MASK:
            temp.append( langStr('elements', 'prvky') )
        return ", ".join(temp)

    #bp-selection
    def createSelection (self,bbox,selectionMode):
       logger.info( langStr("Selection mode: ", "Mód výběru: ") + self.giveSelectionModeName(selectionMode) )
       if not self.multipleSelectionFlag:
           self.resetSelection()
       if selectionMode & NODE_MASK:
           for node in session.domain.nodes.values():
               if node.isInside(bbox):
                   try:
                       # look if node already selected
                       i = self.selection.index(node)
                       # then delete it from selection
                       del self.selection[i]
                   except ValueError:
                       # not in selection => add
                       self.selection.append(node)
                       if not self.multipleSelectionFlag:
                           break

       if selectionMode & ELEMENT_MASK:
           for elem in session.domain.elements.values():
               if elem.isInside(bbox):
                   try:
                       # look if element already selected
                       i = self.selection.index(elem)
                       # then delete it from selection
                       del self.selection[i]
                   except ValueError:
                       # not in selection => add
                       self.selection.append(elem)
                       if not self.multipleSelectionFlag:
                           break


    def hilitSelection (self, selection):
       backup_node_color = globalSettings.nodeColor
       globalSettings.nodeColor =  globalSettings.hilitColor
       backup_elem_color = globalSettings.elemColor
       globalSettings.elemColor = globalSettings.hilitColor
       #
       if selection != [None]:
          for i in selection:
              i.OnDraw()
       #
       globalSettings.nodeColor =  backup_node_color
       globalSettings.elemColor =  backup_elem_color

    def onMouseLeft_selection (self, event):
       x, y = event.GetPosition()
       vc = projectCoordinates(x, y)
       if event.LeftDown():
          self.selectionbbox_initvc = vc
          return
       elif event.LeftUp():
          bbox = BBox(self.selectionbbox_initvc,vc,self.selectionMode)
          #self.selection=[]
          self.createSelection(bbox)
          return
       return





    #
    # GLFrame OpenGL Event Handlers

    def OnInitGL(self):
        """Initialize OpenGL for use in the window."""
        if wx.MAJOR_VERSION >= 3:
            self.canvas.SetCurrent(self.glContext)
        glClearColor(1, 1, 1, 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        (viewLeft, viewRight, viewBottom, viewTop) = self.view
        #make sure the view proportions remain same 
        size = self.getGLExtents()
        self.view = (viewLeft, (viewLeft+size.width/self.dpi), viewBottom, (viewBottom+size.height/self.dpi))
        (viewLeft, viewRight, viewBottom, viewTop) = self.view
        glOrtho(viewLeft, viewRight, viewBottom, viewTop, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        OpenGL.GLU.gluLookAt(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0);

    def OnReshape(self, width, height):
        """Reshape the OpenGL viewport based on the dimensions of the window."""
        glViewport(0, 0, width, height)
        #
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        #
        (viewLeft, viewRight, viewBottom, viewTop) = self.view
        midpoint = (viewLeft+(viewRight - viewLeft)/2, viewTop+(viewBottom - viewTop)/2)
        #make sure the view proportions remain same 
        #self.view = (viewLeft, (viewLeft+width/self.dpi), viewBottom, (viewBottom+height/self.dpi))
        self.view = (midpoint[0]-width/self.dpi/2, midpoint[0]+width/self.dpi/2, midpoint[1]-height/self.dpi/2, midpoint[1]+height/self.dpi/2)
        #
        (viewLeft, viewRight, viewBottom, viewTop) = self.view
        glOrtho(viewLeft, viewRight, viewBottom, viewTop, -1, 1)
        #
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        OpenGL.GLU.gluLookAt(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0);

    def OnDraw(self, *args, **kwargs):
        """Draw the window."""
        glClear(GL_COLOR_BUFFER_BIT)
        #
        if globalFlags.gridDisplayFlag:
            self.drawGrid (globalGridSettings.gridOrigin, globalGridSettings.gridDelta, globalGridSettings.gridCount) 
        if globalFlags.axesDisplayFlag:
            self.drawAxes()
        self.drawCopyright()
        #
        self.preview()
        #
        for elem in session.domain.elements.values():
            elem.OnDraw()
        for node in session.domain.nodes.values():
            node.OnDraw()
        lc = session.domain.activeLoadCase
        useUniformSize = int(globalSizesScales.useUniLoadSize)
        if lc and lc.displayFlag:
            for container in (lc.nodalLoads,lc.elementLoads,lc.prescribedDspls):
                for load in container.values():
                    load.OnDraw(useUniformSize=useUniformSize)
        #hilit selected items
        self.hilitSelection(self.selection) 
        #
        try:
            if isResultFlag():
                if not session.solver.isSolved:
                    raise EduBeamError
                if isBeamResultFlag():
                    for elem in session.domain.elements.values():
                        elem.OnDrawResults(session.solver.giveActiveSolutionVector())
                if globalFlags.intForcesDisplayFlag[3]:
                    for node in session.domain.nodes.values():
                        node.OnDrawResults(useUniformSize=useUniformSize)
        #
        except EduBeamError:
            logger.warning( langStr('Problem has not been solved yet ...', 'Úloha ještě není vypočtena ...') )
        #
        self.SwapBuffers()

    def preview(self):
        if not self.previewWhat:
            return
        w,kw = self.previewWhat, self.previewKw
        if w == 'node' and self.context.currentBox is self.context.nodeBox:
            coords = kw['coords']
            size = kw.get('size',6.)
            color = globalSettings.previewColor
            glPointSize(size)
            glColor3f(color[0],color[1],color[2])
            glBegin(GL_POINTS)
            glVertex3f(coords[0],coords[1],coords[2])
            glEnd()
        elif w == 'element' and self.context.currentBox is self.context.elemBox:
            lw = kw.get('lineWidth',2.)
            color = globalSettings.previewColor
            nodes = kw.get('nodes')
            c1,c2 = nodes[0].coords, nodes[1].coords
            glLineWidth(lw)
            glColor3f(color[0],color[1],color[2])
            glBegin(GL_LINES)
            glVertex3f(c1[0],c1[1],c1[2])
            glVertex3f(c2[0],c2[1],c2[2])
            glEnd()
        glDefaultColor()

    def resetPreview(self):
        self.previewWhat = None
        self.previewKw = {}
        self.canvas.Refresh(False)

    def setPreview(self,what,**kw):
        self.previewWhat = what
        self.previewKw = kw
        self.canvas.Refresh(False)

    def drawGrid(self, origin, delta, count):
        #'Draw a grid'
        xs = origin[0]
        zs = origin[1]
        xe = xs+delta[0]*count
        ze = zs+delta[1]*count
        c = 0
        #
        glEnable(GL_LINE_STIPPLE)
        glLineWidth (1.0);
        glLineStipple (1, 0x0101);  # dotted  
        glColor(0, 0, 0)
        glBegin(GL_LINES)
        while c<count+1:
            x = xs+c*delta[0]
            glVertex3f(x, 0.0, zs)
            glVertex3f(x, 0.0, ze)
            c = c+1
        c = 0
        while c<count+1:
            z = zs+c*delta[1]
            glVertex3f(xs, 0.0, z)
            glVertex3f(xe, 0.0, z)
            c = c+1
        glEnd()
        glDisable(GL_LINE_STIPPLE)
        glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
        glDefaultColor()

    def drawAxes (self):
        """Draws a constant size axes """
        size = self.getGLExtents()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix ()
        #
        glLoadIdentity()
        glViewport (0,size.y-20,20,20)
        glOrtho(-0.2,1., -1., 0.2, -1, 1.)
        glLineWidth (2.0);
        #
        glBegin (GL_LINES);
        glColor3f (1,0,0); # X axis is red.
        glVertex3f (0.,0.,0.);
        glVertex3f (1.,0.,0. );
        glColor3f (0,1,0); # Y axis is green.
        glVertex3f (0.,0.,0.);
        glVertex3f (0.,1.,0. );
        glColor3f (0,0,1); # z axis is blue.
        glVertex3f (0.,0.,0.);
        glVertex3f (0.,0.,1.);
        glEnd();
        #
        size = self.getGLExtents()
        glViewport (0,0,size.x,size.y)
        glPopMatrix ();
        glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
        glDefaultColor()

    def drawCopyright (self):       
        size = self.getGLExtents()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix ()
        #
        glLoadIdentity()
        glViewport (0,0,size.x,size.y)
        glOrtho(0.,1., 0., 1., 0., 1.)
        #glLineWidth (2.0);
        glColor(0,0,1)
        glPrintString (0,0,0, 'EduBeam ver. '+version)
        glDefaultColor()
        size = self.getGLExtents()
        glViewport (0,0,size.x,size.y)
        glPopMatrix ();

    def OnAboutBox(self, event):
        #
        info = wx.AboutDialogInfo()
        #
        #info.SetIcon(wx.Icon('icons/hunter.png', wx.BITMAP_TYPE_PNG))
        info.SetName('EduBeam')
        info.SetVersion(version)
        info.SetDescription(description())
        info.SetCopyright('(C) 2011 Bořek Patzák')
        info.SetWebSite('http://mech.fsv.cvut.cz/edubeam')
        info.SetLicence(licence)
        info.AddDeveloper('Bořek Patzák')
        info.AddDeveloper('Jan Stránský')
        info.AddDeveloper('Vít Šmilauer')
        #info.AddDocWriter('Borek Patzak')
        #info.AddArtist('The Tango crew')
        #info.AddTranslator('Borek Patzak')
        #
        wx.AboutBox(info)

    def undo(self, event):
        self.resetPreview()
        currentBox = self.context.currentBox
        self.context.hideAll()
        session.undo()
        if currentBox:
            currentBox.enable()
        self.canvas.Refresh(False)

    def redo(self, event):
        self.resetPreview()
        currentBox = self.context.currentBox
        self.context.hideAll()
        session.redo()
        if currentBox:
            currentBox.enable()
        self.canvas.Refresh(False)
    





##################################################################
#
# Control panels
#
##################################################################
class MaterialBox(wx.Panel):
    helpE = langStr('Young\'s modulus','Youngův modul pružnosti')
    helpG = langStr('Shear modulus','Smykový modul pružnosti')
    helpAlpha = langStr('Coefficient of thermal expansion','Součinitel délkové teplotní roztažnosti')

    def __init__(self, parent, id, glframe, mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add Material', 'Přidat materiál'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, giveLabel(session.domain.materials,'newNum'), labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit Material', 'Editovat materiál'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete Material', 'Smazat materiál'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, langStr('Map to existing material:', 'Mapuj na existující materiál:'), (10, 65) )
            self.comboDelNew = wx.ComboBox(self, -1, pos=(100,95), size=(100, -1), style=wx.CB_READONLY)

        if mode == 'add' or mode == 'edit':
            #TextCtrl bindings are below
            wx.StaticBox(self, -1, langStr('Material parameters', 'Parametry materiálu'), (5,85), (200, 120))
            StaticTextWithHelp(self, -1, 'E: ', (10, 105), (-1,-1), help=self.helpE)
            self.e = wx.TextCtrl(self, -1, '30.e+6',  (100, 105), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, -1, 'G: ', (10, 135), (-1,-1), help=self.helpG)
            self.g = wx.TextCtrl(self, -1, '10.e+6',  (100, 135), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, -1, 'alpha: ', (10, 165), (-1,-1), help=self.helpAlpha)
            self.alpha = wx.TextCtrl(self, -1, '12.e-6',  (100, 165), (100, -1), style=wx.TE_PROCESS_ENTER)
        #
        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            self.e.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.g.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.alpha.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnAdd)
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            self.e.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.g.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.alpha.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        #
        wx.Button(self, 2, langStr('&Close', 'Zavři (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove=None

    def enable(self, show=True):
        self.SetFocus()
        if self.mode=='add':
            self.labelText.SetValue(giveLabel(session.domain.materials,'newNum'))
        elif self.mode=='edit':
            label = giveLabel(session.domain.materials,'last')
            self.parent.updateCombo(self.comboEdit, session.domain.materials, 'last')
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.materials, 'last')
            self.parent.updateCombo(self.comboDelNew, session.domain.materials, '', 2)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()

    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.labelText.GetValue()
        e = self.e.GetValue()
        g = self.g.GetValue()
        alpha = self.alpha.GetValue()
        if not session.domain.addMaterial(label=label,e=e,g=g,alpha=alpha,isUndoable=True):
            # adding failed
            return
        self.labelText.SetValue(giveLabel(session.domain.materials,'newNum'))
        self.glframe.Refresh(False)
        #self.glframe.canvas.SetFocus()

    def editLabel(self, event=None):
        label=self.comboEdit.GetValue()
        mat = session.domain.materials.get(label)
        if mat:
            self.e.SetValue(str('{0:.4g}'.format(mat.e)))
            self.g.SetValue(str('{0:.4g}'.format(mat.g)))
            self.alpha.SetValue(str('{0:.4g}'.format(mat.alpha)))
            return
        elif not label:
            self.e.SetValue('')
            self.g.SetValue('')
            self.alpha.SetValue('')
            logger.debug( langStr('Material %s not found in the materials %s', 'Materiál %s nebyl nalezen  v materiálech %s') % ( label, sorted(session.domain.materials.keys()) ) )
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.materials, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboEdit.GetValue()
        mat = label
        newLabel = self.newlabelText.GetValue()
        e = self.e.GetValue()
        g = self.g.GetValue()
        alpha = self.alpha.GetValue()
        if newLabel:
            self.comboEdit.SetValue(newLabel)
        if session.domain.changeMaterial(mat,label=newLabel if newLabel else label,e=e,g=g,alpha=alpha,isUndoable=True):
            return#unsuccessful
        print (session.domain.materials)
        self.parent.updateCombo(self.comboEdit, session.domain.materials, 'last')
        self.newlabelText.SetValue('')
        self.glframe.Refresh(False)
        #self.glframe.canvas.SetFocus()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboDel.GetValue()
        newLabel = self.comboDelNew.GetValue()
        if session.domain.delMaterial(label,newMat=newLabel,isUndoable=True):
            # deleting failed
            return
        self.parent.updateCombo(self.comboDel, session.domain.materials, 'last')
        self.parent.updateCombo(self.comboDelNew, session.domain.materials, '', 2)
        self.glframe.Refresh(False)

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()


class CrossSectBox(wx.Panel):
    helpA  = langStr('Cross section area','Průřezová plocha')
    helpIy = langStr('Second moment of area I_y','Moment setrvačnosti I_y') # TODO second moment of area?
    helpH  = langStr('Height of the cross section','Výška průřezu')
    helpK  = langStr('Timoshenko\'s shear coefficient','Timoshenkův smykový součinitel')
    def __init__(self, parent, id, glframe, mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add CrossSection', 'Přidat průřez'), (0,0), mainBoxSize)
            self.labelText = wx.StaticText(self, -1, langStr('Label: ', 'Jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, giveLabel(session.domain.crossSects,'newNum'), labelEntPos, (100, -1), style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit CrossSection', 'Editovat průřez'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            #self.newlabelText.Bind(wx.EVT_KILL_FOCUS, self.OnChange)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete CrossSection', 'Smazat průřez'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, langStr('Map to existing CrossSection:', 'Mapuj na existující průřez:'), (10, 65) )
            self.comboDelNew = wx.ComboBox(self, -1, pos=(100,95), size=(100, -1), style=wx.CB_READONLY)
        #
        if mode == 'add' or mode == 'edit':
            #TextCtrl bindings are below
            wx.StaticBox(self, -1, langStr('CrossSection parameters', 'Průřezové charakteristiky'), (5,85), (200, 145))
            #A default rectangle 0.2 x 0.3 m
            StaticTextWithHelp(self, -1, 'A: ', (10, 105), (-1,-1), help=self.helpA)
            self.a = wx.TextCtrl(self, -1, '0.06',  (100, 105), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, -1, 'Iy: ', (10, 135), (-1,-1), help=self.helpIy)
            self.iy = wx.TextCtrl(self, -1, '4.5e-4',  (100, 135), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, -1, 'h: ', (10, 165), (-1,-1), help=self.helpH)
            self.h = wx.TextCtrl(self, -1, '0.3',  (100, 165), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, -1, 'k (kappa): ', (10, 195), (-1,-1), help=self.helpK)
            self.k = wx.TextCtrl(self, -1, '0.833333',  (100, 195), (100, -1), style=wx.TE_PROCESS_ENTER)
        #
        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            wx.EVT_BUTTON(self, 1, self.OnAdd)
            self.a.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.iy.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.h.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.k.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            btn.SetFocus()
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            self.a.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.iy.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.h.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.k.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        self.SetFocus()
        if self.mode=='add': 
            self.labelText.SetValue(giveLabel(session.domain.crossSects,'newNum'))
        elif self.mode=='edit':
            label = giveLabel(session.domain.crossSects,'last')
            self.parent.updateCombo(self.comboEdit, session.domain.crossSects, 'last')
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.crossSects, 'last')
            self.parent.updateCombo(self.comboDelNew, session.domain.crossSects, '', 2)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()

    def OnAdd(self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label=self.labelText.GetValue()
        a = self.a.GetValue()
        iy = self.iy.GetValue()
        h = self.h.GetValue()
        k = self.k.GetValue()
        if not session.domain.addCrossSect(label=label,a=a,iy=iy,dyz=0.0, h=h, k=k,isUndoable=True):
            # adding failed
            return
        self.labelText.SetValue(giveLabel(session.domain.crossSects,'newNum'))
        self.glframe.Refresh(False)
        #self.glframe.canvas.SetFocus()

    def editLabel(self, event=None):
        label=self.comboEdit.GetValue()
        cs = session.domain.crossSects.get(label)
        if cs:
            self.a.SetValue(str('{0:.4g}'.format(cs.a)))
            self.iy.SetValue(str('{0:.4g}'.format(cs.iy)))
            self.h.SetValue(str('{0:.4g}'.format(cs.h)))
            self.k.SetValue(str('{0:.4g}'.format(cs.k)))
            return
        if not label:
            logger.debug( langStr('CrossSection %s not found in the crossSections %s' 'Průřez %s nebyl nalezen v průřezech %s') % (label, sorted(session.domain.crossSects.keys()) ) )
            self.a.SetValue('')
            self.iy.SetValue('')
            self.h.SetValue('')
            self.k.SetValue('')
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.crossSects, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label=self.comboEdit.GetValue()
        cs = label
        newLabel = self.newlabelText.GetValue()
        a = self.a.GetValue()
        iy = self.iy.GetValue()
        h = self.h.GetValue()
        k = self.k.GetValue()
        if newLabel:
            self.comboEdit.SetValue(newLabel)
        if session.domain.changeCrossSect(cs,label=newLabel if newLabel else label,a=a,iy=iy,h=h,k=k,isUndoable=True):
            # changing failed
            return
        self.parent.updateCombo(self.comboEdit, session.domain.crossSects, 'last')
        self.newlabelText.SetValue('')
        self.glframe.Refresh(False)
        #self.glframe.canvas.SetFocus()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboDel.GetValue()
        newLabel = self.comboDelNew.GetValue()
        if session.domain.delCrossSect(label,newCS=newLabel,isUndoable=True):
            # deleting failed
            return
        self.parent.updateCombo(self.comboDel, session.domain.crossSects, 'last')
        self.parent.updateCombo(self.comboDelNew, session.domain.crossSects, '', 2)
        self.glframe.Refresh(False)

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()



class NodeBox(wx.Panel):
    helpX   = langStr('Coordinate x','Souřadnice x')
    helpZ   = langStr('Coordinate z','Souřadnice z')
    helpBcX    = langStr('Boundary condition in x direction','Okrajová podmínka ve směru x')
    helpBcZ    = langStr('Boundary condition in z direction','Okrajová podmínka ve směru z')
    helpBcRotY = langStr('Boundary condition in rotation','Okrajová podmínka v rotaci')
    def __init__(self, parent, id, glframe, mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add Node', 'Přidat uzel'), (0,0), mainBoxSize)
            self.labelText = wx.StaticText(self, -1, langStr('Label: ', 'Jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, giveLabel(session.domain.nodes,'newNum'), labelEntPos, (100, -1), style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, wx.NewId(), langStr('Edit Node', 'Editovat uzel'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1) )
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_KILL_FOCUS, self.editLabel)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, wx.NewId(), langStr('Delete Node', 'Smazat uzel'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1) )

        if mode == 'add' or mode == 'edit':
            wx.StaticBox(self, wx.NewId(), langStr('Node coordinates', 'Souřadnice uzlu'), (5,85), (200, 100))
            StaticTextWithHelp(self, wx.NewId(), 'x: ', (10, 105), (-1,-1), help=self.helpX)
            self.xc = wx.TextCtrl(self, -1, '0', (30, 105), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self, wx.NewId(), 'z: ', (10, 135), (-1,-1), help=self.helpZ)
            self.zc = wx.TextCtrl(self, -1, '0',  (30, 135), (100, -1), style=wx.TE_PROCESS_ENTER)
            wx.StaticBox(self, wx.NewId(), langStr('Boundary conditions', 'Okrajové podmínky'), (5,190), (200, 225))
            xx = 60
            ww = 130
            zz = 210
            self.bcu = CheckBoxWithHelp(self,wx.NewId(),'u', (10,zz), help=self.helpBcX)
            zz += 30
            self.bcw = CheckBoxWithHelp(self,wx.NewId(),'w', (10,zz), help=self.helpBcZ)
            zz += 30
            self.bcr = CheckBoxWithHelp(self,wx.NewId(),'r', (10,zz), help=self.helpBcRotY)

        if mode=='add':
            self.addBtn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            wx.EVT_BUTTON(self, 1, self.OnAdd)
            self.xc.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.zc.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.xc.Bind(wx.EVT_KEY_UP, self.preview)
            self.zc.Bind(wx.EVT_KEY_UP, self.preview)
            self.addBtn.SetFocus()
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            wx.EVT_BUTTON(self, 1, self.OnChange)
            self.xc.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.zc.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)

        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None

    def preview(self,event=None):
        if (self.mode=='add' or self.mode=='edit'):
            try:
                x = float(self.xc.GetValue())
                z = float(self.zc.GetValue())
            except ValueError:
                return
            coords = (x,0.,z)
            self.glframe.setPreview('node',coords=coords)

    def enable(self, show=True):
        # update
        if self.mode=='add':
            self.labelText.SetValue(giveLabel(session.domain.nodes,'newNum'))
        elif self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.nodes)
            if not self.comboEdit.GetValue():#skip if the key exists (mouse, last edited item). If the position does not exist, set the last one.
                self.parent.updateCombo(self.comboEdit, session.domain.nodes, 'last')
            self.editLabel(None)
            self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            self.glframe.setSelectionMode(NODE_MASK, False)
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.nodes, 'last')
            self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            self.glframe.setSelectionMode(NODE_MASK, True)
            
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        self.glframe.mouseMoveCB = self.OnMouseMoveCB
        #self.glframe.canvas.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.glframe.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        #
        self.Show(show)
        self.parent.currentBox = self
        self.preview()

    def disable(self):
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = None
        self.glframe.mouseMoveCB = None
        self.glframe.resetPreview()
        self.Hide()
 
    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label=self.labelText.GetValue()
        coords = (self.xc.GetValue(), 0.0, self.zc.GetValue())
        bcs = {
            'x':self.bcu.GetValue(),
            'z':self.bcw.GetValue(),
            'Y':self.bcr.GetValue()}
        if not session.domain.addNode(label=label, coords=coords, bcs=bcs, isUndoable=True):
            # adding failed
            return
        self.labelText.SetValue(giveLabel(session.domain.nodes,'newNum'))
        
        self.glframe.Refresh(False)
        # register mouse move handler - to continue adding new node(s)
        self.glframe.mouseMoveCB = self.OnMouseMoveCB
        self.glframe.canvas.SetFocus()
        
    def editLabel(self, event=None):
        label=self.comboEdit.GetValue()
        node = session.domain.nodes.get(label)
        #highlight selected node
        self.glframe.resetSelection()
        self.glframe.addToSelection(node)
        self.glframe.Refresh(False)

        if node:
            self.xc.SetValue(str('{0:.4g}'.format(node.coords[0])))
            self.zc.SetValue(str('{0:.4g}'.format(node.coords[2])))
            self.bcu.SetValue(node.bcs['x'])
            self.bcw.SetValue(node.bcs['z'])
            self.bcr.SetValue(node.bcs['Y'])
            return
        elif not label:
            logger.debug( langStr('Node %s not found in the nodes %s', 'Uzel %s nebyl nalezen v uzlech %s') % ( label, sorted(session.domain.nodes.keys()) ) )
            self.xc.SetValue('')
            self.zc.SetValue('')
            self.bcu.SetValue(False)
            self.bcw.SetValue(False)
            self.bcr.SetValue(False)
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.nodes, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if len(selection)>1: # nodes selected
            bcs = {
                'x':self.bcu.GetValue(),
                'z':self.bcw.GetValue(),
                'Y':self.bcr.GetValue()
            }
            if session.domain.changeNodes(selection,bcs=bcs,isUndoable=True):
                # failed
                return
            self.glframe.resetSelection()
        else:
            if selection:
                self.comboEdit.SetValue(selection[0].label)
            label=self.comboEdit.GetValue()
            node = label
            newLabel = self.newlabelText.GetValue()
            coords = [float(self.xc.GetValue()), 0.0, float(self.zc.GetValue())]
            bcs = {
                'x':self.bcu.GetValue(),
                'z':self.bcw.GetValue(),
                'Y':self.bcr.GetValue()
            }
            if newLabel:
                self.comboEdit.SetValue(newLabel)
            if session.domain.changeNode(node,label=newLabel if newLabel else label,coords=coords,bcs=bcs,isUndoable=True):
                # changing failed
                return
        self.parent.updateCombo(self.comboEdit, session.domain.nodes, 'last')
        self.newlabelText.SetValue('')
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if len(selection)>1: # nodes selected
            if session.domain.delNodes(selection,isUndoable=True):
                # deleting failed
                return
            self.glframe.resetSelection()
        else:
            if selection:
                self.comboDel.SetValue(selection[0].label)
                self.glframe.resetSelection()
            label = self.comboDel.GetValue()
            if session.domain.delNode(label,isUndoable=True):
                # deleting failed
                return
        self.parent.updateCombo(self.comboDel, session.domain.nodes, 'last')
        self.glframe.Refresh(False)

    def SetNodeLabel(self, label):
        if self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.nodes, 0)
            self.comboEdit.SetValue(str(label))
        self.editLabel()

    def OnMouseMoveCB(self, mc):
        #get closest snap point
        if globalFlags.snapGridFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridSnap[0]-0.5)*globalGridSettings.gridSnap[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridSnap[1]-0.5)*globalGridSettings.gridSnap[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0])
            snapz = (mc[2])
        #snapx = math.ceil((mc[0]-globalSizesScales.gridOrigin[0])/globalSettings.gridDelta[0]-0.5)*globalSettings.gridDelta[0]+globalSizesScales.gridOrigin[0]
        #snapz = math.ceil((mc[2]-globalSizesScales.gridOrigin[1])/globalSettings.gridDelta[1]-0.5)*globalSettings.gridDelta[1]+globalSizesScales.gridOrigin[1]
        #if self.mode != 'del':
        if self.mode == 'add':
            self.xc.SetValue(str(snapx))
            self.zc.SetValue(str(snapz))
        self.preview()

    def OnMouseSelectionCB (self, selection):
        if (len(selection) == 1):
            if self.mode == 'edit':
                self.comboEdit.SetValue(selection[0].label)
                tmp = selection[0]
                self.xc.SetValue(str('{0:.4g}'.format(tmp.coords[0])))
                self.zc.SetValue(str('{0:.4g}'.format(tmp.coords[2])))
                self.bcu.SetValue(tmp.bcs['x'])
                self.bcw.SetValue(tmp.bcs['z'])
                self.bcr.SetValue(tmp.bcs['Y'])
               
            if self.mode == 'del':
                self.comboDel.SetValue(selection[0].label)
        else:
            #multiple selection -> need to hide element label 
            pass
        self.SetFocus()
 
    def OnMouseLeftDownCB(self, mc):
        #get closest snap point
        if globalFlags.snapGridFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridSnap[0]-0.5)*globalGridSettings.gridSnap[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridSnap[1]-0.5)*globalGridSettings.gridSnap[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0])
            snapz = (mc[2])
        #snapx = math.ceil((mc[0]-globalSizesScales.gridOrigin[0])/globalSettings.gridDelta[0]-0.5)*globalSettings.gridDelta[0]+globalSizesScales.gridOrigin[0]
        #snapz = math.ceil((mc[2]-globalSizesScales.gridOrigin[1])/globalSettings.gridDelta[1]-0.5)*globalSettings.gridDelta[1]+globalSizesScales.gridOrigin[1]
        if self.mode == 'add':
            self.xc.SetValue(str(snapx))
            self.zc.SetValue(str(snapz))
            # unregister mouse move handler - to keep last coords
            self.glframe.mouseMoveCB = None
            self.preview()
            self.SetFocus()
        elif self.mode == 'del':
            node = self.glframe.findClosestNode(snapx,snapz)
            self.comboDel.SetValue(node.label)
        elif self.mode=='edit':
            node = self.glframe.findClosestNode(snapx,snapz)
            self.comboEdit.SetValue(node.label)
            self.xc.SetValue(str(node.coords[0]))
            self.zc.SetValue(str(node.coords[2]))
            self.bcu.SetValue(node.bcs['x'])
            self.bcw.SetValue(node.bcs['z'])
            self.bcr.SetValue(node.bcs['Y'])

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()




class ElemBox(wx.Panel):
    def __init__(self, parent, id, glframe, mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        self.editNodeFlag = 0
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add Element', 'Přidat prvek'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, '', labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit Element', 'Editovat prvek'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_KILL_FOCUS, self.editLabel)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete Element', 'Smazat prvek'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1) )
        
        if mode == 'add' or mode == 'edit':
            wx.StaticText(self, -1, langStr('Node 1: ', 'Uzel 1: '), (10, 95))
            self.comboN1 = wx.ComboBox(self, -1, pos=(100, 95), size=(100, -1) )
            self.comboN1.Bind(wx.EVT_COMBOBOX, self.preview)
            wx.StaticText(self, -1, langStr('Node 2: ', 'Uzel 2:'), (10, 125))
            self.comboN2 = wx.ComboBox(self, -1, pos=(100, 125), size=(100, -1) )
            self.comboN2.Bind(wx.EVT_COMBOBOX, self.preview)
            wx.StaticText(self, -1, langStr('Material: ', 'Materiál: '), (10, 155))
            self.comboMat = wx.ComboBox(self, -1, pos=(100, 155), size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, langStr('CrossSect: ', 'Průřez: '), (10, 185))
            self.comboCS = wx.ComboBox(self, -1, pos=(100, 185), size=(100, -1), style=wx.CB_READONLY)
            self.leftHinge = wx.CheckBox(self, -1, langStr('Start hinge', 'Kloub na počátku'), (10,220))
            self.rightHinge = wx.CheckBox(self, -1, langStr('End hinge', 'Kloub na konci'), (10,250))
            self.parent.updateCombo(self.comboMat, session.domain.materials, 'last')
            self.parent.updateCombo(self.comboCS, session.domain.crossSects, 'last')
        #
        if mode=='add':
            self.parent.updateCombo(self.comboN1, session.domain.nodes, 'first')
            self.parent.updateCombo(self.comboN2, session.domain.nodes, 'last')
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            wx.EVT_BUTTON(self, 1, self.OnAdd)
            btn.SetFocus()
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        #
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove=None

    def preview(self,event=None):
        n1Val,n2Val = self.comboN1.GetValue(), self.comboN2.GetValue()
        if not n1Val or not n2Val:
            return
        n1 = session.domain.giveNode(self.comboN1.GetValue())
        n2 = session.domain.giveNode(self.comboN2.GetValue())
        if not n1 or not n2:
            return
        self.glframe.setPreview('element',nodes=[n1,n2])

    def enable(self, show=True):
        #self.SetFocus()
        # update labels
        if self.mode=='add':
            self.labelText.SetValue(giveLabel(session.domain.elements,'newNum'))
            self.parent.updateCombo(self.comboN1, session.domain.nodes, 'first')
            self.parent.updateCombo(self.comboN2, session.domain.nodes, 'last')
            self.parent.updateCombo(self.comboMat, session.domain.materials, 'last')
            self.parent.updateCombo(self.comboCS, session.domain.crossSects, 'last')
            self.preview()
        elif self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.elements, 'last')
            self.parent.updateCombo(self.comboMat, session.domain.materials, 'last')
            self.parent.updateCombo(self.comboCS, session.domain.crossSects, 'last')
            self.editLabel()
            self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            self.glframe.setSelectionMode(ELEMENT_MASK, False)
            self.preview()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.elements, 'last')
            self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            self.glframe.setSelectionMode(ELEMENT_MASK, True)

        #
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        #        self.glframe.mouseMoveCB = self.OnMouseMoveCB
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.glframe.resetPreview()
        self.Hide()

    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        n1 = self.comboN1.GetValue()
        n2 = self.comboN2.GetValue()
        mat = self.comboMat.GetValue()
        cs = self.comboCS.GetValue()
        label = self.labelText.GetValue()
        hinges = [self.leftHinge.GetValue(),self.rightHinge.GetValue()]
        if not session.domain.addElement(label=label, nodes=(n1,n2), mat=mat, cs=cs, hinges=hinges,isUndoable=True):
            # adding failed
            return
        self.labelText.SetValue(giveLabel(session.domain.elements,'newNum'))
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()        

    def editLabel(self, event=None):
        label=self.comboEdit.GetValue()
        elem = session.domain.elements.get(label)
        #highlight selected elemtn
        self.glframe.resetSelection()
        self.glframe.addToSelection(elem)
        self.glframe.Refresh(False)

        if elem:
            self.parent.updateCombo(self.comboN1, session.domain.nodes)
            self.parent.updateCombo(self.comboN2, session.domain.nodes)
            self.comboN1.SetValue(elem.nodes[0].label)
            self.comboN2.SetValue(elem.nodes[1].label)
            self.comboMat.SetValue(elem.mat.label)
            self.comboCS.SetValue(elem.cs.label)
            self.leftHinge.SetValue(elem.hinges[0])
            self.rightHinge.SetValue(elem.hinges[1])
            return
        elif not label:
            logger.debug( langStr('Element %s not found in the elements %s', 'Prvek %s nebyl nalezen v prvcích %s') % ( label, sorted(session.domain.elements.keys()) ) )
            self.parent.updateCombo(self.comboN1, session.domain.nodes, 2)
            self.parent.updateCombo(self.comboN2, session.domain.nodes, 2)
            self.comboMat.SetValue('')
            self.comboCS.SetValue('')
            self.leftHinge.SetValue(0)
            self.rightHinge.SetValue(0)
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.elements, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboEdit.GetValue()
        elem = label
        newLabel = self.newlabelText.GetValue()
        n1 = self.comboN1.GetValue()
        n2 = self.comboN2.GetValue()
        mat = self.comboMat.GetValue()
        cs = self.comboCS.GetValue()
        hinges = [self.leftHinge.GetValue(), self.rightHinge.GetValue()]
        if newLabel:
            self.comboEdit.SetValue(newLabel)
        if session.domain.changeElement(elem,label=newLabel if newLabel else label,nodes=[n1,n2],mat=mat,cs=cs,hinges=hinges, isUndoable=True):
            # changing failed
            return
        self.parent.updateCombo(self.comboEdit, session.domain.elements, 'last')
        self.newlabelText.SetValue('')
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if len(selection)>1: # elements selected
            if session.domain.delElements(selection,isUndoable=True):
                # deleting failed
                return
            self.glframe.resetSelection()
        else:
            if selection:
                self.comboDel.SetValue(selection[0].label)
                self.glframe.resetSelection()
            label = self.comboDel.GetValue()
            if session.domain.delElement(label,isUndoable=True):
                # deleting failed
                return
        self.parent.updateCombo(self.comboDel, session.domain.elements, 'last')
        self.glframe.Refresh(False)

    def OnMouseSelectionCB(self, selection):
        if (len(selection) == 1):
            if self.mode == 'edit':
                self.comboEdit.SetValue(selection[0].label)
                tmp = selection[0]
                self.comboN1.SetValue(tmp.nodes[0].label)
                self.comboN2.SetValue(tmp.nodes[1].label)
                self.comboMat.SetValue(tmp.mat.label)
                self.comboCS.SetValue(tmp.cs.label)
                self.leftHinge.SetValue(tmp.hinges[0])
                self.rightHinge.SetValue(tmp.hinges[1])

            if self.mode == 'del':
                self.comboDel.SetValue(selection[0].label)
        else:
            #multiple selection -> need to hide element label 
            pass
        self.SetFocus()

    def OnMouseLeftDownCB(self, mc):
        #get closest snap point
        if globalFlags.gridDisplayFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]-0.5)*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]-0.5)*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = (mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        # unregister mouse move handler - to keep last coords
        self.glframe.mouseMoveCB = None
        if self.mode == 'edit' or self.mode == 'del':
            if len(session.domain.elements)==0:
                return
            elem = self.glframe.findClosestElement(snapx,snapz)
            if self.mode == 'edit':
                self.comboEdit.SetValue(elem.label)
                self.editLabel(None)
            elif self.mode == 'del':
                self.comboDel.SetValue(elem.label)
        elif self.mode == 'add':
            if len(session.domain.nodes)==0:
                return
            node = self.glframe.findClosestNode(snapx,snapz)
            if self.editNodeFlag == 0:
                self.comboN1.SetValue(node.label)
                self.editNodeFlag = 1
            elif self.editNodeFlag == 1:
                self.comboN2.SetValue(node.label)
                self.editNodeFlag = 0
            self.preview()
        self.SetFocus()

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def SetElementLabel(self, label):
        if self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.elements, 0)
            self.comboEdit.SetValue(str(label))
        self.editLabel(None)
 



class LoadCaseBox(wx.Panel):
    def __init__(self, parent, id, glframe,mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add load case', 'Přidat zatěžovací stav'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, '', labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit load case', 'Editovat zatěžovací stav'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete load case', 'Smazat zatěžovací stav'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.Bind(wx.EVT_TEXT_ENTER, self.editLabel)
            
        if mode == 'add' or mode == 'edit':
            pass
        #
        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnAdd)
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        self.SetFocus()
        if self.mode=='add':#used also in mouse edit
            self.labelText.SetValue( "LC_"+giveNewLabel( session.domain.loadCases, 'newNum') )
        elif self.mode=='edit':
            #first, get label of node.
            self.parent.updateCombo(self.comboEdit, session.domain.loadCases, 'last')
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.loadCases, 'last')
        # setup glcanvas on mouse event handler
        #self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        #self.glframe.mouseMoveCB = self.OnMouseMoveCB
        #self.glframe.canvas.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.glframe.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = None
        self.glframe.mouseMoveCB = None
        self.Hide()

    def OnAdd (self, event):
        #self.glframe.resetSolverAndPostprocessBox()
        label = self.labelText.GetValue()
        if not session.domain.addLoadCase(label=label, isUndoable=True ):
            # adding failed
            self.labelText.SetValue( "LC_"+giveNewLabel( session.domain.loadCases, 'newNum') )
            return
        self.labelText.SetValue("LC_"+giveNewLabel( session.domain.loadCases, 'newNum') )
        self.glframe.updateLoadCaseChoice()
        session.solver.isSolved = False
        session.domain.changeActiveLoadCaseTo(label)
        self.glframe.Refresh(False)
        self.SetFocus()
        #self.glframe.canvas.SetFocus()

    def editLabel(self, event=None):
        self.newlabelText.SetValue('')
        label = self.comboEdit.GetValue()
        lc = session.domain.loadCases.get(label)
        if lc:
            return
        elif not lc:
            logger.debug( langStr('Load case %s not found in the nodal loads %s', 'Zatěžovací stav %s nebylo nalezeno v zatíženích %s') % ( label, sorted(session.domain.loadCases.keys()) ) )
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.loadCases, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboEdit.GetValue()
        lc = label
        newLabel = self.newlabelText.GetValue()
        if newLabel:
            self.comboEdit.SetValue(newLabel)
        if session.domain.changeLoadCase(lc,label=newLabel if newLabel else label, isUndoable=True):
            # changing failed
            return
            label = newLabel
        self.newlabelText.SetValue('')
        self.parent.updateCombo(self.comboEdit, session.domain.loadCases, 'last')
        self.glframe.updateLoadCaseChoice()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()
        
    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def disable(self):
        self.Hide()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboDel.GetValue()
        if session.domain.delLoadCase(label,isUndoable=True):
            # deleting failed
            return
        self.parent.updateCombo(self.comboDel, session.domain.loadCases, 'last')
        self.glframe.updateLoadCaseChoice()
        self.glframe.Refresh(False)




class NodalLoadBox(wx.Panel):
    def __init__(self, parent, id, glframe,mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add Nodal load', 'Přidat uzlové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, '', labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit Nodal load', 'Editovat uzlové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete Nodal load', 'Smazat uzlové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.Bind(wx.EVT_TEXT_ENTER, self.editLabel)
            
        if mode == 'add' or mode == 'edit':
            #TextCtrl bindings are below
            wx.StaticText(self, -1, langStr('Node: ', 'Uzel: '), (10, 90))
            self.comboNode = wx.ComboBox(self, -1, pos=(80, 90), size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, 'Fx: ', (10, 120))
            self.fx = wx.TextCtrl(self, -1, '0',  (80, 120), (100, -1), style=wx.TE_PROCESS_ENTER)
            wx.StaticText(self, -1, 'Fz: ', (10, 150))
            self.fz = wx.TextCtrl(self, -1, '0',  (80, 150), (100, -1), style=wx.TE_PROCESS_ENTER)
            wx.StaticText(self, -1, 'My: ', (10, 180))
            self.my = wx.TextCtrl(self, -1, '0',  (80, 180), (100, -1), style=wx.TE_PROCESS_ENTER)
            if mode == 'edit':
                wx.StaticText(self, -1, langStr('New Load case: ', 'Nový zat. stav: '), (10, 240))
                self.comboLC = wx.ComboBox(self, -1, '',  (120, 240), (80, -1), style=wx.CB_READONLY)

        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            self.fx.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.fz.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.my.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnAdd)
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            self.fx.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.fz.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.my.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        # update
        #self.SetFocus()
        if self.mode=='add':#used also in mouse edit
            self.labelText.SetValue( "F_"+giveNewLabel( [lc.nodalLoads for lc in session.domain.loadCases.values()], 'newNum') )
            self.parent.updateCombo(self.comboNode, session.domain.nodes, 'last')
        elif self.mode=='edit':
            #first, get label of node.
            self.parent.updateCombo(self.comboNode, session.domain.nodes)
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.nodalLoads, 'last')
            self.parent.updateCombo(self.comboLC, session.domain.loadCases)
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.nodalLoads, 'last')
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
        self.glframe.setSelectionMode(NODE_MASK)
        #self.glframe.mouseMoveCB = self.OnMouseMoveCB
        #self.glframe.canvas.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.glframe.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = None
        self.glframe.mouseMoveCB = None
        self.Hide()

    def OnMouseLeftDownCB(self, mc):
        #get closest snap point
        if globalFlags.gridDisplayFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]-0.5)*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]-0.5)*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = (mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        self.glframe.mouseMoveCB = None
        if self.mode == 'add':
            node = self.glframe.findClosestNode(snapx,snapz)
            if node:
                self.comboNode.SetValue(node.label)
        elif self.mode == 'edit' or self.mode == 'del':
            load = self.glframe.findClosestNodalLoad(snapx,snapz)
            if load:
                if self.mode == 'edit':
                    self.comboEdit.SetValue(load.label)
                    self.editLabel()
                elif self.mode == 'del':
                    self.comboDel.SetValue(load.label)

    def OnMouseSelectionCB (self, selection):
        if (len(selection) == 1):
            if self.mode == 'add':
                self.comboNode.SetValue(selection[0].label)
            if self.mode == 'edit' or self.mode == 'del':
                self.comboEdit.SetValue(selection[0].label)
                #Could not be selectable-more nodal lodes in one load
                pass
        else:
            #multiple selection -> need to hide element label 
            pass
        self.SetFocus()
 
    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        fx = self.fx.GetValue()
        fz = self.fz.GetValue()
        my = self.my.GetValue()
        if selection: # nodes selected
            for item in selection:
                label = "F_"+giveNewLabel( [lc.nodalLoads for lc in session.domain.loadCases.values()], 'newNum')
                if not session.domain.addNodalLoad(label=label, where=item.label, value={'fx':fx,'fz':fz,'my':my}, isUndoable=True ):
                    # adding failed
                    self.labelText.SetValue( "F_"+giveNewLabel( [lc.nodalLoads for lc in session.domain.loadCases.values()], 'newNum') )
                    return
            self.glframe.resetSelection()
        else: # node number entered manually
            label=self.labelText.GetValue()
            node = self.comboNode.GetValue()
            if not session.domain.addNodalLoad(label=label, where=node, value={'fx':fx,'fz':fz,'my':my}, isUndoable=True ):
                # adding failed
                self.labelText.SetValue( "F_"+giveNewLabel( [lc.nodalLoads for lc in session.domain.loadCases.values()], 'newNum') )
                return
        #
        self.labelText.SetValue("F_"+giveNewLabel( [lc.nodalLoads for lc in session.domain.loadCases.values()], 'newNum') )
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()
    
    def onLoadCaseChange(self, event):
        if self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.nodalLoads, 'last')
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.nodalLoads, 'last')

    def editLabel(self, event=None):
        self.newlabelText.SetValue('')
        label = self.comboEdit.GetValue()
        load = session.domain.activeLoadCase.nodalLoads.get(label)
        if load:
            value = load.value
            if not self.mode == 'del':
                self.fx.SetValue('{0:.4g}'.format(value['fx']) )
                self.fz.SetValue('{0:.4g}'.format(value['fz']) )
                self.my.SetValue('{0:.4g}'.format(value['my']) )
                self.comboNode.SetValue(load.where.label)
                self.comboLC.SetValue(str(load.loadCase))
            self.glframe.resetSelection()
            self.glframe.selection.append (load.where)
            self.glframe.Refresh(False) # to display selection
            return
        elif not label:
            logger.debug( langStr('NodalLoad %s not found in the nodal loads %s', 'Uzlové zatížení %s nebylo nalezeno v zatíženích %s') % ( label, sorted(session.domain.activeLoadCase.nodalLoads.keys()) ) )
            self.fx.SetValue('')
            self.fz.SetValue('')
            self.my.SetValue('')
            self.comboNode.SetValue('')
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.nodalLoads, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if len(selection)>1: # nodes selected
            val = {
                'fx':float(self.fx.GetValue()),
                'fz':float(self.fz.GetValue()),
                'my':float(self.my.GetValue()),
            }
            loads = list(set(load for node in selection for load in session.domain.giveNodalLoadsOnNode(node,onlyActiveLC=True)))
            if session.domain.changeNodalLoads(loads,value=val,isUndoable=True):
                # failed
                return
            self.glframe.resetSelection()
        else: # manual load specification
            label = self.comboEdit.GetValue()
            load = label
            newLabel = self.newlabelText.GetValue()
            node = self.comboNode.GetValue()
            val = {
                'fx':float(self.fx.GetValue()),
                'fz':float(self.fz.GetValue()),
                'my':float(self.my.GetValue()),
            }
            lc = self.comboLC.GetValue()
            if newLabel:
                self.comboEdit.SetValue(newLabel)
            if session.domain.changeNodalLoad(load,label=newLabel if newLabel else label,where=node,value=val,loadCase=lc,isUndoable=True):
                # changing failed
                return
                label = newLabel
            self.newlabelText.SetValue('')
        #
        self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.nodalLoads, 'last')
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()
        
    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def disable(self):
        self.Hide()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if selection: #elements selected
            loads = list(set(load for node in selection for load in session.domain.giveNodalLoadsOnNode(node,onlyActiveLC=True)))
            if session.domain.delNodalLoads(loads, isUndoable=True):
                # deleting failed
                return
            self.glframe.resetSelection()
        else: #manual selection
            label = self.comboDel.GetValue()
            if session.domain.delNodalLoad(label,isUndoable=True):
                # deleting failed
                return
        self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.nodalLoads, 'last')
        self.glframe.Refresh(False)

    def SetNodeLabel (self, label):
        self.parent.updateCombo(self.comboNode, session.domain.nodes)
        self.comboNode.SetValue(str(label))




class PrescribedDsplBox(wx.Panel):
    def __init__(self, parent, id, glframe,mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add prescribed displacement', 'Přidat předepsané přemístění'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, '', labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit prescribed displacement', 'Editovat předepsané přemístění'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete prescribed displacement', 'Smazat předepsané přemístění'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.Bind(wx.EVT_TEXT_ENTER, self.editLabel)
            
        if mode == 'add' or mode == 'edit':
            #TextCtrl bindings are below
            wx.StaticText(self, -1, langStr('Node: ', 'Uzel: '), (10, 90))
            self.comboNode = wx.ComboBox(self, -1, pos=(80, 90), size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, 'ux: ', (10, 120))
            self.ux = wx.TextCtrl(self, -1, '0',  (80, 120), (100, -1), style=wx.TE_PROCESS_ENTER)
            wx.StaticText(self, -1, 'uz: ', (10, 150))
            self.uz = wx.TextCtrl(self, -1, '0',  (80, 150), (100, -1), style=wx.TE_PROCESS_ENTER)
            wx.StaticText(self, -1, 'phi_y: ', (10, 180))
            self.phiy = wx.TextCtrl(self, -1, '0',  (80, 180), (100, -1), style=wx.TE_PROCESS_ENTER)
            if mode == 'edit':
                wx.StaticText(self, -1, langStr('Load case: ', 'Zat. stav: '), (10, 240))
                self.comboLC = wx.ComboBox(self, -1, '0',  (80, 240), (100, -1), style=wx.CB_READONLY)
        #
        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            self.ux.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.uz.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            self.phiy.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnAdd)
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            self.ux.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.uz.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            self.phiy.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)
        #
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        #self.SetFocus()
        if self.mode=='add':#used also in mouse edit
            self.labelText.SetValue( "P_"+giveNewLabel( [lc.prescribedDspls for lc in session.domain.loadCases.values()], 'newNum') )
            self.parent.updateCombo(self.comboNode, session.domain.nodes, 'last')
        elif self.mode=='edit':
            #first, get label of node.
            self.parent.updateCombo(self.comboNode, session.domain.nodes)
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.prescribedDspls, 'last')
            self.parent.updateCombo(self.comboLC, session.domain.loadCases, directValue=session.domain.activeLoadCase.label)
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.prescribedDspls, 'last')
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        #self.glframe.mouseMoveCB = self.OnMouseMoveCB
        #self.glframe.canvas.Bind(wx.EVT_MOTION, self.OnMouseMove)
        #self.glframe.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = None
        self.glframe.mouseMoveCB = None
        self.Hide()

    def OnMouseLeftDownCB(self, mc):
        #get closest snap point
        if globalFlags.gridDisplayFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]-0.5)*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]-0.5)*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = (mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        self.glframe.mouseMoveCB = None
        if self.mode == 'add':
            node = self.glframe.findClosestNode(snapx,snapz)
            if node:
                self.comboNode.SetValue(node.label)
            self.SetFocus()
        elif self.mode == 'edit' or self.mode == 'del':
            pDspl = self.glframe.findClosestPrescribedDspl(snapx,snapz)
            if pDspl:
                if self.mode == 'edit':
                    self.comboEdit.SetValue(pDspl.label)
                    self.editLabel()
                elif self.mode == 'del':
                    self.comboDel.SetValue(pDspl.label)
        self.SetFocus()
 
    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label=self.labelText.GetValue()
        node = self.comboNode.GetValue()
        ux = self.ux.GetValue()
        uz = self.uz.GetValue()
        phiy = self.phiy.GetValue()
        if not session.domain.addPrescribedDspl(label=label, where=node, value={'x':ux,'z':uz,'Y':phiy}, isUndoable=True ):
            # adding failed
            self.labelText.SetValue( "P_"+giveNewLabel( [lc.prescribedDspls for lc in session.domain.loadCases.values()], 'newNum') )
            return
        self.labelText.SetValue("P_"+giveNewLabel( [lc.prescribedDspls for lc in session.domain.loadCases.values()], 'newNum') )
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def onLoadCaseChange(self, event):
        if self.mode=='edit':
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.prescribedDspls, 'last')
            self.editLabel()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.prescribedDspls, 'last')
    
    
    def editLabel(self, event=None):
        self.newlabelText.SetValue('')
        label = self.comboEdit.GetValue()
        pDspl = session.domain.activeLoadCase.prescribedDspls.get(label)
        if pDspl:
            value = pDspl.value
            self.ux.SetValue('{0:.4g}'.format(value['x']) )
            self.uz.SetValue('{0:.4g}'.format(value['z']) )
            self.phiy.SetValue('{0:.4g}'.format(value['Y']) )
            self.comboNode.SetValue(pDspl.where.label)
            self.comboLC.SetValue(str(pDspl.loadCase))
            return
        elif not label:
            logger.debug( langStr('Prescribed displacement %s not found in the pDspls %s', 'Předepsané přemístění %s nebylo nalezeno v přemístěních %s') % ( label, sorted(session.domain.activeLoadCase.prescribedDspls.keys()) ) )
            self.ux.SetValue('')
            self.uz.SetValue('')
            self.phiy.SetValue('')
            self.comboNode.SetValue('')
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.prescribedDspls, 'last')
            self.editLabel()

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboEdit.GetValue()
        pDspl = label
        newLabel = self.newlabelText.GetValue()
        node = self.comboNode.GetValue()
        val = {
            'x':float(self.ux.GetValue()),
            'z':float(self.uz.GetValue()),
            'Y':float(self.phiy.GetValue()),
        }
        lc = self.comboLC.GetValue()
        if newLabel:
            self.comboEdit.SetValue(newLabel)
        if session.domain.changePrescribedDspl(pDspl,label=newLabel if newLabel else label,where=node,value=val,loadCase=lc,isUndoable=True):
            # changing failed
            return
            label = newLabel
        self.newlabelText.SetValue('')
        self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.prescribedDspls, 'last')
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()
        
    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def disable(self):
        self.Hide()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboDel.GetValue()
        if session.domain.delPrescribedDspl(label,isUndoable=True):
            # deleting failed
            return
        self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.prescribedDspls, 'last')
        self.glframe.Refresh(False)

    def SetNodeLabel (self, label):
        self.parent.updateCombo(self.comboNode, session.domain.nodes)
        self.comboNode.SetValue(str(label))




class ElementLoadBox(wx.Panel):
    typeList = [langStr('Uniform', 'Spojité'), langStr('Force', 'Síla'), langStr('Temperature', 'Teplota')]
    dirList = ['X', 'Z', 'Local X', 'Local Z']
    
    def __init__(self, parent, id, glframe,mode):
        self.glframe = glframe
        self.parent = parent
        self.mode = mode
        self.subPanel = None
        
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        
        if mode=='add':
            wx.StaticBox(self, -1, langStr('Add element load', 'Přidat prvkové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.labelText = wx.TextCtrl(self, -1, '', labelEntPos, (100, -1),style=wx.TE_PROCESS_ENTER)
            self.labelText.Bind(wx.EVT_TEXT_ENTER, self.OnAdd)
        elif mode=='edit':
            wx.StaticBox(self, -1, langStr('Edit element load', 'Editovat prvkové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '), labelTextPos)
            self.comboEdit = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboEdit.Bind(wx.EVT_COMBOBOX, self.editLabel)
            wx.StaticText(self, -1, langStr('New label: ', 'Nové jméno: '), (10, 55))
            self.newlabelText = wx.TextCtrl(self, -1, '', pos=(100,55) , size=(100, -1), style=wx.TE_PROCESS_ENTER)
            self.newlabelText.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
        elif mode=='del':
            wx.StaticBox(self, -1, langStr('Delete element load', 'Smazat prvkové zatížení'), (0,0), mainBoxSize)
            wx.StaticText(self, -1, langStr('Enter label: ', 'Vlož jméno: '),labelTextPos)
            self.comboDel = wx.ComboBox(self, -1, pos=labelEntPos, size=(100, -1), style=wx.CB_READONLY)
            self.comboDel.Bind(wx.EVT_COMBOBOX, self.deleteLoad)
            self.newlabelText = None
        
        if mode == 'add' or mode == 'edit':
            wx.StaticText(self, -1, langStr('Element:', 'Prvek:'), (10, 95))
            self.comboElem = wx.ComboBox(self, -1, pos=(100, 95), size=(100, -1), style=wx.CB_READONLY)
            wx.StaticText(self, -1, langStr('Type:', 'Typ:'), (10, 125))
            self.loadType = wx.ComboBox(self, choices=self.typeList, value=self.typeList[0], pos=(100, 125), size=(100, -1), style=wx.CB_READONLY)
            self.subPanelG(None)
            self.loadType.Bind(wx.EVT_COMBOBOX, self.subPanelG)
            self.comboElem.Bind(wx.EVT_COMBOBOX, self.comboElement)
            if mode == 'edit':
                StaticTextWithHelp(self, -1, langStr('New Load case: ', 'Nový zat. stav: '), (10, 375) )
                self.comboLC = wx.ComboBox(self, -1, '', (120, 375), (80, -1), style=wx.CB_READONLY)
        
        if mode=='add':
            btn = wx.Button(self, 1, langStr('&Add', 'Přidat (&a)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnAdd)
        elif mode=='edit':
            btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
            #self.fx.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            #self.fz.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            #self.dTc.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            #self.dTg.Bind(wx.EVT_TEXT_ENTER, self.OnChange)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnChange)
        elif mode=='del':
            btn = wx.Button(self, 1, langStr('&Delete', 'Smazat (&d)'), btPos1, btSize1)
            btn.SetFocus()
            wx.EVT_BUTTON(self, 1, self.OnDel)

        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        

    def subPanelG(self,event):#initialize layout according to loadType. First, clean up everything.
        if self.subPanel:
            self.subPanel.Destroy()
        
        self.subPanel = wx.Panel(self,pos=(10,200), size=(panelSize[0]-20,110), style=wx.SUNKEN_BORDER)
        
        if self.loadType.GetValue() == self.typeList[0]:#Uniform
            StaticTextWithHelp(self.subPanel, -1, langStr('Direction:', 'Směr:'), pos=(0, 10), size=(-1,-1))
            self.loadDir = wx.ComboBox(self.subPanel, choices=self.dirList, value=self.dirList[1], pos=(90, 10), size=(100, -1), style=wx.CB_READONLY)
            StaticTextWithHelp(self.subPanel, -1, langStr('Magnitude:', 'Velikost:'), (0, 40), (-1,-1), help=langStr('Uniform distributed load per element unit length','Rovnoměrné zatížení na jednotkovou délku prvku'))
            self.loadMagnitude = wx.TextCtrl(self.subPanel, -1, '0',  (90, 40), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self.subPanel, -1, langStr('Projection on glob. X:', 'Projekce na glob. X:'), (0, 70), (-1,-1))
            self.loadPerX = CheckBoxWithHelp(self.subPanel,wx.NewId(), label='', pos=(160,70), help=langStr('Projection per global coordinate X (e.g. snow load)','Projekce na globální X (např. sníh)'))
        elif self.loadType.GetValue() == self.typeList[1]: #Force
            StaticTextWithHelp(self.subPanel, -1, 'Fx glob:', (0, 10), (-1,-1))
            self.Fx = wx.TextCtrl(self.subPanel, -1, '0',  (90, 10), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self.subPanel, -1, 'Fz glob:', (0, 40), (-1,-1))
            self.Fz = wx.TextCtrl(self.subPanel, -1, '0',  (90, 40), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self.subPanel, -1, langStr('Dist. left:', 'Vzd. zleva:'), (0, 70), (-1,-1))
            self.DistF = wx.TextCtrl(self.subPanel, -1, '0',  (90, 70), (100, -1), style=wx.TE_PROCESS_ENTER)
        elif self.loadType.GetValue() == self.typeList[2]: #Temperature
            StaticTextWithHelp(self.subPanel, -1, langStr('T in centr.: ', 'T v těž.:' ), (0, 10), (-1,-1), help=langStr('Uniform temperature in cross section\'s centroid','Teplota v těžišti průřezu'))
            self.dTc = wx.TextCtrl(self.subPanel, -1, '0',  (90, 10), (100, -1), style=wx.TE_PROCESS_ENTER)
            StaticTextWithHelp(self.subPanel, -1, langStr('T_b - T_t: ', 'T_d - T_h'), (0, 40), (-1,-1), help=langStr('Temperature difference (T_bottom - T_top)','Teplotní rozdíl (T_spodní - T_horní)'))
            self.dTg = wx.TextCtrl(self.subPanel, -1, '0',  (90, 40), (100, -1), style=wx.TE_PROCESS_ENTER)
        elif self.loadType.GetValue() == '':#Invisible
            None
    
    def preview(self,event=None):
        if self.comboElem.GetValue() == '':
            return
        element = session.domain.giveElement(self.comboElem.GetValue() )
        if element:
            n1,n2 = element.nodes[0], element.nodes[1]
            self.glframe.setPreview('element',nodes=[n1,n2])
    
    def enable(self, show=True):
        #self.SetFocus()
        if self.mode=='add':#used also in mouse edit
            self.labelText.SetValue(  "L_"+giveNewLabel( [lc.elementLoads for lc in session.domain.loadCases.values()], 'newNum') )
            self.parent.updateCombo(self.comboElem, session.domain.elements, 'last')
            self.comboElement()
            self.preview()
            #self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            #self.glframe.setSelectionMode(ELEMENT_MASK, False)
            #self.Show(show)
        elif self.mode=='edit':
            self.parent.updateCombo(self.comboElem, session.domain.elements)
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.elementLoads, 'last')
            self.parent.updateCombo(self.comboLC, session.domain.loadCases)
            self.editLabel()
            self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
            self.glframe.setSelectionMode(ELEMENT_MASK, False)
            self.preview()
        elif self.mode=='del':
            self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.elementLoads, 'last')
            self.glframe.resetSelection()
            load = session.domain.activeLoadCase.elementLoads.get(self.comboDel.GetValue())
            elem = session.domain.giveElement(load.where)
            self.glframe.addToSelection(elem)
            self.glframe.Refresh(False)
        # setup glcanvas on mouse event handler
        self.glframe.mouseLeftCB = self.OnMouseLeftDownCB
        self.glframe.mouseSelectionCB = self.OnMouseSelectionCB
        self.glframe.setSelectionMode(ELEMENT_MASK)
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.glframe.mouseLeftCB = None
        self.glframe.mouseMoveCB = None
        self.glframe.mouseSelectionCB = None
        self.glframe.resetSelection()
        self.glframe.Refresh(False)
        self.glframe.resetPreview()
        self.Hide()

    def OnMouseLeftDownCB(self, mc):
        #get closest snap point
        if globalFlags.gridDisplayFlag:
            snapx = math.ceil((mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]-0.5)*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = math.ceil((mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]-0.5)*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        else:
            snapx = (mc[0]-globalGridSettings.gridOrigin[0])/globalGridSettings.gridDelta[0]*globalGridSettings.gridDelta[0]+globalGridSettings.gridOrigin[0]
            snapz = (mc[2]-globalGridSettings.gridOrigin[1])/globalGridSettings.gridDelta[1]*globalGridSettings.gridDelta[1]+globalGridSettings.gridOrigin[1]
        self.glframe.mouseMoveCB = None
        if self.mode == 'add':
            elem = self.glframe.findClosestElement(snapx,snapz)
            if elem:
                self.comboElem.SetValue(elem.label)
            self.SetFocus()
        elif self.mode == 'edit' or self.mode == 'del':
            load = self.glframe.findClosestElementLoad(snapx,snapz)
            if load:
                if self.mode == 'edit':
                    self.comboEdit.SetValue(load.label)
                    self.editLabel()
                elif self.mode == 'del':
                    self.comboDel.SetValue(load.label)
        self.SetFocus()

    def OnMouseSelectionCB (self, selection):
        if self.mode == 'add':
            #pick up the last added element and remove the others
            self.comboElem.SetValue(selection[-1].label)
            self.glframe.resetSelection()
            self.glframe.addToSelection(selection[-1])
            self.glframe.Refresh(False)
            self.preview()
        else:
            #multiple selection -> need to hide element label 
            pass
        self.SetFocus()
    
    def comboElement(self, event=None):
        self.glframe.resetSelection()
        label=self.comboElem.GetValue()
        elem = session.domain.elements.get(label)
        if self.mode == 'add':
            self.glframe.addToSelection(elem)
            self.glframe.Refresh(False)
            self.preview()
    
    def deleteLoad(self, event=None):
        self.glframe.resetSelection()
        load = session.domain.activeLoadCase.elementLoads.get(self.comboDel.GetValue())
        elem = session.domain.giveElement(load.where)
        self.glframe.addToSelection(elem)
        self.glframe.Refresh(False)
        
    
    def OnAdd (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        loadType = self.loadType.GetValue()
        loadDir = None
        loadMagnitude = 0
        loadPerX = False
        Fx = 0
        Fz = 0
        DistF = 0
        dTc = 0
        dTg = 0
        if self.loadType.GetValue() == self.typeList[0]:#Uniform
            typeVal = 'Uniform'
            loadDir = self.loadDir.GetValue()
            loadMagnitude = float(self.loadMagnitude.GetValue())
            loadPerX = self.loadPerX.GetValue()
        elif self.loadType.GetValue() == self.typeList[1]:#Force
            typeVal = 'Force'
            Fx = float(self.Fx.GetValue())
            Fz = float(self.Fz.GetValue())
            DistF = float(self.DistF.GetValue())
        elif self.loadType.GetValue() == self.typeList[2]:#Temperature
            typeVal = 'Temperature'
            dTc = float(self.dTc.GetValue())
            dTg = float(self.dTg.GetValue())
        else:
            print ("Unknown load type")
        
        if not selection: # element selected manually
            selection = [session.domain.giveElement(self.comboElem.GetValue())]
        
        for item in selection:
            if (DistF<0) or (DistF>item.computeGeom()[0]):
                print (langStr('Distance %g is outside of element %s', 'Vzdálenost %g je mimo prvek %s') % (DistF, item.label))
                return
        for item in selection:
            if self.mode=='edit':
                if self.newlabelText.GetValue():
                    label = self.newlabelText.GetValue()
                else:
                    label = self.comboEdit.GetValue()
                loadCase = self.comboLC.GetValue()
            else:
                label = self.labelText.GetValue()
                loadCase = session.domain.activeLoadCase
            
            if keyExists([lc.elementLoads for lc in session.domain.loadCases.values()], label):
                label = "L_" + giveNewLabel( [lc.elementLoads for lc in session.domain.loadCases.values()], 'newNum')
            
            if not session.domain.addElementLoad(label=label, where=item.label, loadCase=loadCase, value={'type': typeVal, 'dir':loadDir,  'magnitude':loadMagnitude,'perX':loadPerX, 'Fx':Fx, 'Fz':Fz, 'DistF':DistF, 'dTc':dTc, 'dTg':dTg}, isUndoable=True ):
                if self.mode=='add':# adding failed
                    self.labelText.SetValue(  "L_"+giveNewLabel( [lc.elementLoads for lc in session.domain.loadCases.values()], 'newNum') )
                return
        
        self.glframe.resetSelection()
        if self.mode=='add':
            self.labelText.SetValue( "L_"+giveNewLabel( [lc.elementLoads for lc in session.domain.loadCases.values()], 'newNum') )
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def onLoadCaseChange(self, event):
        try:
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.elementLoads, 'last')
            if self.mode == 'edit':
                self.editLabel()
            elif self.mode == 'del':
                self.glframe.resetSelection()
        except:
            pass

    def editLabel(self, event=None):
        if self.newlabelText:
            self.newlabelText.SetValue('')
        label = self.comboEdit.GetValue()
        #First check if the label is in activeLoadCase
        if not keyExists(session.domain.activeLoadCase.elementLoads, label):
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.elementLoads, 'last')
        load = session.domain.activeLoadCase.elementLoads.get(label)
        if load:
            self.comboElem.SetValue(str(load.where))
            self.loadType.SetValue(str(load.value['type']))
            self.subPanelG(None)
            if self.loadType.GetValue() == self.typeList[0]:#Uniform
                self.loadDir.SetValue(str(load.value['dir']))
                self.loadMagnitude.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['magnitude'])) )
                self.loadPerX.SetValue(load.value['perX'])
            elif self.loadType.GetValue() == self.typeList[1]:#Single force
                self.Fx.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['Fx'])) )
                self.Fz.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['Fz'])) )
                self.DistF.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['DistF'])) )
            elif self.loadType.GetValue() == self.typeList[2]:#Temperature
                self.dTc.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['dTc'])) )
                self.dTg.SetValue(str('' if label=='' else '{0:.4g}'.format(load.value['dTg'])) )
            self.comboLC.SetValue(str(load.loadCase))
            self.glframe.resetSelection()
            self.glframe.selection.append (load.where)
            self.glframe.Refresh(False) # to display selection
            return
        else:
            self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.elementLoads, 'last')
            self.comboElem.SetValue('')
            self.loadType.SetValue('')
            self.subPanelG(None)

    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        label = self.comboEdit.GetValue()
        session.domain.delElementLoad(label, isUndoable=True)
        self.glframe.resetSelection()
        selection = [session.domain.giveElement(self.comboElem.GetValue())]
        self.OnAdd(None)
        self.newlabelText.SetValue('')
        self.parent.updateCombo(self.comboEdit, session.domain.activeLoadCase.elementLoads, 'last')
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnClose (self, event):
        self.glframe.resetSelection()
        self.disable()
        self.glframe.canvas.SetFocus()

    def disable(self):
        self.glframe.resetPreview()
        self.Hide()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        if selection: #elements selected
            loads = list(set(load for elem in selection for load in session.domain.giveElementLoadsOnElement(elem,onlyActiveLC=True)))
            if session.domain.delElementLoads(loads, isUndoable=True):
                # deleting failed
                return
            self.glframe.resetSelection()
        else: #manual selection
            label = self.comboEdit.GetValue()
            if session.domain.delElementLoad(label, isUndoable=True):
                # deleting failed
                return
        self.parent.updateCombo(self.comboDel, session.domain.activeLoadCase.elementLoads, 'last', 0)
        self.glframe.Refresh(False)

    def SetElementLabel (self, label):
        self.parent.updateCombo(self.comboElem, session.domain.elements)
        self.comboElem.SetValue(str(label))


class TransformMeshBox(wx.Panel):
    """Panel for mesh translation"""
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.spreadSheet = None
        self.parent = parent
        # 
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, -1, langStr('Translate mesh', 'Přesunout síť'), (0,0), mainBoxSize)
        xx1,xx2,xx3,zz,dz = 5,10,100,20,20
        # type of translation (move/copy)
        self.moveRb = wx.RadioButton(self, -1, langStr('Move elements', 'Přesunout prvky'), (xx2, zz+1*dz), style=wx.RB_GROUP)
        self.copyRb = wx.RadioButton(self, -1, langStr('Copy elements', 'Kopírovat prvky'), (xx2, zz+2*dz))
        self.moveRb.Bind(wx.EVT_RADIOBUTTON, self.SetModeVal)
        self.copyRb.Bind(wx.EVT_RADIOBUTTON, self.SetModeVal)
        # show when only copy selected
        self.nCopiesLabel = wx.StaticText(self, -1, langStr('No. of copies', 'Počet kopií '), (xx2, zz+4*dz))
        #self.nCopiesEntry = self.dx = wx.TextCtrl(self, -1, '1',  (xx3+10, zz+3*dz), (30, -1))
        self.nCopiesEntry = wx.SpinCtrl(self, value='0', pos=(xx3+10, zz+4*dz), size=(50, -1))
        self.nCopiesEntry.SetRange(0, 100)

        # set to disabled; move is default
        self.nCopiesLabel.Enable(False)
        self.nCopiesEntry.Enable(False)

        # copy/move direction
        zz += 110
        dz = 30
        wx.StaticText(self, -1, langStr('Set direction', 'Směr přesunu '), (xx2+5, zz+1*dz-10))
        wx.StaticText(self, -1, 'dX', (xx2+5, zz+2*dz-10))
        self.dx = wx.TextCtrl(self, -1, '0.0',  (xx3, zz+2*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER)
        wx.StaticText(self, -1, 'dZ', (xx2+5, zz+3*dz-10))
        self.dz = wx.TextCtrl(self, -1, '0.0',  (xx3, zz+3*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER)

        # bottom buttons
        btn = wx.Button(self, 1, langStr('Apply', 'Proveď'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 1, self.OnApply)
        btn.SetFocus()
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        #
        #self.defScaleSlider = wx.Slider(self, -1, 50, 0, 100, (20, 140), (110, -1))

    def SetModeVal (self, e):
        
        copyFlag = self.copyRb.GetValue()
        if (copyFlag):
            self.nCopiesLabel.Enable(True)
            self.nCopiesEntry.Enable(True)
        else:
            self.nCopiesLabel.Enable(False)
            self.nCopiesEntry.Enable(False)

    def OnApply(self, event):
        selection = self.glframe.selection
        self.glframe.resetSelection()
        copyMode = self.copyRb.GetValue()
        moveMode = self.moveRb.GetValue()
        dx = float(self.dx.GetValue())
        dy = 0.0
        dz = float(self.dz.GetValue())
        nc = int (self.nCopiesEntry.GetValue())
        if copyMode:
            session.domain.copyElements(selection,dx,dy,dz,nc,isUndoable=True)           
        elif moveMode:  #move mode -> just update nodal positions
            session.domain.moveNodes(selection,dx,dy,dz,isUndoable=True)
        else:
            raise EduBeamError

        #force redraw and set focus
        self.glframe.Refresh(False)        
        self.glframe.canvas.SetFocus()

    def enable(self, show=True):
        # update label (necessary if a new file opened)
        self.Show(show)
        self.parent.currentBox = self
        self.glframe.setSelectionMode(NODE_MASK|ELEMENT_MASK)

    def disable(self):
        self.Hide()
        self.glframe.resetSelection()
        self.glframe.setViewMode()
        
    def OnClose (self, event):
        self.disable()   
        self.glframe.canvas.SetFocus()


class ModifyNodesBox(wx.Panel):
    helpBcX    = langStr('Boundary condition in x direction','Okrajová podmínka ve směru x')
    helpBcZ    = langStr('Boundary condition in z direction','Okrajová podmínka ve směru z')
    helpBcRotY = langStr('Boundary condition in rotation','Okrajová podmínka rotační')
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent = parent
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, wx.NewId(), langStr('Change nodal attributes', 'Modifikuj uzly'), (0,0), mainBoxSize)

        wx.StaticBox(self, wx.NewId(), langStr('Boundary conditions', 'Okrajové podmínky'), (5,20), (200, 120))
        xx = 60
        ww = 130
        zz = 40
        self.bcu = CheckBoxWithHelp(self,wx.NewId(),'u', (10,zz), help=self.helpBcX)
        zz += 20
        self.bcw = CheckBoxWithHelp(self,wx.NewId(),'w', (10,zz), help=self.helpBcZ)
        zz += 20
        self.bcr = CheckBoxWithHelp(self,wx.NewId(),'r', (10,zz), help=self.helpBcRotY)
        
        btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), (10, minHeight-80), btSize1)
        wx.EVT_BUTTON(self, 1, self.OnChange)
        btn.SetFocus()

        btn = wx.Button(self, 2, langStr('&Delete', 'Smazat (&d)'), (110, minHeight-80), btSize1)
        btn.SetFocus()
        wx.EVT_BUTTON(self, 2, self.OnDel)

        wx.Button(self, 3, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 3, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        # update
        self.Show(show)
        self.parent.currentBox = self
        self.glframe.setSelectionMode(NODE_MASK)

    def disable(self):
        # setup glcanvas on mouse event handler
        self.Hide()
        self.glframe.resetSelection()
        
    def OnChange (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        bcs = {
            'x':self.bcu.GetValue(),
            'z':self.bcw.GetValue(),
            'Y':self.bcr.GetValue()
        }

        session.domain.changeNodes(selection,bcs,isUndoable=True)
        self.glframe.resetSelection()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnDel (self, event):
        self.glframe.resetSolverAndPostprocessBox()
        selection = self.glframe.selection
        session.domain.delNodes(selection,isUndoable=True)
        self.glframe.resetSelection()
        self.glframe.Refresh(False)

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()






class LinearStaticPostProcessBox(wx.Panel):
    """Panel for postprocess control"""
    dictDataTypeSheetTitle = {
        'linStatResults'    : langStr('Results','Výsledky'),
        'linStatGlobMatrix' : langStr('Global matrices','Globální matice'),
        'linStatElemMatrix' : langStr('Element matrices','Matice prvku'),
    }
    dictDataTypeComboLabel = {
        'linStatResults'    : langStr('Results','Výsledky'),
        'linStatGlobMatrix' : langStr('Global matrices','Globální matice'),
        'linStatElemMatrix' : langStr('Element matrices','Matice prvku'),
    }
    dictComboLabelDataType = dict( (i[1],i[0]) for i in dictDataTypeComboLabel.items() )
    choices = (
        dictDataTypeComboLabel['linStatResults'],
        dictDataTypeComboLabel['linStatGlobMatrix'],
        dictDataTypeComboLabel['linStatElemMatrix'],
    )

    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.spreadSheet = None
        self.parent = parent
        # 
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, -1, langStr('Postprocessor', 'Postprocesor'), (0,0), mainBoxSize)
        xx1,xx2,xx3,zz,dz = 5,10,100,20,20
        # what to draw
        self.defGeoCB = wx.CheckBox(self, -1, langStr('Deformed geometry', 'Deformovaný tvar'), (xx2, zz))
        wx.EVT_CHECKBOX(self, self.defGeoCB.GetId(), self.defGeo)
        self.NCB = wx.CheckBox(self, -1, langStr('Normal force', 'Normálová síla'), (xx2, zz+1*dz))
        wx.EVT_CHECKBOX(self, self.NCB.GetId(), self.NDraw)
        self.VCB = wx.CheckBox(self, -1, langStr('Shear Force', 'Posouvající síla'), (xx2, zz+2*dz))
        wx.EVT_CHECKBOX(self, self.VCB.GetId(), self.VDraw)
        self.MCB = wx.CheckBox(self, -1, langStr('Moment', 'Moment'), (xx2, zz+3*dz))
        wx.EVT_CHECKBOX(self, self.MCB.GetId(), self.MDraw)
        self.RCB = wx.CheckBox(self, -1, langStr('Reactions', 'Reakce'), (xx2, zz+4*dz))
        wx.EVT_CHECKBOX(self, self.RCB.GetId(), self.RDraw)
        # scales
        zz += 110
        dz = 30
        wx.StaticBox(self, -1, langStr('Scales', 'Měřítka'), (xx1,zz), (200, 115))
        wx.StaticText(self, -1, langStr('DefGeom: ', 'Def. tvar: '), (xx2+5, zz+1*dz-10))
        self.defGeom = wx.TextCtrl(self, -1, '1.0',  (xx3, zz+1*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER | wx.BORDER_DOUBLE)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('IntForces: ', 'Vnitřní síly: '), (xx2+5, zz+2*dz-10))
        self.intForces = wx.TextCtrl(self, -1, '1.0',  (xx3, zz+2*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        autoscale_btn = wx.Button(self, 3, langStr('&AutoScale', 'Aut. měř. (&a)'), (xx3,zz+3*dz-10), btSize1)
        wx.EVT_BUTTON(self, 3, self.OnAutoScale)
        # table
        zz += 120
        wx.StaticBox(self, -1, langStr('Table', 'Tabulka'), (xx1,zz), (200, 115))
        self.comboDataType = wx.ComboBox(self, -1, pos=(xx2, zz+1*dz-10), size=(180,-1), style=wx.CB_READONLY, choices=self.choices, value=self.choices[0] )
        self.comboDataType.Bind(wx.EVT_COMBOBOX, self.OnChangeCombo1)
        self.combo2 = wx.ComboBox(self, -1, pos=(xx2,zz+2*dz-10), size=(180,-1), style=wx.CB_READONLY)
        self.combo2.Hide()
        self.ResultsSpreadsheet = wx.Button(self, -1, langStr('Results to spreadsheet', 'Výsledky do tabulky'), (xx2, zz+3*dz-10))
        wx.EVT_BUTTON(self, self.ResultsSpreadsheet.GetId(), self.ResultsToSpreadsheet)

        # bottom buttons
        btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 1, self.OnSetScale)
        btn.SetFocus()
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        #
        #self.defScaleSlider = wx.Slider(self, -1, 50, 0, 100, (20, 140), (110, -1))

    def OnAutoScale(self, event):
        self.glframe.autoScale(event)
        self.enable(True)
        self.glframe.canvas.SetFocus()

    def enable(self, show=True):
        # update label (necessary if a new file opened)
        self.defGeom.SetValue(str('{0:.3g}'.format(float(globalSizesScales.deformationScale))))
        self.intForces.SetValue(str('{0:.3g}'.format(float(globalSizesScales.intForceScale))))
        self.Show(show)
        self.parent.currentBox = self
        self.OnChangeCombo1()

    def reset(self):
        self.defGeoCB.SetValue(False)
        self.NCB.SetValue(False)
        self.VCB.SetValue(False)
        self.MCB.SetValue(False)
        self.RCB.SetValue(False)
        self.glframe.Refresh(False)
        globalFlags.deformationDisplayFlag = False
        globalFlags.intForcesDisplayFlag = [False,False,False,False]

    def disable(self):
        self.Hide()

    def defGeo(self, event):
        globalFlags.deformationDisplayFlag = self.defGeoCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def NDraw(self, event):
        globalFlags.intForcesDisplayFlag[0] = self.NCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def VDraw(self, event):
        globalFlags.intForcesDisplayFlag[1] = self.VCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def MDraw(self, event):
        globalFlags.intForcesDisplayFlag[2] = self.MCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def RDraw(self, event):
        globalFlags.intForcesDisplayFlag[3] = self.RCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def ResultsToSpreadsheet(self, event):
        if not session.solver.isSolved:
            logger.warning( langStr('Problem has not been solved yet ...', 'Úloha ještě není vypočtena ...') )
            return
        if self.spreadSheet:
            self.ResultsToSpreadsheetClose(None)
        self.spreadSheet = Notebook(self)
        dataType = self.giveSpreadsheetDataType()
        self.spreadSheet.SetTitle(self.dictDataTypeSheetTitle[dataType])
        kw = {}
        if dataType == 'linStatElemMatrix':
            kw['elem'] = self.combo2.GetValue()
        self.spreadSheet.importData(dataType,**kw)
        self.spreadSheet.Bind(wx.EVT_CLOSE, self.ResultsToSpreadsheetClose)
        self.spreadSheet.Show(True)
        self.spreadSheet.Centre()

    def ResultsToSpreadsheetClose(self, event=None):
        self.spreadSheet.Destroy()
        self.glframe.canvas.SetFocus()

    def giveSpreadsheetDataType(self):
        cVal = self.comboDataType.GetValue()
        dVal = self.dictComboLabelDataType[cVal]
        return dVal

    def OnChangeCombo1(self, event=None):
        val = self.giveSpreadsheetDataType()
        if   val == 'linStatResults':
            self.combo2.Hide()
        elif val == 'linStatGlobMatrix':
            self.combo2.Hide()
        elif val == 'linStatElemMatrix':
            self.combo2.Show()
            self.parent.updateCombo(self.combo2, session.domain.elements, 'first')
        else:
            logger.error( 'PostProcessBox.OnChangeCombo1: wrong dict values' )

    class MyPopupMenu(wx.Menu):  
        def __init__(self, parent):  
            wx.Menu.__init__(self)  
            #
            self.parent = parent  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Fit all', 'Přizpůsobit oknu'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.fitAll, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom in', 'Zvětši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.zoomIn, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom out', 'Zmenši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.zoomOut, item)  
            #
            def fitAll(self, event):  
                self.parent.fitAll()  
            #
            def OnClose(self, event):  
                self.parent.Close()  

    def OnSetScale (self, event):
        globalSizesScales.deformationScale = float(self.defGeom.GetValue())
        globalSizesScales.intForceScale = float(self.intForces.GetValue())
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnClose (self, event):
        self.disable()   
        self.glframe.canvas.SetFocus()

class LinearStabilityPostProcessBox(wx.Panel):
    """Panel for postprocess control"""

    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.spreadSheet = None
        self.parent = parent
        # 
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, -1, langStr('Postprocessor', 'Postprocesor'), (0,0), mainBoxSize)
        xx1,xx2,xx3,zz,dz = 5,10,100,20,20
        # active eigen mode
        self.activeEigvalLabel = wx.StaticText(self, -1, langStr('Active mode:', 'Aktivní tvar:'), (xx2, zz))
        self.activeEigValSpin =  wx.SpinCtrl(self, value='0', pos=(xx2+100, zz), size=(50, -1))
        self.activeEigValSpin.SetRange(0, 1)
        self.Bind( wx.EVT_SPINCTRL, self.OnActiveEigValSpin )
        self.activeEigvalValue = wx.StaticText(self, -1, '', (xx2, zz+2*dz))
        #
        self.defGeoCB = wx.CheckBox(self, -1, langStr('Eigen mode', 'Vlastní tvar'), (xx2, zz+4*dz))
        wx.EVT_CHECKBOX(self, self.defGeoCB.GetId(), self.defGeo)
        self.NCB = wx.CheckBox(self, -1, langStr('Normal force', 'Normálová síla'), (xx2, zz+5*dz))
        wx.EVT_CHECKBOX(self, self.NCB.GetId(), self.NDraw)
        self.VCB = wx.CheckBox(self, -1, langStr('Shear Force', 'Posouvající síla'), (xx2, zz+6*dz))
        wx.EVT_CHECKBOX(self, self.VCB.GetId(), self.VDraw)
        self.MCB = wx.CheckBox(self, -1, langStr('Moment', 'Moment'), (xx2, zz+7*dz))
        wx.EVT_CHECKBOX(self, self.MCB.GetId(), self.MDraw)
        self.RCB = wx.CheckBox(self, -1, langStr('Reactions', 'Reakce'), (xx2, zz+8*dz))
        wx.EVT_CHECKBOX(self, self.RCB.GetId(), self.RDraw)
        # scales
        zz += 200
        dz = 30
        wx.StaticBox(self, -1, langStr('Scales', 'Měřítka'), (xx1,zz), (200, 115))
        wx.StaticText(self, -1, langStr('EigMode: ', 'Vl. tvary: '), (xx2+5, zz+1*dz-10))
        self.defGeom = wx.TextCtrl(self, -1, '1.0',  (xx3, zz+1*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER | wx.BORDER_DOUBLE)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('IntForces: ', 'Vnitřní síly: '), (xx2+5, zz+2*dz-10))
        self.intForces = wx.TextCtrl(self, -1, '1.0',  (xx3, zz+2*dz-10), (90, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        autoscale_btn = wx.Button(self, 3, langStr('&AutoScale', 'Aut. měř. (&a)'), (xx3,zz+3*dz-10), btSize1)
        wx.EVT_BUTTON(self, 3, self.OnAutoScale)

        # bottom buttons
        btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 1, self.OnSetScale)
        btn.SetFocus()
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        #
        #self.defScaleSlider = wx.Slider(self, -1, 50, 0, 100, (20, 140), (110, -1))

    def OnActiveEigValSpin( self, event ):
        eigVal = self.activeEigValSpin.GetValue()
        nEigVals = len(session.solver.eigval)
        if eigVal >= nEigVals:
            self.activeEigValSpin.SetValue(nEigVals-1)
            return
        session.solver.activeEigVal = self.activeEigValSpin.GetValue()
        if session.solver.isSolved:
            self.activeEigvalValue.SetLabel(langStr("Eigen value","Vl. hodnota") + ": %e"%session.solver.giveActiveEigenValue().real)
        self.glframe.Refresh(False)

    def OnAutoScale(self, event):
        self.glframe.autoScale(event)
        self.enable(True)
        self.glframe.canvas.SetFocus()

    def enable(self, show=True):
        # update label (necessary if a new file opened)
        self.defGeom.SetValue(str('{0:.3g}'.format(float(globalSizesScales.deformationScale))))
        self.intForces.SetValue(str('{0:.3g}'.format(float(globalSizesScales.intForceScale))))
        if session.solver.isSolved:
            self.activeEigValSpin.SetRange(0, min (10, len(session.solver.giveActiveSolutionVector())/3))
            self.activeEigvalValue.SetLabel(langStr("Eigen value","Vl. hodnota") + ": %e"%session.solver.giveActiveEigenValue().real)

        self.Show(show)
        self.parent.currentBox = self

    def reset(self):
        self.defGeoCB.SetValue(False)
        self.NCB.SetValue(False)
        self.VCB.SetValue(False)
        self.MCB.SetValue(False)
        self.RCB.SetValue(False)
        self.glframe.Refresh(False)
        globalFlags.deformationDisplayFlag = False
        globalFlags.intForcesDisplayFlag = [False,False,False,False]

    def disable(self):
        self.Hide()

    def defGeo(self, event):
        globalFlags.deformationDisplayFlag = self.defGeoCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def NDraw(self, event):
        globalFlags.intForcesDisplayFlag[0] = self.NCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def VDraw(self, event):
        globalFlags.intForcesDisplayFlag[1] = self.VCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def MDraw(self, event):
        globalFlags.intForcesDisplayFlag[2] = self.MCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def RDraw(self, event):
        globalFlags.intForcesDisplayFlag[3] = self.RCB.GetValue()
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    class MyPopupMenu(wx.Menu):  
        def __init__(self, parent):  
            wx.Menu.__init__(self)  
            #
            self.parent = parent  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Fit all', 'Přizpůsobit oknu'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.fitAll, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom in', 'Zvětši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.zoomIn, item)  
            #
            item = wx.MenuItem(self, wx.NewId(), langStr('Zoom out', 'Zmenši'))  
            self.AppendItem(item)  
            self.Bind(wx.EVT_MENU, self.zoomOut, item)  
            #
            def fitAll(self, event):  
                self.parent.fitAll()  
            #
            def OnClose(self, event):  
                self.parent.Close()  

    def OnSetScale (self, event):
        globalSizesScales.deformationScale = float(self.defGeom.GetValue())
        globalSizesScales.intForceScale = float(self.intForces.GetValue())
        self.glframe.Refresh(False)
        self.glframe.canvas.SetFocus()

    def OnClose (self, event):
        self.disable()   
        self.glframe.canvas.SetFocus()


class SelectSolverBox(wx.Panel):
    """Panel for postprocess control"""
    
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent = parent
        #
        problemTypes = [langStr('Linear static', 'Lineární statika'),
                        langStr('Linear stability', 'Lineární stabilita')]
                        

        # 
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, -1, langStr('Select solver', 'Typ problému'), (0,0), mainBoxSize)
        xx1,xx2,xx3,zz,dz = 5,10,100,20,20
        # set problem types
        self.problemCTRL = self.comboProblemType = wx.ComboBox(self, -1, pos=(10, 30), size=(160, -1), choices=problemTypes, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        self.comboProblemType.SetSelection(0) 
        # problem-specific options
        ##self.stabilityOptions = []
        ##solverBox = wx.StaticBox(self, -1, langStr('Stability solver options', 'Nastavení lin. stability'), (5,100), (200, 90))
        ##lcsText = wx.StaticText(self, -1, langStr('Select active lcs', 'Zvolit zatěžovací stav'), (10, 120))
        ##self.stabilityLcsCTRL = wx.ComboBox(self, -1, pos=(10, 140), size=(160, -1), style=wx.CB_READONLY)

        ##self.stabilityOptions.append(solverBox)
        ##self.stabilityOptions.append(self.stabilityLcsCTRL)
        ##self.stabilityOptions.append(lcsText)
        ##HideStabilityOptions()
        
        # bottom buttons
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        #
        #self.defScaleSlider = wx.Slider(self, -1, 50, 0, 100, (20, 140), (110, -1))

    def OnSelect(self, event ):
        ctrl = event.GetEventObject()
        item = event.GetSelection()

        if ctrl == self.problemCTRL:
            if item == 0:
                session.setSolver(LinearStaticSolver())
                self.HideStabilityOptions()
            elif item == 1:
                session.setSolver(LinearStabilitySolver())
                self.ShowStabilityOptions()
        ##elif ctrl == self.stabilityLcsCTRL:
        ##    session.solver.activeLCS = item
        ##    print "Selected ", item, " as active LCS"
        ##    logger.info(langStr('Load should be applied in Default_loadcase', 'Zatížení musí být definováno v Default_loadcase') )

        self.glframe.context.postProcessBox = session.solver.postProcesorBox(self.glframe.context,wx.NewId(),self.glframe)
        self.glframe.context.postProcessBox.Hide()
        

    def enable(self, show=True):
        ##self.stabilityLcsCTRL.Clear()
        ##self.stabilityLcsCTRL.AppendItems([key for key in sorted(session.domain.loadCases.iterkeys())])
        ##self.stabilityLcsCTRL.SetValue( session.domain.activeLoadCase.label if session.domain.activeLoadCase else '' )
        self.Show(show)
        self.parent.currentBox = self

    def reset(self):
        pass

    def disable(self):
        self.Hide()

    def OnClose (self, event):
        self.disable()   
        self.glframe.canvas.SetFocus()

    def ShowStabilityOptions(self):
        ##for i in self.stabilityOptions:
        ##            i.Show()
        pass

    def HideStabilityOptions(self):
        ##for i in self.stabilityOptions:
        ##            i.Hide()
        pass
        


class ScaleBox(wx.Panel):
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent = parent
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        wx.StaticBox(self, -1, langStr('Scale settings', 'Nastavení měřítek'), (0,0), mainBoxSize)
        wx.StaticText(self, -1, langStr('Boundary cond.: ', 'Okr. podmínky:'), (10, 30))
        self.bc = wx.TextCtrl(self, -1, '1.0',  (130, 30), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Load, reactions: ', 'Zatíž. a reakce: '), (10, 60))
        self.load = wx.TextCtrl(self, -1, '1.0',  (130, 60), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Deformed geom.: ', 'Deform. tvar:'), (10, 90))
        self.defGeom = wx.TextCtrl(self, -1, '1.0',  (130, 90), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Internal forces: ', 'Vnitřní síly:'), (10, 120))
        self.intForces = wx.TextCtrl(self, -1, '1.0',  (130, 120), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Lines width: ', 'Tloušťka čar:'), (10, 150))
        self.lineWidth = wx.TextCtrl(self, -1, '1.0',  (130, 150), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Forces/moments: ', 'Síly/momenty:'), (10, 180))
        self.momentForce = wx.TextCtrl(self, -1, '1.0',  (130, 180), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Presc. dspl: ', 'Předeps. posuny:'), (10, 210))
        self.pDspl = wx.TextCtrl(self, -1, '1.0',  (130, 210), (70, -1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Font size: ', 'Vel. písma:'), (10, 240))
        self.fontSize = wx.ComboBox(self, -1, pos=(130,240), size=(70, -1), style=wx.CB_READONLY, choices=['10','12','18'], value='12')
        self.Bind(wx.EVT_COMBOBOX, self.OnSetScale)
        wx.StaticText(self, -1, langStr('Scale load: ', 'Zatíž. v měřítku:'), (10, 270))
        self.uniLoadSizeCB = wx.CheckBox(self, -1, "", (130,270))
        self.Bind(wx.EVT_CHECKBOX, self.glframe.toggleUniLoadSize)

        autoscale_btn = wx.Button(self, 1, langStr('&AutoScale', '&Auto. měř.'), (10,300), (btSize1[0]-10,btSize1[1]) )
        wx.EVT_BUTTON(self, 1, self.glframe.autoScale)
        wx.Button(self, 3, langStr('&Default', 'Výchozí (&d)'), (100,300), btSize1)
        wx.EVT_BUTTON(self, 3, self.OnDefault)
        btn = wx.Button(self, 2, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 2, self.OnSetScale)
        btn.SetFocus()
        wx.Button(self, 3, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 3, self.OnClose)
        self.onmousemove = None

    def enable(self, show=True):
        # update label (necessary if new file opened)
        self.bc.SetValue(str('{0:.3g}'.format(float(globalSizesScales.bcSize))))
        self.load.SetValue(str('{0:.3g}'.format(float(globalSizesScales.loadSize))))
        self.defGeom.SetValue(str('{0:.3g}'.format(float(globalSizesScales.deformationScale))))
        self.intForces.SetValue(str('{0:.3g}'.format(float(globalSizesScales.intForceScale))))
        self.lineWidth.SetValue(str('{0:.3g}'.format(float(globalSizesScales.lineWidthCoeff))))
        self.momentForce.SetValue(str('{0:.3g}'.format(float(globalSizesScales.momentForceRatio))))
        self.pDspl.SetValue(str('{0:.3g}'.format(float(globalSizesScales.pDsplSize))))
        self.fontSize.SetValue(str('{0:.3g}'.format(float(globalSizesScales.fontSize))))
        self.uniLoadSizeCB.SetValue(not int(globalSizesScales.useUniLoadSize))
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()

    def OnSetScale (self, event):
        globalSizesScales.bcSize = '{0:.3g}'.format(float(self.bc.GetValue()))
        globalSizesScales.loadSize = '{0:.3g}'.format(float(self.load.GetValue()))
        globalSizesScales.deformationScale = '{0:.3g}'.format(float(self.defGeom.GetValue()))
        globalSizesScales.intForceScale = '{0:.3g}'.format(float(self.intForces.GetValue()))
        globalSizesScales.lineWidthCoeff = '{0:.3g}'.format(float(self.lineWidth.GetValue()))
        globalSizesScales.momentForceRatio = '{0:.3g}'.format(float(self.momentForce.GetValue()))
        globalSizesScales.pDsplSize = '{0:.3g}'.format(float(self.pDspl.GetValue()))
        globalSizesScales.fontSize = '{0:d}'.format(int(self.fontSize.GetValue()))
        self.glframe.Refresh(False)

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def OnDefault(self, event):
        globalSizesScales.update(defaultGlobalSizesScales)
        self.glframe.Refresh()  
        self.enable()




class PythonBox(wx.Panel):
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent = parent
        self.shellFrames = []
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        #
        wx.StaticBox(self, -1, langStr('Python', 'Python'), (0,0), mainBoxSize)
        wx.StaticText(self, -1, langStr('Python command: ', 'Příkaz Pythonu: '),labelTextPos)
        self.commandText = wx.TextCtrl(self, -1, '', (10,40), (160,160),style=wx.TE_MULTILINE)
        #
        execBtn = wx.Button(self, 2, langStr('Exec', 'Exec'), (btPos1[0],btPos1[1]-33), btSize1)
        wx.EVT_BUTTON(self, 2, self.execCommand)
        execBtn.SetFocus()
        #
        shellBtn = wx.Button(self, 3, langStr('Shell', 'Shell'), (btPos2[0],btPos2[1]-33), btSize1)
        wx.EVT_BUTTON(self, 3, self.launchPythonShell)
        shellBtn.SetFocus()
        #
        evalBtn = wx.Button(self, 1, langStr('Eval', 'Eval'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 1, self.evalCommand)
        evalBtn.SetFocus()
        #
        wx.Button(self, 4, langStr('&Close', 'Zavři (&c)'), btPos2, btSize1)
        wx.EVT_BUTTON(self, 4, self.OnClose)

    def launchPythonShell(self, event):
        try:
            from wx.py.shell import Shell
        except ImportError:
            logger.error( langStr('Required package wx.py.shell not found', 'Požadovaný balík wx.py.shell nebyl nalezen') )
            return
        frm = wx.Frame(None,size=(700,500))
        self.shellFrames.append(frm)
        sh = Shell(frm)
        frm.Show()

    def quitShellFrames(self):
        for frm in self.shellFrames:
            if frm:
               frm.Destroy()

    def enable(self, show=True):
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()
        
    def evalCommand(self, event):
        print (eval(self.commandText.GetValue()))

    def execCommand(self, event):
        exec(self.commandText.GetValue())

    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

class GridBox(wx.Panel):
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent = parent
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        #
        wx.StaticBox(self, -1, langStr('Grid settings', 'Nastavit mřížku'), (0,0), mainBoxSize)
        wx.StaticText(self, wx.NewId(), langStr('Origin [x]: ', 'Počátek [x]: '), (10,30))
        wx.StaticText(self, wx.NewId(), langStr('Origin [z]: ', 'Počátek [y]: '), (10,60))
        self.gox=wx.TextCtrl(self, wx.NewId(), "", (100, 30), (100, -1), style=wx.TE_PROCESS_ENTER)
        self.goz=wx.TextCtrl(self, wx.NewId(), "", (100, 60), (100, -1), style=wx.TE_PROCESS_ENTER)
        self.gox.Bind(wx.EVT_TEXT_ENTER, self.OnSetGrid)
        self.goz.Bind(wx.EVT_TEXT_ENTER, self.OnSetGrid)
        wx.StaticText(self, wx.NewId(), langStr('Grid delta: ', 'Krok mřížky: '), (10, 90))
        self.gd=wx.TextCtrl(self, wx.NewId(), "", (100, 90), (100, -1), style=wx.TE_PROCESS_ENTER)
        self.gd.Bind(wx.EVT_TEXT_ENTER, self.OnSetGrid)
        wx.StaticText(self, wx.NewId(), langStr('Grid count: ', 'Počet mříží: '), (10, 120))
        self.gc=wx.TextCtrl(self, wx.NewId(), "", (100, 120), (100, -1), style=wx.TE_PROCESS_ENTER)
        self.gc.Bind(wx.EVT_TEXT_ENTER, self.OnSetGrid)
        wx.StaticText(self, wx.NewId(), langStr('Snap delta: ', 'Krok chytání: '), (10, 150))
        self.gs=self.snap = wx.TextCtrl(self, wx.NewId(), "", (100, 150), (100, -1),  style=wx.TE_PROCESS_ENTER)
        self.gs.Bind(wx.EVT_TEXT_ENTER, self.OnSetGrid)
        #
        set_btn = wx.Button(self, 1, langStr('Chan&ge', 'Změnit (&g)'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 1, self.OnSetGrid)
        set_btn.SetFocus()
        wx.Button(self, 2, langStr('&Close', 'Zavřít (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        self.onmousemove = None
        #
        wx.Button(self, 3, langStr('&Default', 'Výchozí (&d)'), (100,180), btSize1)
        wx.EVT_BUTTON(self, 3, self.OnDefault)
        #
        if None:
            # nice automatic layout setup using box sizers, but works only in Linux
            sb = wx.StaticBox(self, label=langStr('Grid settings', 'Nastavení mřížky'))
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            
            fgs = wx.FlexGridSizer(6, 2, 9, 25)
            
            r11=wx.StaticText(self, wx.NewId(), langStr('Grid Origin: ', 'Počátek mřížky: '))
            r21=wx.StaticText(self, wx.NewId(), 'x: ')
            r31=wx.StaticText(self, wx.NewId(), 'z: ')
            self.gox=self.origin_x = wx.TextCtrl(self, wx.NewId(), str(globalGridSettings.gridOrigin[0]), style=wx.TE_PROCESS_ENTER)
            self.goz=self.origin_z = wx.TextCtrl(self, wx.NewId(), str(globalGridSettings.gridOrigin[1]), style=wx.TE_PROCESS_ENTER)
            r41=wx.StaticText(self, wx.NewId(), langStr('Grid delta: ', 'Krok mřížky: '))
            self.gd=self.delta = wx.TextCtrl(self, wx.NewId(), str(globalGridSettings.gridDelta[0]), style=wx.TE_PROCESS_ENTER)
            r51=wx.StaticText(self, wx.NewId(), langStr('Grid count: ', 'Počet mříží: '))
            self.gc=self.count = wx.TextCtrl(self, wx.NewId(), str(globalGridSettings.gridCount), style=wx.TE_PROCESS_ENTER)
            r61=wx.StaticText(self, wx.NewId(), langStr('Snap delta: ', 'Krok chytání: '))
            self.gs=self.snap = wx.TextCtrl(self, wx.NewId(), str(globalGridSettings.gridSnap[0]), style=wx.TE_PROCESS_ENTER)
            

            fgs.AddMany([(r11), (wx.StaticText(self), wx.EXPAND), 
                         (r21), (self.gox, 1, wx.EXPAND), 
                         (r31), (self.goz, 1, wx.EXPAND),
                         (r41), (self.gd, 1, wx.EXPAND),
                         (r51), (self.gc, 1, wx.EXPAND),
                         (r61), (self.gs, 1, wx.EXPAND)])
            
            #fgs.AddGrowableRow(2, 1)
            #fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            set_btn = wx.Button(self, 1, langStr('Set', 'Nastav'))
            wx.EVT_BUTTON(self, 1, self.OnSetGrid)
            #set_btn.SetFocus()
            cls_btn=wx.Button(self, 2, langStr('&Close', 'Zavři (&c)'))
            wx.EVT_BUTTON(self, 2, self.OnClose)
            hbox.Add(set_btn)
            hbox.Add(cls_btn)
        
            boxsizer.Add(hbox, border=10)
            self.SetSizer(boxsizer)

    def enable(self, show=True):
        self.gox.SetValue(str(globalGridSettings.gridOrigin[0]))
        self.goz.SetValue(str(globalGridSettings.gridOrigin[1]))
        self.gd.SetValue(str(globalGridSettings.gridDelta[0]))
        self.gc.SetValue(str(globalGridSettings.gridCount))
        self.gs.SetValue(str(globalGridSettings.gridSnap[0]))
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()

    def OnSetGrid (self, event):
        globalGridSettings.gridOrigin[0] = float(self.gox.GetValue())
        globalGridSettings.gridOrigin[1] = float(self.goz.GetValue())
        globalGridSettings.gridDelta[0]=globalGridSettings.gridDelta[1] = float(self.gd.GetValue())
        globalGridSettings.gridCount = int(self.gc.GetValue())
        globalGridSettings.gridSnap[0]=globalGridSettings.gridSnap[1]=float(self.gs.GetValue())
        self.glframe.Refresh(False)
        #
        return
        
    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()

    def OnDefault(self, event):
        globalGridSettings.update(defaultGlobalGridSettings)
        self.glframe.Refresh()  
        self.enable()


class MySheet(sheet.CSheet):
    def __init__(self, parent, id):
        sheet.CSheet.__init__(self, parent)
        self.SetLabelBackgroundColour('#DBD4D4')
        self.SetDefaultColSize(120, True)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        
    def OnKey(self,event):
        currCell = (self.GetGridCursorRow(), self.GetGridCursorCol())
        if event.ControlDown() and event.GetKeyCode() == 67:# If Ctrl+C is pressed
            if(self.IsSelection()):
                self.Copy()#copy to clipboard
        elif event.ControlDown() and event.GetKeyCode() == 65:# If Ctrl+A is pressed
            self.SelectAll()
        elif event.GetKeyCode() == 366:# PgUp is pressed
            self.MovePageUp()
        elif event.GetKeyCode() == 367:# PgDown is pressed
            self.MovePageDown()
        elif event.GetKeyCode() == 314:# Left arrow is pressed. If shift simultaneously, mark the region
            self.MoveCursorLeft(event.ShiftDown())
        elif event.GetKeyCode() == 316:# Right arrow is pressed. If shift simultaneously, mark the region
            self.MoveCursorRight(event.ShiftDown())
        elif event.GetKeyCode() == 315:# Up arrow is pressed. If shift simultaneously, mark the region
            self.MoveCursorUp(event.ShiftDown())
        elif event.GetKeyCode() == 317:# Down arrow is pressed. If shift simultaneously, mark the region
            self.MoveCursorDown(event.ShiftDown())
        #event.Skip() 


class Notebook(wx.Frame):
    from ebio import saveNotebook
    save = saveNotebook
    """Saving method (defined in ebio.py)"""
    def __init__(self, parent, id=-1, title=''):
        wx.Frame.__init__(self, parent, id, title, size=(1200, 500))
        menubar = wx.MenuBar()
        file = wx.Menu()
        file.Append(101, langStr('&Quit', '&Zavřít')+'\tCtrl+Q', '' )
        file.Append(102, langStr('&Save as', '&Uložit jako')+'\tCtrl+Shift+S', '' )
        menubar.Append(file, langStr('&File', '&Soubor'))
        self.SetMenuBar(menubar)
        wx.EVT_MENU(self, 101, parent.ResultsToSpreadsheetClose)
        wx.EVT_MENU(self, 102, self.saveFileAsMenu)
        self.nb = wx.Notebook(self, -1, style=wx.NB_BOTTOM)
        self.StatusBar()
        #self.Nodes.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        #self.Elements.Bind(wx.EVT_KEY_DOWN, self.OnKey)
    
    def importData(self,how='linStatResults',**kw):    
        if   how == 'linStatResults':
            self.importData_linStatResults()
        elif how == 'linStatGlobMatrix':
            self.importData_linStatGlobMatrix()
        elif how == 'linStatElemMatrix':
            self.importData_linStatElemMatrix(**kw)
        else:
            raise EduBeamError
            print('Notebook.importData: wrong argument')

    def importData_linStatGlobMatrix(self):
        kuu,kpp,kup = session.solver.assembleStiffnessMatrix()
        r,f = session.solver.r[session.domain.activeLoadCase.label], session.solver.f[session.domain.activeLoadCase.label]
        self.k = MySheet(self.nb,1)
        self.r = MySheet(self.nb,2)
        self.f = MySheet(self.nb,3)
        nu,np = size(kuu,0), size(kpp,0)
        self.k.SetNumberRows(nu+np+1)
        self.k.SetNumberCols(nu+np+1)
        self.r.SetNumberRows(nu+np+1)
        self.r.SetNumberCols(2)
        self.f.SetNumberRows(nu+np+1)
        self.f.SetNumberCols(2)
        self.nb.AddPage(self.k, langStr('Stiffness matrix', 'Matice tuhosti'))
        self.nb.AddPage(self.r, langStr('Nodal displacements', 'Uzlové posuny'))
        self.nb.AddPage(self.f, langStr('Nodal forces', 'Uzlové síly'))
        self.k.SetFocus()
        # k
        self.k.SetCellValue(0,0, 'dof/dof')
        for col in xrange(nu):
            self.k.SetCellValue(0, col+1, str(col)+', u, '+session.solver.dofNames[col])
        for col in xrange(np):
            self.k.SetCellValue(0, col+1+nu, str(col+nu)+', p, '+session.solver.dofNames[col+nu])
        for row in xrange(nu):
            self.k.SetCellValue(row+1, 0, str(row)+', u, '+session.solver.dofNames[row])
            for col in xrange(nu):
                self.k.SetCellValue(row+1, col+1, '%g'%kuu[row,col] )
            for col in xrange(np):
                self.k.SetCellValue(row+1, col+1+nu, '%g'%kup[row,col] )
        for row in xrange(np):
            self.k.SetCellValue(row+1+nu, 0, str(row+nu)+', p, '+session.solver.dofNames[row+nu])
            for col in xrange(nu):
                self.k.SetCellValue(row+1+nu, col+1, '%g'%kup[col,row] )
            for col in xrange(np):
                self.k.SetCellValue(row+1+nu, col+1+nu, '%g'%kpp[row,col] )
        # r
        self.r.SetCellValue(0,0, 'dof')
        self.r.SetCellValue(0,1, 'value')
        for row in xrange(nu):
            self.r.SetCellValue(row+1, 0, str(row)+', u, '+session.solver.dofNames[row])
            self.r.SetCellValue(row+1, 1, '%g'%r[row] )
        for row in xrange(np):
            self.r.SetCellValue(row+1+nu, 0, str(row+nu)+', p, '+session.solver.dofNames[row+nu])
            self.r.SetCellValue(row+1+nu, 1, '%g'%r[row+nu] )
        # f
        self.f.SetCellValue(0,0, 'dof')
        self.f.SetCellValue(0,1, 'value')
        for row in xrange(nu):
            self.f.SetCellValue(row+1, 0, str(row)+', u, '+session.solver.dofNames[row])
            self.f.SetCellValue(row+1, 1, '%g'%f[row] )
        for row in xrange(np):
            self.f.SetCellValue(row+1+nu, 0, str(row+nu)+', p, '+session.solver.dofNames[row+nu])
            self.f.SetCellValue(row+1+nu, 1, '%g'%f[row+nu] )

    def importData_linStatElemMatrix(self,elem):
        elem = session.domain.giveElement(elem)
        if not elem:
            logger.error( langStr('wrong element', 'Chybný prvek') )
            self.parent.ResultsToSpreadsheetClose()
        kl  = elem.computeLocalStiffness()
        kg  = elem.computeStiffness()
        f,r = elem.computeEndValues(session.solver.r[session.domain.activeLoadCase.label])
        self.kl = MySheet(self.nb,1)
        self.kg = MySheet(self.nb,2)
        self.r  = MySheet(self.nb,3)
        self.f  = MySheet(self.nb,4)
        self.kl.SetNumberRows(6)
        self.kl.SetNumberCols(6)
        self.kg.SetNumberRows(6)
        self.kg.SetNumberCols(6)
        self.r.SetNumberRows(6)
        self.r.SetNumberCols(1)
        self.f.SetNumberRows(6)
        self.f.SetNumberCols(1)
        self.nb.AddPage(self.kl, langStr('Stiffness matrix (local)', 'Matice tuhosti (lokální)'))
        self.nb.AddPage(self.kg, langStr('Stiffness matrix (global)', 'Matice tuhosti (globální)'))
        self.nb.AddPage(self.r, langStr('End displacements (local)', 'Koncové posuny (lokální)'))
        self.nb.AddPage(self.f, langStr('End forces (local)', 'Koncové síly (lokální)'))
        self.kl.SetFocus()
        # kl
        for row in xrange(6):
            for col in xrange(6):
                self.kl.SetCellValue(row, col, '%g'%kl[row,col] )
        # kg
        for row in xrange(6):
            for col in xrange(6):
                self.kg.SetCellValue(row, col, '%g'%kg[row,col] )
        # r
        for row in xrange(6):
            self.r.SetCellValue(row, 0, '%g'%r[row] )
        # f
        for row in xrange(6):
            self.f.SetCellValue(row, 0, '%g'%f[row] )

    def importData_linStatResults(self):
        self.Nodes = MySheet(self.nb,1)
        self.Elements = MySheet(self.nb,2)
        self.Nodes.SetNumberRows(len(session.domain.nodes)+1)
        self.Nodes.SetNumberCols(10)
        self.Elements.SetNumberRows(len(session.domain.elements)+1)
        self.Elements.SetNumberCols(15)
        self.nb.AddPage(self.Nodes, langStr('Nodes', 'Uzly'))
        self.nb.AddPage(self.Elements, langStr('Elements', 'Prvky'))
        self.Nodes.SetFocus()
        # nodes
        header = [langStr('Node', 'Uzel') , 'x [~m]' , 'y [~m]' , 'z [~m]' , 'u [~m]' , 'w [~m]' , 'phi [~rad]', 'Rx [~N]', 'Rz [~N]' , 'Rm [~Nm]']
        for i in xrange(0,len(header)):
            self.Nodes.SetCellValue(0,i, header[i])
        r = session.solver.r[session.domain.activeLoadCase.label]
        f = session.solver.f[session.domain.activeLoadCase.label]
        row = 1
        sortedNodes = sorted(session.domain.nodes.values(), key=lambda n: natural_key(n.label))
        for n in sortedNodes:
            c = n.coords
            data = []
            data.append(n.label)
            data.append('{0:g}'.format(c[0]))
            data.append('{0:g}'.format(c[1]))
            data.append('{0:g}'.format(c[2]))
            data.append('{0:.8g}'.format(r[n.loc[0]]))
            data.append('{0:.8g}'.format(r[n.loc[1]]))
            data.append('{0:.8g}'.format(r[n.loc[2]]))
            data.append( ('{0:.8g}'.format(f[n.loc[0]])) if n.hasPrescribedBcInDof(0) else '-'  )
            data.append( ('{0:.8g}'.format(f[n.loc[1]])) if n.hasPrescribedBcInDof(1) else '-'  )
            data.append( ('{0:.8g}'.format(f[n.loc[2]])) if n.hasPrescribedBcInDof(2) else '-'  )
            for i in xrange(0,len(data)):
                self.Nodes.SetCellValue(row, i, data[i])
            row = row + 1
        # elements
        header = [langStr('Element', 'Prvek') , '(a-b)' , 'u_a^l [~m]' , 'w_a^l [~m]' , 'phi_a [~rad]' , 'u_b^l [~m]' , 'w_b^l [~m]', 'phi_b [~rad]', 'X_a^l [~N]' , 'Z_a^l [~N]', 'M_a [~Nm]' , 'X_b^l [~N]' , 'Z_b^l [~N]' , 'M_b [~Nm]' , 'N [~N]']
        for i in xrange(0,len(header)):
            self.Elements.SetCellValue(0,i, header[i])
        row = 1
        sortedElems = sorted(session.domain.elements.values(), key=lambda n: natural_key(n.label))
        for e in sortedElems:
            l,d = e.computeEndValues(session.solver.r[session.domain.activeLoadCase.label])
            data = []
            data.append(smart_str(e.label))
            data.append(e.nodes[0].label + '-' + e.nodes[1].label)
            data.append('{0:.8g}'.format(d[0]))
            data.append('{0:.8g}'.format(d[1]))
            data.append('{0:.8g}'.format(d[2]))
            data.append('{0:.8g}'.format(d[3]))
            data.append('{0:.8g}'.format(d[4]))
            data.append('{0:.8g}'.format(d[5]))
            data.append('{0:.8g}'.format(l[0]))
            data.append('{0:.8g}'.format(l[1]))
            data.append('{0:.8g}'.format(l[2]))
            data.append('{0:.8g}'.format(l[3]))
            data.append('{0:.8g}'.format(l[4]))
            data.append('{0:.8g}'.format(l[5]))
            data.append( ('{0:.8g}'.format(l[3])) if abs(l[0]+l[3])<1.e-8 else '-')#only when constant normal force
            for i in xrange(0,len(data)):
                self.Elements.SetCellValue(row, i, data[i])
            row = row + 1

    def StatusBar(self):
        self.statusbar = self.CreateStatusBar()

    def saveFileAsMenu(self, event):
        if 'xls' in sheetExportFormats:
            wcd = langStr('Xls files (*.xls)|*.xls;*.XLS;*.Xls|Csv files (*.csv)|*.csv;*.CSV;*.Csv|All files (*)|*', 'Xls soubory (*.xls)|*.xls;*.XLS;*.Xls|Csv soubory (*.csv)|*.csv;*.CSV;*.Csv|Všechny soubory (*)|*')
        else:
            wcd = langStr('Csv files (*.csv)|*.csv;*.CSV;*.Csv|All files (*)|*', 'Csv soubory (*.csv)|*.csv;*.CSV;*.Csv|Všechny soubory (*)|*')
        dir = os.getcwd()
        open_dlg = wx.FileDialog(self, message=langStr('Enter a file for saving', 'Zadej soubor pro uložení'), defaultDir=dir, defaultFile='',
                                 wildcard=wcd, style=wx.SAVE|wx.CHANGE_DIR)
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            if open_dlg.GetFilterIndex() == 0:
                pl = path.lower()
                if not (pl.endswith('.xls') or pl.endswith('.csv')):
                    path += ('.xls' if 'xls' in sheetExportFormats else '.csv')
                pl = path.lower()
                fFormat = 'xls' if pl.endswith('.xls') else 'csv' if pl.endswith('.csv') else None
            if os.path.isfile(path):#if the file already exists
                dlg = wx.MessageDialog(self, langStr('File %s already exists. Overwrite?\n', 'Soubor %s již existuje. Přepsat?\n') % path, style=wx.YES_NO)
                if dlg.ShowModal() == wx.ID_NO:
                    return
                dlg.Destroy()
            try:
                with open(path, 'wb') as file:
                    self.save(file, fFormat)
                    file.close()
            except (IOError,EduBeamError) as error:
                dlg = wx.MessageDialog(self, langStr('Error saving file\n', 'Chyba při ukládání souboru\n') + str(error))
                dlg.ShowModal()
                return
            logger.info( langStr('Table successfully saved to file %s','Tabulka úspěšně uložena do souboru %s') % (str(path)) )
        open_dlg.Destroy()




class ColorSetupBox(wx.Panel):
    def __init__(self, parent, id, glframe):
        self.glframe = glframe
        self.parent=parent
        wx.Panel.__init__(self, parent, id=-1, pos=panelPos, size=panelSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr) 
        #
        wx.StaticBox(self, -1, langStr('Color settings', 'Nastavení barev'), (0,0), mainBoxSize)
        #
        wx.StaticText(self, wx.NewId(), langStr('Nodal color', 'Barva uzlů'), (10, 30))
        self.nodecolorBtn = wx.Button(self, wx.NewId(), '   ', (110,30), (50,20))
        self.nodecolorBtn.SetBackgroundColour([c*255 for c in globalSettings.nodeColor])
        self.nodecolorBtn.Bind(wx.EVT_BUTTON, self.selectNodalColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Element color', 'Barva prvků'), (10, 60))
        self.elemcolorBtn = wx.Button(self, wx.NewId(), '   ', (110,60), (50,20))
        self.elemcolorBtn.SetBackgroundColour([c*255 for c in globalSettings.elemColor])
        self.elemcolorBtn.Bind(wx.EVT_BUTTON, self.selectElementColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Normal Force', 'Normálová síla'), (10, 90))
        self.NcolorBtn = wx.Button(self, wx.NewId(), '   ', (110,90), (50,20))
        self.NcolorBtn.SetBackgroundColour([c*255 for c in globalSettings.nForceColor])
        self.NcolorBtn.Bind(wx.EVT_BUTTON, self.selectNColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Shear Force', 'Posouvající síla'), (10, 120))
        self.VcolorBtn = wx.Button(self, wx.NewId(), '   ', (110,120), (50,20))
        self.VcolorBtn.SetBackgroundColour([c*255 for c in globalSettings.vForceColor])
        self.VcolorBtn.Bind(wx.EVT_BUTTON, self.selectVColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Moments', 'Momenty'), (10, 150))
        self.McolorBtn = wx.Button(self, wx.NewId(), '   ', (110,150), (50,20))
        self.McolorBtn.SetBackgroundColour([c*255 for c in globalSettings.mForceColor])
        self.McolorBtn.Bind(wx.EVT_BUTTON, self.selectMColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Selection', 'Výběr'), (10, 180))
        self.hilitColorBtn = wx.Button(self, wx.NewId(), '   ', (110,180), (50,20))
        self.hilitColorBtn.SetBackgroundColour([c*255 for c in globalSettings.hilitColor])
        self.hilitColorBtn.Bind(wx.EVT_BUTTON, self.selectHilitColor)
        #
        wx.StaticText(self, wx.NewId(), langStr('Preview', 'Preview'), (10, 210))
        self.previewColorBtn = wx.Button(self, wx.NewId(), '   ', (110,210), (50,20))
        self.previewColorBtn.SetBackgroundColour([c*255 for c in globalSettings.previewColor])
        self.previewColorBtn.Bind(wx.EVT_BUTTON, self.selectPreviewColor)
        #
        wx.Button(self, 3, langStr('&Default', 'Výchozí (&d)'), btPos1, btSize1)
        wx.EVT_BUTTON(self, 3, self.OnDefault)
        wx.Button(self, 2, langStr('&Close', 'Zavři (&c)'), btPos2, btSize2)
        wx.EVT_BUTTON(self, 2, self.OnClose)
        #
        self.onmousemove = None

    def enable(self, show=True):
        # update label (necessary if new file opened)
        # self.bc.SetValue(str(bcSize))
        #self.load.SetValue(str(loadSize))
        #self.defGeom.SetValue(str(deformationScale))
        #self.intForces.SetValue(str(intForceScale))
        self.Show(show)
        self.parent.currentBox = self

    def disable(self):
        self.Hide()

    def selectNodalColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.nodecolorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.nodeColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()  

    def selectElementColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.elemcolorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.elemColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

    def selectNColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.NcolorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.nForceColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

    def selectVColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.VcolorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.vForceColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

    def selectMColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.McolorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.mForceColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

    def selectHilitColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.hilitColorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.hilitColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

    def selectPreviewColor(self, event):
        """display the colour dialog and select"""
        c = self.selectColor()
        if c: 
            self.previewColorBtn.SetBackgroundColour(c)
            self.Refresh()
            globalSettings.previewColor = (c[0]/255., c[1]/255., c[2]/255.)
            self.glframe.Refresh()

       
    def selectColor(self):
        """display the colour dialog and select"""
        rgb=None
        dlg = wx.ColourDialog(self)
        # get the full colour dialog
        # default is False and gives the abbreviated version
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            # gives red, green, blue tuple (r, g, b)
            # each rgb value has a range of 0 to 255
            rgb = data.GetColour().Get()
            s = langStr('The selected color (r, g, b) = %s', 'Vybrána barva (r, g, b) = %s') % str(rgb)
            logger.info( s )
        dlg.Destroy()
        return rgb
   
    def OnDefault(self, event):
        for color in defaultGlobalSettings.iterkeys():
            if color in colorsInDefaultSetup:
                globalSettings[color] = defaultGlobalSettings[color]
        self.nodecolorBtn.SetBackgroundColour([c*255. for c in globalSettings.nodeColor])
        self.elemcolorBtn.SetBackgroundColour([c*255. for c in globalSettings.elemColor])
        self.NcolorBtn.SetBackgroundColour([c*255. for c in globalSettings.nForceColor])
        self.VcolorBtn.SetBackgroundColour([c*255. for c in globalSettings.vForceColor])
        self.McolorBtn.SetBackgroundColour([c*255. for c in globalSettings.mForceColor])
        self.hilitColorBtn.SetBackgroundColour([c*255. for c in globalSettings.hilitColor])
        self.previewColorBtn.SetBackgroundColour([c*255. for c in globalSettings.previewColor])
        logger.info( langStr('Colors set to default','Barvy nastaveny na výchozí hodnoty') )
        self.glframe.Refresh()  
      
    def OnClose (self, event):
        self.disable()
        self.glframe.canvas.SetFocus()






##################################################################
#
# Graphical functions for classes from ebfem.py
#
##################################################################

##################################################################
# Node
##################################################################
def OnDraw (self):
    """ Draws receiver geometry, label, boundary conds"""
    if globalFlags.nodeDisplayFlag:
        (r,g,b) = globalSettings.nodeColor
        glPointSize(6.0)        
        glColor3f(r,g,b)
        glBegin(GL_POINTS)
        glVertex3f (self.coords[0],self.coords[1], self.coords[2] )
        glEnd()
        #
        if globalFlags.labelDisplayFlag:
            glPrintString (self.coords[0], self.coords[1], self.coords[2], self.label)
        glDefaultColor()
    #
    if globalFlags.bcDisplayFlag:
        bcs = self.giveBCs()
        if   bcs == (True,True,True):
            self.drawClampedEnd()
        elif bcs == (True,True,False):
            self.drawHinge()
        elif bcs == (True,False,False):
            self.drawHinge(angle=0.5*math.pi,sliding=True)
        elif bcs == (False,True,False):
            self.drawHinge(sliding=True)
        elif bcs == (True,False,True):
            self.drawSlidingClampedEnd(angle=0.5*math.pi)
        elif bcs == (False,True,True):
            self.drawSlidingClampedEnd()
        elif bcs == (False,False,True):
            self.drawFixedRotation()
              
def OnDrawResults(self, useUniformSize=True):
    if not self.domain.session.solver.isSolved:
        raise EduBeamError
        return
    if globalFlags.intForcesDisplayFlag[3]:
        (r,g,b) = globalSettings.rForceColor
        glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
        glColor3f(r,g,b)
        value = {'fx':0., 'fy':0., 'fz':0., 'mx':0., 'my':0., 'mz':0.} # 'x', 'y', 'z' for forces, 'X', 'Y', 'Z' for moments
        co = self.coords
        fr = self.domain.session.solver.f[session.domain.activeLoadCase.label]
        if self.bcs['x']: # x direction
            val = value['fx'] = fr[ self.loc[0] ]
            size = float(globalSizesScales.loadSize) * val
            if useUniformSize and val:
                size /= abs(val)
            glArrow(co[0],co[1],co[2],size,0.)
        if self.bcs['z']: # z direction
            val = value['fz'] = fr[ self.loc[1] ]
            size = float(globalSizesScales.loadSize) * val
            if useUniformSize and val:
                size /= abs(val)
            glArrow(co[0],co[1],co[2],0.,size)
        if self.bcs['Y']: # y moment
            val = value['my'] = fr[ self.loc[2] ]
            size = float(globalSizesScales.loadSize)*float(globalSizesScales.momentForceRatio) * val
            if useUniformSize and val:
                size /= abs(val)
            glArrowMoment(co[0],co[1],co[2],size)
        if self.giveBCs() != (False,False,False):
            glPrintString(co[0], co[1], co[2], '%.2f, %.2f, %.2f' % (abs(value['fx']), abs(value['fz']), abs(value['my'])) )
        glDefaultColor()

def drawClampedEnd(self,angle=0.0,w=0.8,h=0.35):
    """Draw clamped end (all 3 dofs fixed)"""
    c = math.cos(angle)
    s = math.sin(angle) # positive angle is clockwise, is it ok? TODO
    bs = float(globalSizesScales.bcSize)
    co = self.coords
    (r,g,b) = globalSettings.bcColor
    glColor3f(r,g,b)
    glBegin(GL_LINES)
    glVertex3f(co[0]+c*(-w*bs),co[1],co[2]+s*(-w*bs))
    glVertex3f(co[0]+c*( w*bs),co[1],co[2]+s*( w*bs))
    # hatching
    glVertex3f(co[0]+c*(      -w*bs)-s*h*bs,co[1],co[2]+s*(      -w*bs)+c*h*bs)
    glVertex3f(co[0]+c*(  (-w+h)*bs)      ,co[1],co[2]+s*(  (-w+h)*bs)      )
    glVertex3f(co[0]+c*(  (-w+h)*bs)-s*h*bs,co[1],co[2]+s*(  (-w+h)*bs)+c*h*bs)
    glVertex3f(co[0]+c*((-w+2*h)*bs)      ,co[1],co[2]+s*((-w+2*h)*bs)      )
    glVertex3f(co[0]+c*((-w+2*h)*bs)-s*h*bs,co[1],co[2]+s*((-w+2*h)*bs)+c*h*bs)
    glVertex3f(co[0]+c*((-w+3*h)*bs)      ,co[1],co[2]+s*((-w+3*h)*bs)      )
    glVertex3f(co[0]+c*((-w+3*h)*bs)-s*h*bs,co[1],co[2]+s*((-w+3*h)*bs)+c*h*bs)
    glVertex3f(co[0]+c*((-w+4*h)*bs)      ,co[1],co[2]+s*((-w+4*h)*bs)      )
    glEnd()
    glDefaultColor()

def drawHinge(self,angle=0.0,w=0.5,h=0.7,sliding=False,gap=0.2):
    """draw hinge support"""
    c = math.cos(angle)
    s = math.sin(angle)
    bs = float(globalSizesScales.bcSize)
    co = self.coords
    (r,g,b) = globalSettings.bcColor
    glColor3f(r,g,b)
    glBegin(GL_LINE_LOOP)
    glVertex3f(co[0],co[1],co[2])
    glVertex3f(co[0]+c*(-w)*bs-s*h*bs,co[1],co[2]+s*(-w)*bs+c*h*bs)
    glVertex3f(co[0]+c*( w)*bs-s*h*bs,co[1],co[2]+s*( w)*bs+c*h*bs)
    glEnd()
    if sliding:
        glBegin(GL_LINES)
        glVertex3f(co[0]+c*(-w)*bs-s*(h+gap)*bs,co[1],co[2]+s*(-w)*bs+c*(h+gap)*bs)
        glVertex3f(co[0]+c*( w)*bs-s*(h+gap)*bs,co[1],co[2]+s*( w)*bs+c*(h+gap)*bs)
        glEnd()
    glDefaultColor()

def drawSlidingClampedEnd(self,angle=0.0,w=0.8,h=0.35):
    """Draw sliding clamped end (fixed rotation and displacement in one direction)"""
    c = math.cos(angle)
    s = math.sin(angle)
    bs = float(globalSizesScales.bcSize)
    co = self.coords
    (r,g,b) = globalSettings.bcColor
    glColor3f(r,g,b)
    glBegin(GL_LINES)
    glVertex3f(co[0]+c*(-w*bs),co[1],co[2]+s*(-w*bs))
    glVertex3f(co[0]+c*( w*bs),co[1],co[2]+s*( w*bs))
    glVertex3f(co[0]+c*(-w*bs)-s*h*bs,co[1],co[2]+s*(-w*bs)+c*h*bs)
    glVertex3f(co[0]+c*( w*bs)-s*h*bs,co[1],co[2]+s*( w*bs)+c*h*bs)
    # hatching
    glVertex3f(co[0]+c*(      -w*bs)-s*2*h*bs,co[1],co[2]+s*(      -w*bs)+c*2*h*bs)
    glVertex3f(co[0]+c*(  (-w+h)*bs)-s*h*bs  ,co[1],co[2]+s*(  (-w+h)*bs)+c*h*bs  )
    glVertex3f(co[0]+c*(  (-w+h)*bs)-s*2*h*bs,co[1],co[2]+s*(  (-w+h)*bs)+c*2*h*bs)
    glVertex3f(co[0]+c*((-w+2*h)*bs)-s*h*bs  ,co[1],co[2]+s*((-w+2*h)*bs)+c*h*bs  )
    glVertex3f(co[0]+c*((-w+2*h)*bs)-s*2*h*bs,co[1],co[2]+s*((-w+2*h)*bs)+c*2*h*bs)
    glVertex3f(co[0]+c*((-w+3*h)*bs)-s*h*bs  ,co[1],co[2]+s*((-w+3*h)*bs)+c*h*bs  )
    glVertex3f(co[0]+c*((-w+3*h)*bs)-s*2*h*bs,co[1],co[2]+s*((-w+3*h)*bs)+c*2*h*bs)
    glVertex3f(co[0]+c*((-w+4*h)*bs)-s*h*bs  ,co[1],co[2]+s*((-w+4*h)*bs)+c*h*bs  )
    glEnd()
    # circles ('wheels')
    glCircle(co[0]+c*(-0.66*w)*bs-s*0.5*h*bs,co[1],co[2]+s*(-0.66*w)*bs+c*0.5*h*bs,r=0.45*h*bs)
    glCircle(co[0]+             -s*0.5*h*bs,co[1],co[2]+             +c*0.5*h*bs,r=0.45*h*bs)
    glCircle(co[0]+c*( 0.66*w)*bs-s*0.5*h*bs,co[1],co[2]+s*( 0.66*w)*bs+c*0.5*h*bs,r=0.45*h*bs)
    glDefaultColor()

def drawFixedRotation(self,w=0.35,h=0.35):
    """Draw fixed rotation (only rotation is fixed)"""
    bs = float(globalSizesScales.bcSize)
    co = self.coords
    (r,g,b) = globalSettings.bcColor
    glColor3f(r,g,b)
    glBegin(GL_LINES)
    glVertex3f(co[0]-w*bs,co[1],co[2]-h*bs)
    glVertex3f(co[0]+w*bs,co[1],co[2]-h*bs)
    glVertex3f(co[0]+w*bs,co[1],co[2]-h*bs)
    glVertex3f(co[0]+w*bs,co[1],co[2]+h*bs)
    glVertex3f(co[0]+w*bs,co[1],co[2]+h*bs)
    glVertex3f(co[0]-w*bs,co[1],co[2]+h*bs)
    glVertex3f(co[0]-w*bs,co[1],co[2]+h*bs)
    glVertex3f(co[0]-w*bs,co[1],co[2]-h*bs)
    glEnd()
    glDefaultColor()


def isInside (self, bbox):
   return bbox.isInside(self.coords)

Node.OnDraw = OnDraw
Node.OnDrawResults = OnDrawResults
Node.drawClampedEnd = drawClampedEnd
Node.drawHinge = drawHinge
Node.drawSlidingClampedEnd = drawSlidingClampedEnd
Node.drawFixedRotation = drawFixedRotation
Node.isInside = isInside

##################################################################
# Beam2d
##################################################################
def OnDraw (self):
    """Draw element geometry and label"""
    (r,g,b) = globalSettings.elemColor
    glLineWidth(float(globalSettings.elemthick)*float(globalSizesScales.lineWidthCoeff))
    glColor3f(r,g,b)
    c1 = self.nodes[0].coords
    c2 = self.nodes[1].coords
    glBegin(GL_LINES)
    glVertex3f (c1[0], c1[1], c1[2])
    glVertex3f (c2[0], c2[1], c2[2])
    glEnd()
    glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
    if globalFlags.labelDisplayFlag:
        glPrintString (
            0.5*(c1[0]+c2[0]),
            0.5*(c1[1]+c2[1]),
            0.5*(c1[2]+c2[2]),
            self.label)
    if self.hasHinges():
        h = 0.3*float(globalSizesScales.bcSize)
        dx = c2[0] - c1[0]
        dz = c2[2] - c1[2]
        l = math.sqrt(dx*dx+dz*dz)
        c = dx/l
        s = dz/l
        if self.hinges[0]:
            glCircle(c1[0]+h*c, c1[1], c1[2]+h*s,h)
        if self.hinges[1]:
            glCircle(c2[0]-h*c, c2[1], c2[2]-h*s,h)
    glDefaultColor()

def OnDrawResults(self, rr, nseg=20):
    """Draw element deformed shape and internal forces N, V, M"""
    if not isBeamResultFlag():
        return
    if not self.domain.session.solver.isSolved:
        raise EduBeamError
    c1 = self.nodes[0].coords
    c2 = self.nodes[1].coords
    l,dx,dz = self.computeGeom()
    c = dx/l
    s = dz/l
    glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
    if globalFlags.deformationDisplayFlag:
        (r,g,b) = globalSettings.defgeoColor
        glColor3f(r,g,b)
        rl = self.computeEndDspl(rr)
        u,w = self.computeDefl(rl=rl, fzloc=None, geom=(l,dx,dz))
        glBegin(GL_LINE_STRIP )
        for i in xrange(nseg+1):
            xl = float(i)/float(nseg)
            xc = (1.-xl)*c1[0]+xl*c2[0]+(c*u[i]-s*w[i])*float(globalSizesScales.deformationScale)
            zc = (1.-xl)*c1[2]+xl*c2[2]+(s*u[i]+c*w[i])*float(globalSizesScales.deformationScale)
            glVertex3f (xc, 0.0, zc)
        glEnd()
        if globalFlags.valuesDisplayFlag:
            minw = min(w)
            posmin = w.index(minw)
            maxw = max(w)
            posmax = w.index(maxw)
            if posmin!=0 and posmin!=nseg:
               posmin *= l/float(nseg)
               glPrintString(c1[0]+c*posmin-s*minw*float(globalSizesScales.deformationScale), c1[1], c1[2]+s*posmin+c*minw*float(globalSizesScales.deformationScale),'{0:.2e}'.format(abs(minw)))
            if posmax!=0 and posmax!=nseg:
               posmax *= l/float(nseg)
               glPrintString(c1[0]+c*posmax-s*maxw*float(globalSizesScales.deformationScale), c1[1], c1[2]+s*posmax+c*maxw*float(globalSizesScales.deformationScale),'{0:.2e}'.format(abs(maxw)))
        glDefaultColor()
    #
    if not (globalFlags.intForcesDisplayFlag[0] or globalFlags.intForcesDisplayFlag[1] or globalFlags.intForcesDisplayFlag[2]):
        return
    #
    F = self.computeEndForces(rr)
    #
    if globalFlags.intForcesDisplayFlag[0]: # N force
        (r,g,b) = globalSettings.nForceColor
        glColor3f(r,g,b)
        glBegin(GL_LINE_STRIP )
        glVertex3f (c1[0], c1[1], c1[2])
        distances,N,labelMask = self.computeNormalForce(F=F)
        for i in xrange(0,len(distances)):
            xl = distances[i]
            glVertex3f (
                c1[0]+c*xl+s*N[i]*float(globalSizesScales.intForceScale),
                c1[1],
                c1[2]+s*xl-c*N[i]*float(globalSizesScales.intForceScale))
        #glVertex3f (c1[0]-s*F[0]*float(globalSizesScales.intForceScale), c1[1], c1[2]+c*F[0]*float(globalSizesScales.intForceScale))
        #glVertex3f (c2[0]+s*F[3]*float(globalSizesScales.intForceScale), c2[1], c2[2]-c*F[3]*float(globalSizesScales.intForceScale))
        glVertex3f (c2[0], c2[1], c2[2])
        glEnd()
        if globalFlags.valuesDisplayFlag:
            for i in xrange(0,len(labelMask)):
                if labelMask[i]:
                    xl = distances[i]
                    glPrintString (c1[0]+c*xl+s*N[i]*float(globalSizesScales.intForceScale), c1[1], c1[2]+s*xl-c*N[i]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(posZero(N[i])))
        
            #glPrintString (c1[0]-s*F[0]*float(globalSizesScales.intForceScale), c1[1], c1[2]+c*F[0]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(-F[0]))
            #glPrintString (c2[0]+s*F[3]*float(globalSizesScales.intForceScale), c2[1], c2[2]-c*F[3]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(F[3]))
    if globalFlags.intForcesDisplayFlag[1]: # V force
        (r,g,b) = globalSettings.vForceColor
        glColor3f(r,g,b)
        glBegin(GL_LINE_STRIP )
        glVertex3f (c1[0], c1[1], c1[2])
        distances,V,labelMask = self.computeShearForce(F=F)
        for i in xrange(0,len(distances)):
            xl = distances[i]
            glVertex3f (
                c1[0]+c*xl+s*V[i]*float(globalSizesScales.intForceScale),
                c1[1],
                c1[2]+s*xl-c*V[i]*float(globalSizesScales.intForceScale))
        glVertex3f (c2[0], c2[1], c2[2])
        glEnd()
        
        
        #glVertex3f (c1[0]-s*F[1]*float(globalSizesScales.intForceScale), c1[1], c1[2]+c*F[1]*float(globalSizesScales.intForceScale))
        #glVertex3f (c2[0]+s*F[4]*float(globalSizesScales.intForceScale), c2[1], c2[2]-c*F[4]*float(globalSizesScales.intForceScale))
        #glVertex3f (c2[0], c2[1], c2[2])
        #glEnd()
        if globalFlags.valuesDisplayFlag:
            for i in xrange(0,len(labelMask)):
                if labelMask[i]:
                    xl = distances[i]
                    glPrintString (c1[0]+c*xl+s*V[i]*float(globalSizesScales.intForceScale), c1[1], c1[2]+s*xl-c*V[i]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(posZero(V[i])))
            
            #glPrintString (c1[0]-s*F[1]*float(globalSizesScales.intForceScale), c1[1], c1[2]+c*F[1]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(-F[1]))
            #glPrintString (c2[0]+s*F[4]*float(globalSizesScales.intForceScale), c2[1], c2[2]-c*F[4]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(F[4]))
    if globalFlags.intForcesDisplayFlag[2]: # M function
        (r,g,b) = globalSettings.mForceColor
        glColor3f(r,g,b)
        glBegin(GL_LINE_STRIP )
        glVertex3f (c1[0], c1[1], c1[2])
        distances,M = self.computeMoment(F=F, fzloc=None, geom=(l,dx,dz))
        for i in xrange(0,len(distances)):
            xl = distances[i]
            glVertex3f (
                c1[0]+c*xl+s*M[i]*float(globalSizesScales.intForceScale),
                c1[1],
                c1[2]+s*xl-c*M[i]*float(globalSizesScales.intForceScale))
        glVertex3f (c2[0], c2[1], c2[2])
        glEnd()
        if globalFlags.valuesDisplayFlag:
            glPrintString (c1[0]+s*F[2]*float(globalSizesScales.intForceScale), c1[1], c1[2]-c*F[2]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(abs(F[2])))
            glPrintString (c2[0]-s*F[5]*float(globalSizesScales.intForceScale), c2[1], c2[2]+c*F[5]*float(globalSizesScales.intForceScale),'{0:.2f}'.format(abs(F[5])))
            minM = min(M)
            posmin = M.index(minM)
            maxM = max(M)
            posmax = M.index(maxM)
            if posmin!=0 and posmin!=len(distances)-1:
                glPrintString(c1[0]+c*distances[posmin]+s*minM*float(globalSizesScales.intForceScale), c1[1], c1[2]+s*distances[posmin]-c*minM*float(globalSizesScales.intForceScale),'{0:.2f}'.format(abs(minM)))
            if posmax!=0 and posmax!=len(distances)-1:
                glPrintString(c1[0]+c*distances[posmax]+s*maxM*float(globalSizesScales.intForceScale), c1[1], c1[2]+s*distances[posmax]-c*maxM*float(globalSizesScales.intForceScale),'{0:.2f}'.format(abs(maxM)))
            glDefaultColor()

def isInside(self, bbox):
    c1 = self.nodes[0].coords
    c2 = self.nodes[1].coords
    return bbox.isInside((0.5*(c1[0]+c2[0]), 0.5*(c1[1]+c2[1]), 0.5*(c1[2]+c2[2])))

Beam2d.OnDraw = OnDraw
Beam2d.OnDrawResults = OnDrawResults
Beam2d.isInside = isInside



##################################################################
# NodalLoad
##################################################################
def OnDraw(self, useUniformSize=True):
    (r,g,b) = globalSettings.loadColor
    glColor3f(r,g,b)
    glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
    if globalFlags.loadDisplayFlag:
        c = self.where.coords
        logger.debug( self.value )
        vx = self.value['fx']
        vz = self.value['fz']
        m = self.value['my']
        if vx!=0 or vz!=0:
            # draw force
            ratio = float(globalSizesScales.loadSize)
            if useUniformSize:
                ratio /= sqrt(vx*vx + vz*vz)
            vx *= ratio
            vz *= ratio
            glArrow(c[0],c[1],c[2],vx,vz)
            if globalFlags.labelDisplayFlag:
                glPrintString (c[0]-vx, c[1], c[2]-vz, '%s (%g, %g, %g)'%(self.label,abs(self.value['fx']),abs(self.value['fz']),abs(self.value['my'])))
        if m != 0:
            # draw moment
            ratio = float(globalSizesScales.loadSize)*float(globalSizesScales.momentForceRatio)
            if useUniformSize:
                ratio /= abs(m)
            m *= ratio
            glArrowMoment(c[0],c[1],c[2],0.5*m)
            if globalFlags.labelDisplayFlag:
                glPrintString (c[0]+.2*m, c[1], c[2]+.2*m, '%s (%g, %g, %g)'%(self.label,abs(self.value['fx']),abs(self.value['fz']),abs(self.value['my'])))
    glDefaultColor()

NodalLoad.OnDraw = OnDraw


##################################################################
# PrescribedDisplacement
##################################################################
def OnDraw(self, useUniformSize=True):
    (r,g,b) = globalSettings.loadColor
    glColor3f(r,g,b)
    co = self.where.coords
    glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
    if globalFlags.loadDisplayFlag:
        if self.where.bcs['x'] == True and self.value['x'] != 0.:
            size = float(globalSizesScales.pDsplSize) * (1. if useUniformSize else self.value['x'])
            glArrow(co[0],co[1],co[2],size,0.)
        if self.where.bcs['z'] == True and self.value['z'] != 0.:
            size = float(globalSizesScales.pDsplSize) * (1. if useUniformSize else self.value['z'])
            glArrow(co[0],co[1],co[2],0.,size)
        if self.where.bcs['Y'] == True and self.value['Y'] != 0.:
            size = float(globalSizesScales.pDsplSize)*float(globalSizesScales.momentForceRatio) * (1. if useUniformSize else self.value['Y'])
            glArrowMoment(co[0],co[1],co[2],size)
        if globalFlags.labelDisplayFlag:
            glPrintString(co[0], co[1], co[2], '%.2f, %.2f, %.2f' % (
                self.value['x'] if self.where.bcs['x'] else 0.,
                self.value['z'] if self.where.bcs['z'] else 0.,
                self.value['Y'] if self.where.bcs['Y'] else 0.,
            )
        )
    glDefaultColor()

PrescribedDisplacement.OnDraw = OnDraw


##################################################################
# ElementLoad
##################################################################
def OnDraw(self, useUniformSize=True):
    glLineWidth(float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
    if globalFlags.loadDisplayFlag:
        (r,g,b) = globalSettings.loadColor
        glColor3f(r,g,b)
        c1 = self.where.nodes[0].coords
        c2 = self.where.nodes[1].coords
        l,dx,dz = self.where.computeGeom()
        
        if not 'type' in self.value.keys():
            logger.error( langStr('Missing keyword \'type\' in element load on element %s', 'Chybní slovo \'type\' z zatížení na elementu') % self.where.label )
            
            
        if self.value['type']=='Uniform': #Uniform load
            vxTmp, vzTmp = self.giveFxFzElemProjection()
            
            #print c1, c2, vxTmp, vzTmp, self.value['dir']
            
            vx = vxTmp*float(globalSizesScales.loadSize)
            vz = vzTmp*float(globalSizesScales.loadSize)
            if vx !=0. or vz !=0.:
                #c1 = self.where.nodes[0].coords
                #c2 = self.where.nodes[1].coords
                ratio = float(globalSizesScales.loadSize)
                if useUniformSize:
                    ratio /= sqrt(vx*vx + vz*vz)
                vx *= ratio
                vz *= ratio
                # frame
                glBegin(GL_LINE_STRIP)
                glVertex3f(c1[0],c1[1],c1[2])
                glVertex3f(c1[0]-vx,c1[1],c1[2]-vz)
                glVertex3f(c2[0]-vx,c2[1],c2[2]-vz)
                glVertex3f(c2[0],c2[1],c2[2])
                glEnd()
                # arrows
                c = 1.0
                size = math.sqrt(vx*vx+vz*vz)
                d = c*size
                n = int(l/d)-1
                if n<2: n=2
                dx /= float(n)
                dz /= float(n)
                for i in xrange(1,n):
                    glArrow(c1[0]+i*dx,c1[1],c1[2]+i*dz,vx,vz)
            if globalFlags.labelDisplayFlag:
                c = self.where.computeCenter()
                glPrintString (c[0]-vx, c[1], c[2]-vz, '%s %g %s'%(self.label,abs(self.value['magnitude']),'X' if self.value['perX']==1 else ''))
        
        if self.value['type']=='Force': #Force
            vx = self.value['Fx']
            vz = self.value['Fz']
            distF = self.value['DistF']
            if vx!=0 or vz!=0:
                ratio = float(globalSizesScales.loadSize)
                if useUniformSize:
                    ratio /= sqrt(vx*vx + vz*vz)
                vx *= ratio
                vz *= ratio
                c = [c1[0]+dx*distF/l,c1[1],c1[2]+dz*distF/l]
                glArrow(c[0],c[1],c[2],vx,vz)
                if globalFlags.labelDisplayFlag:
                    glPrintString (c[0]-vx, c[1], c[2]-vz, '%s (%g,  %g)'%(self.label,abs(self.value['Fx']),abs(self.value['Fz'])))
        
        if self.value['type']=='Temperature': #Temperature load
            (r,g,b) = globalSettings.temperatureColor
            glColor3f(r,g,b)
            if self.value['dTc'] !=0. or self.value['dTg'] !=0.:
                cc = self.where.computeCenter()
                #draw dashed line along element
                c1 = self.where.nodes[0].coords
                c2 = self.where.nodes[1].coords
                #compute unit normal
                dx = c1[2]-c2[2]
                dz = c2[0]-c1[0]
                l = math.sqrt(dx*dx+dz*dz)
                n = (dx/l,0,dz/l)
                c = 0.1
                glEnable(GL_LINE_STIPPLE)
                glLineWidth (1.0);
                glLineStipple (1, 0x00FF);  # dashed  

                glBegin(GL_LINES)
                glVertex3f (c1[0]+n[0]*c, c1[1]+n[1]*c, c1[2]+n[2]*c)
                glVertex3f (c2[0]+n[0]*c, c2[1]+n[1]*c, c2[2]+n[2]*c)
                glEnd()
                glDisable(GL_LINE_STIPPLE)
                glLineWidth (float(globalSettings.defaultthick)*float(globalSizesScales.lineWidthCoeff))
                #
                if globalFlags.labelDisplayFlag:
                    l,dx,dz = self.where.computeGeom()
                    c = dx/l
                    s = dz/l
                   # td = self.value['dTc']+0.5*self.value['dTg']
                   # tt = self.value['dTc']-0.5*self.value['dTg']
                    coeff = 0.4
                    glPrintString (cc[0]+.4*coeff,cc[1],cc[2]-.4*coeff, '%s (%g, %g)' % (self.label,self.value['dTc'], self.value['dTg'] ))
                   # glPrintString (cc[0]-coeff*s, cc[1], cc[2]+c*coeff, 'T=%g'%(td))
                   # glPrintString (cc[0]+coeff*s, cc[1], cc[2]-c*coeff, 'T=%g'%(tt))
                else:
                    glPrintString (cc[0],cc[1],cc[2],'T')
            glDefaultColor()      

ElementLoad.OnDraw = OnDraw
##################################################################
