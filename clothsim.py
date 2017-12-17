import sys
import pymel.core as pm
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaRender as OpenMayaRender
import maya.OpenMayaRender as V1OpenMayaRender
import maya.api.OpenMayaUI as OpenMayaUI #OpenMayaUI.M3dView.active3dView()

pluginname = "Clothsim"

def maya_useNewAPI():
    pass

# Spring class
# pos_a: first position
# pos_b: second position
# ks: spring constant
# rest length: rest length of string
class Spring():
    STIFFNESS = 1

    def __init__(self, a, b, ks, rest_length, spring_type):
        self.pos_a = a
        self.pos_b = b
        self.ks = ks
        self.rest_length = rest_length
        self.spring_type = spring_type

# Simulation class
# width: width of cloth area
# height: height of cloth area
class Clothsim():
    id = OpenMaya.MTypeId( 0x80007 )

    #cloth_area = [[5,0,0], [-5,0,0], [-1,0,0], [1,0,0]]
    #vertex_density = 0.5
    VERTEX_MASS = 5
    STRUCTURAL_SPRING_TYPE = 0
    SHEAR_SPRING_TYPE = 1
    GRAVITY_FORCE = 9.8
    VERTEX_SIZE = 4
    VERTEX_SIZE_HALF = 2
    KS_STRUCTURAL = 10
    KS_SHEAR = 13

    @staticmethod
    def creator():
        return Clothsim(300, 300)

    @staticmethod
    def initialize():
        return

    def __init__(self, w, h):
        '''clothsim __init__'''
        #OpenMayaUI.MPxLocatorNode.__init__(self)
        self.width = w
        self.height = h
        self.num_x = 10
        self.num_y = 10
        #self.total_verts = (num_x+1)*(num_y+1)
        self.sim_u = self.num_x + 1
        self.sim_v = self.num_y + 1
        
        self.vertices = []
        self.v_forces = []
        self.v_velocities = []
        self.v_indices = []
        self.springs = []

        # Initialized with Hardware renderer
        self.gl_renderer = V1OpenMayaRender.MHardwareRenderer.theRenderer()

        # Hold reference to OpenGl fucntion table used by maya
        self.gl_ft = self.gl_renderer.glFunctionTable()

    def add_spring(self, a, b, ks, spring_type):
        s = Spring(a, b, ks, a - b, spring_type)
        self.springs.append(s)

    def setup(self):

        # Calculate initial vertices
        for i in range(0, self.sim_u):
            for j in range(0, self.sim_v):
                self.vertices.append([((i/(self.sim_u - 1)) * 2 - 1) * self.VERTEX_SIZE_HALF, self.VERTEX_SIZE + 1, ((j/(self.sim_v - 1)) * self.VERTEX_SIZE), ''])
                self.v_forces.append([0, 0, 0])
                self.v_velocities.append([0, 0, 0])

        for i in self.vertices:
            print(self.vertices[i])

        # Fill in triangle indices
        for i in range(0, self.num_y):
            for j in range(0, self.num_x):
                i_0 = i * (self.num_x + 1) + j
                i_1 = i_0 + 1
                i_2 = i_0 + (self.num_x + 1)
                i_3 = i_2 + 1

                if (j+i) % 2:
                    self.v_indices.append(i_0)
                    self.v_indices.append(i_2)
                    self.v_indices.append(i_1)

                    self.v_indices.append(i_1)
                    self.v_indices.append(i_2)
                    self.v_indices.append(i_3)
                else:
                    self.v_indices.append(i_0)
                    self.v_indices.append(i_2)
                    self.v_indices.append(i_3)

                    self.v_indices.append(i_0)
                    self.v_indices.append(i_3)
                    self.v_indices.append(i_1)


        # Add structural springs
        # Horizontal
        for i in range(0, self.sim_v):
            for j in range(0, self.sim_u - 1):
                self.add_spring((i * self.sim_u) + j, (i * self.sim_u) + j + 1, self.KS_STRUCTURAL, self.STRUCTURAL_SPRING_TYPE)

        # Vertical
        for i in range(0, self.sim_u):
            for j in range(0, self.sim_v - 1):
                self.add_spring((j * self.sim_u) + i, ((j + 1) * self.sim_u) + i, self.KS_STRUCTURAL, self.STRUCTURAL_SPRING_TYPE)

        # Add shear springs
        for i in range(0, self.sim_v - 1):
            for j in range(0, self.sim_u - 1):
                self.add_spring( (i * self.sim_u) + j, ((i + 1) * self.sim_u) + j + 1, self.KS_SHEAR, self.SHEAR_SPRING_TYPE)
                self.add_spring( ((i + 1) * self.sim_u) + j, (i * self.sim_u) + j + 1, self.KS_SHEAR, self.SHEAR_SPRING_TYPE)

        # Add spheres at initial vertex positions, put reference name in last field
        for i in range(0, len(self.v_indices), 3):
            p_1 = self.vertices[self.v_indices[i]]
            p_2 = self.vertices[self.v_indices[i+1]]
            p_3 = self.vertices[self.v_indices[i+2]] 

            sphere = pm.polySphere(sx=10, sy=15, r=0.1)
            pm.move(p_1[0], p_1[1], p_1[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i]][3] = sphere[0]

            sphere = pm.polySphere(sx=10, sy=15, r=0.1)
            pm.move(p_2[0], p_2[1], p_2[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i+1]][3] = sphere[0]

            sphere = pm.polySphere(sx=10, sy=15, r=0.1)
            pm.move(p_3[0], p_3[1], p_3[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i+2]][3] = sphere[0]

    def drawGL(self):
        view = OpenMayaUI.M3dView.active3dView()
        view.drawText( 'Hej', OpenMaya.MPoint(0, 0, -1), OpenMayaUI.M3dView.kCenter ) 
        view.beginGL()
        self.gl_ft.glPushAttrib( V1OpenMayaRender.MGL_CURRENT_BIT )
        self.gl_ft.glDisable( V1OpenMayaRender.MGL_CULL_FACE )
        self.gl_ft.glColor3f(1, 1, 1)
        self.gl_ft.glBegin(V1OpenMayaRender.MGL_TRIANGLE_FAN)

        for i in range(0, len(self.v_indices), 3):
            p_1 = self.vertices[self.v_indices[i]]
            p_2 = self.vertices[self.v_indices[i+1]]
            p_3 = self.vertices[self.v_indices[i+2]] #index out of range
            self.gl_ft.glVertex3f(p_1[0], p_1[1], p_1[2])
            self.gl_ft.glVertex3f(p_2[0], p_2[1], p_2[2])
            self.gl_ft.glVertex3f(p_3[0], p_3[1], p_3[2])

        self.gl_ft.glEnd()

        self.gl_ft.glPopAttrib()
        view.endGL()
        view.drawText( "Hello", OpenMaya.MPoint( 0.0, 0.0, 0.0 ), OpenMayaUI.M3dView.kCenter )

    def draw(self):
        #plane = pm.polyPlane()
        #print(plane)
        #iterations = 20

        #for i in range(iterations):
        #    pm.setKeyframe(insert=True, value=i)

    #def run(self)
        # animation step        

# Run sim
#inputGeoTrans = pm.polyPlane(sx=10, sy=10, w=10, h=10, ch = False)[0]
#inputGeoShape = inputGeoTrans.getShape()
#pm.select(cl = True)
#
#outputGeoTrans = pm.polyPlane( sx=10, sy=10, w=10, h=10, ch = False)[0]
#outputGeoShape = outputGeoTrans.getShape()
#pm.select(cl = True)
#
## Position constraint locators
#positionConstraintLocatorIndex0Trans = pm.spaceLocator(n = 'positionConstraintLocatorIndex0')
#positionConstraintLocatorIndex0Shape = positionConstraintLocatorIndex0Trans.getShape()
#positionConstraintLocatorIndex0Trans.translate.set(-5,5,5)
#pm.select(cl = True)
#
#positionConstraintLocatorIndex110Trans = pm.spaceLocator(n = 'positionConstraintLocatorIndex110')
#positionConstraintLocatorIndex110Shape = positionConstraintLocatorIndex110Trans.getShape()
#positionConstraintLocatorIndex110Trans.translate.set(-5,5,-5)
#pm.select(cl = True)
#
#positionConstraintLocatorIndex120Trans = pm.spaceLocator(n = 'positionConstraintLocatorIndex120')
#positionConstraintLocatorIndex120Shape = positionConstraintLocatorIndex120Trans.getShape()
#positionConstraintLocatorIndex120Trans.translate.set(5,5,-5)
#pm.select(cl = True)
#
#positionConstraintLocatorIndex10Trans = pm.spaceLocator(n = 'positionConstraintLocatorIndex10')
#positionConstraintLocatorIndex10Shape = positionConstraintLocatorIndex10Trans.getShape()
#positionConstraintLocatorIndex10Trans.translate.set(5,5,5)
#pm.select(cl = True)
#
#positionConstraintLocatorIndex60Trans = pm.spaceLocator(n = 'positionConstraintLocatorIndex60')
#positionConstraintLocatorIndex60Shape = positionConstraintLocatorIndex60Trans.getShape()
#positionConstraintLocatorIndex60Trans.translate.set(0,5,0)
#pm.select(cl = True)
#
## Collision sphere
#collisionSphereTrans = pm.polySphere(sx = 8,sy = 8, n = 'collisionSphere0', r = 2, ch = 0)[0]
#collisionSphereShape = collisionSphereTrans.getShape()
#collisionSphereTrans.translate.set(0,1,0)
#pm.select(cl = True)

sim = Clothsim(300, 300)
sim.setup()
sim.draw()
