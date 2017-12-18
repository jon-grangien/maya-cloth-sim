import sys, math
import pymel.core as pm
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaRender as OpenMayaRender
import maya.OpenMayaRender as V1OpenMayaRender
import maya.api.OpenMayaUI as OpenMayaUI #OpenMayaUI.M3dView.active3dView()

plugin_name = "Clothsim"

SET_KEY_STEP = 4 

def maya_useNewAPI():
    pass

# Spring class
# pos_a: first position
# pos_b: second position
# ks: spring constant
# rest length: rest length of string
class Spring():
    STIFFNESS = 1

    def __init__(self, a, b, ks, kd, rest_length, spring_type):
        self.pos_a = a
        self.pos_b = b
        self.ks = ks
        self.kd = kd
        self.rest_length = rest_length
        self.spring_type = spring_type

# Simulation class
# width: width of cloth area
# height: height of cloth area
class Clothsim():
    id = OpenMaya.MTypeId( 0x80007 )

    #cloth_area = [[5,0,0], [-5,0,0], [-1,0,0], [1,0,0]]
    #vertex_density = 0.5
    VERTEX_MASS = 30.0
    STRUCTURAL_SPRING_TYPE = 0
    SHEAR_SPRING_TYPE = 1
    BEND_SPRING_TYPE = 2

    GRAVITY_FORCE = [0.0, -0.0098, 0.0]
    VERTEX_SIZE = 4
    VERTEX_SIZE_HALF = 2.0

    KS_STRUCTURAL = 50.75
    KD_STRUCTURAL = -0.25
    KS_SHEAR = 50.75
    KD_SHEAR = -0.25
    KS_BEND = 50.95
    KD_BEND = -0.25

    DEFAULT_DAMPING = -0.0125
    TIME_STEP = 1.0 / 24.0
    FPS = 24.0

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
        self.num_x = 20
        self.num_y = 20
        self.total_verts = (self.num_x+1)*(self.num_y+1)
        self.sim_u = self.num_y + 1
        self.sim_v = self.num_x + 1
        
        self.vertices = []
        self.vertices_last = []
        self.v_forces = []
        self.v_velocities = []
        self.v_indices = []
        self.springs = []

        # Initialized with Hardware renderer
        self.gl_renderer = V1OpenMayaRender.MHardwareRenderer.theRenderer()

        # Hold reference to OpenGl fucntion table used by maya
        self.gl_ft = self.gl_renderer.glFunctionTable()

    def add_spring(self, a, b, ks, kd, spring_type):
        s = Spring(a, b, ks, kd, a - b, spring_type)
        self.springs.append(s)

    def setup(self):

        for i in range(0, self.total_verts):
            self.vertices.append([0,0,0,''])
            self.vertices_last.append([0,0,0,''])
            self.v_forces.append([0,0,0])
            self.vertices.append([0,0,0])

        # Calculate initial vertices
        counter = 0
        for i in range(0, self.sim_u):
            for j in range(0, self.sim_v):
                self.vertices[counter] = [((float(i)/(float(self.sim_u) - 1.0)) * 2.0 - 1.0) * self.VERTEX_SIZE_HALF, self.VERTEX_SIZE + 1, ((float(j)/(float(self.sim_v) - 1.0)) * self.VERTEX_SIZE), '']
                self.vertices_last[counter] = self.vertices[counter]
                counter = counter + 1

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
                self.add_spring((i * self.sim_u) + j, (i * self.sim_u) + j + 1, self.KS_STRUCTURAL, self.KD_STRUCTURAL, self.STRUCTURAL_SPRING_TYPE)

        # Vertical
        for i in range(0, self.sim_u):
            for j in range(0, self.sim_v - 1):
                self.add_spring((j * self.sim_u) + i, ((j + 1) * self.sim_u) + i, self.KS_STRUCTURAL, self.KD_STRUCTURAL, self.STRUCTURAL_SPRING_TYPE)

        # Add shear springs
        for i in range(0, self.sim_v - 1):
            for j in range(0, self.sim_u - 1):
                self.add_spring( (i * self.sim_u) + j, ((i + 1) * self.sim_u) + j + 1, self.KS_SHEAR, self.KD_SHEAR, self.SHEAR_SPRING_TYPE)
                self.add_spring( ((i + 1) * self.sim_u) + j, (i * self.sim_u) + j + 1, self.KS_SHEAR, self.KD_SHEAR, self.SHEAR_SPRING_TYPE)

        # Add bend strings
        for i in range(0, self.sim_v ):
            for j in range(0, self.sim_u - 2):
                self.add_spring((i * self.sim_u) + j, (i * self.sim_u) + j + 2, self.KS_BEND, self.KD_BEND, self.BEND_SPRING_TYPE)
            self.add_spring((i * self.sim_u) + (self.sim_u - 3), (i * self.sim_u) + (self.sim_u - 1), self.KS_BEND, self.KD_BEND, self.BEND_SPRING_TYPE)
                
        for i in range(0, self.sim_u):
            for j in range(0, self.sim_v - 2):
                self.add_spring((j * self.sim_u) + i, ((j + 2) * self.sim_u) + i, self.KS_BEND, self.KD_BEND, self.BEND_SPRING_TYPE)
            self.add_spring(((self.sim_v - 3) * self.sim_u) + i, ((self.sim_v - 1) * self.sim_u) + i, self.KS_BEND, self.KD_BEND, self.BEND_SPRING_TYPE)


        # Add spheres at initial vertex positions, put reference name in last field
        for i in range(0, len(self.v_indices), 3):
            p_1 = self.vertices[self.v_indices[i]]
            p_2 = self.vertices[self.v_indices[i+1]]
            p_3 = self.vertices[self.v_indices[i+2]] 

            sphere = pm.polySphere(sx=4, sy=4, r=0.1)
            pm.move(p_1[0], p_1[1], p_1[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i]][3] = sphere[0]

            sphere = pm.polySphere(sx=4, sy=4, r=0.1)
            pm.move(p_2[0], p_2[1], p_2[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i+1]][3] = sphere[0]

            sphere = pm.polySphere(sx=4, sy=4, r=0.1)
            pm.move(p_3[0], p_3[1], p_3[2], sphere[0], ws=True)
            self.vertices[self.v_indices[i+2]][3] = sphere[0]

    
    def IntegrateVerlet(self, dt):
        dt_2_mass = float(dt * dt) / float(self.VERTEX_MASS)

        for i in range(0, self.total_verts):
            buffer = self.vertices[i][:]
            force = [0.0, 0.0, 0.0]
            force[0] = dt_2_mass * self.v_forces[i][0]
            force[1] = dt_2_mass * self.v_forces[i][1]
            force[2] = dt_2_mass * self.v_forces[i][2]

            diff_x = self.vertices[i][0] - self.vertices_last[i][0]
            diff_y = self.vertices[i][1] - self.vertices_last[i][1]
            diff_z = self.vertices[i][2] - self.vertices_last[i][2]

            self.vertices[i][0] = self.vertices[i][0] + diff_x + force[0]
            self.vertices[i][1] = self.vertices[i][1] + diff_y + force[1]
            self.vertices[i][2] = self.vertices[i][2] + diff_z + force[2]

            #print("diff")
            #print(str(diff_x) + " " + str(diff_y) + " " + str(diff_z))            
            #print("force")
            #print("%.32f" % force[1])

            self.vertices_last[i] = buffer
 
        if self.vertices[i][1] < 0.0:
            self.vertices[i][1] = 0

    def GetVertletVelocity(self, v_i, v_i_last, dt):
        diff_x = (v_i[0] - v_i_last[0]) / float(dt)
        diff_y = (v_i[1] - v_i_last[1]) / float(dt)
        diff_z = (v_i[2] - v_i_last[2]) / float(dt)

        return [diff_x, diff_y, diff_z]

    def ComputeForces(self, dt):
        for i in range(0, self.total_verts):
            self.v_forces[i] = [0, 0, 0]
            vel = self.GetVertletVelocity(self.vertices[i], self.vertices_last[i], dt)

            if i != 0 and i != self.num_x:
                self.v_forces[i][1] = 1000.0 * self.GRAVITY_FORCE[1] * float(self.VERTEX_MASS) #y

            self.v_forces[i][0] += self.DEFAULT_DAMPING * vel[0]
            self.v_forces[i][1] += self.DEFAULT_DAMPING * vel[1]
            self.v_forces[i][2] += self.DEFAULT_DAMPING * vel[2]

            #print("compute")
            #print("%.32f" % self.v_forces[i][1])
            #print("%.32f" % self.GRAVITY_FORCE[1])

        for i in range(0, len(self.springs)):
            p_1 = self.vertices[self.springs[i].pos_a][:]
            p_1_last = self.vertices_last[self.springs[i].pos_a][:]
            p_2 = self.vertices[self.springs[i].pos_b][:]
            p_2_last = self.vertices_last[self.springs[i].pos_b][:]

            v_1 = self.GetVertletVelocity(p_1, p_1_last, dt)
            v_2 = self.GetVertletVelocity(p_2, p_2_last, dt)

            delta_p = [0, 0, 0] # p1 - p2
            delta_p[0] = p_1[0] - p_2[0]
            delta_p[1] = p_1[1] - p_2[1]
            delta_p[2] = p_1[2] - p_2[2]

            delta_v = [0, 0, 0] # v1 - v2
            delta_v[0] = v_1[0] - v_2[0]
            delta_v[1] = v_1[1] - v_2[1]
            delta_v[2] = v_1[2] - v_2[2]

            dist = math.sqrt(delta_p[0] * delta_p[0] + delta_p[1] * delta_p[1] + delta_p[2] * delta_p[2])
            #print("compute forces dist = " + str(dist))
            left_term = -self.springs[i].ks * (dist - self.springs[i].rest_length)
            right_term = self.springs[i].kd * ((delta_p[0] * delta_v[0] + delta_p[1] * delta_v[1] + delta_p[2] * delta_v[2]) / dist)
            spring_force = [0.0, 0.0, 0.0]
            spring_force[0] = (left_term + right_term) * (delta_p[0]/dist)
            spring_force[1] = (left_term + right_term) * (delta_p[1]/dist)
            spring_force[2] = (left_term + right_term) * (delta_p[2]/dist)

            if self.springs[i].pos_a != 0 and self.springs[i].pos_a != self.num_x:
                self.v_forces[self.springs[i].pos_a][0] += spring_force[0]
                self.v_forces[self.springs[i].pos_a][1] += spring_force[1]
                self.v_forces[self.springs[i].pos_a][2] += spring_force[2]

            if self.springs[i].pos_b != 0 and self.springs[i].pos_b != self.num_x:
                self.v_forces[self.springs[i].pos_b][0] -= spring_force[0]
                self.v_forces[self.springs[i].pos_b][1] -= spring_force[1]
                self.v_forces[self.springs[i].pos_b][2] -= spring_force[2]
            
            #print("compute end")
            #print("%.32f" % self.v_forces[i][1])

    def UpdatePlaceholderSpheres(self):
        for i in range(0, len(self.v_indices), 3):
            p_1 = self.vertices[self.v_indices[i]][:]
            p_2 = self.vertices[self.v_indices[i+1]][:]
            p_3 = self.vertices[self.v_indices[i+2]][:]

            if p_1[1] < 0.0:
                p_1[1] = 1
            if p_2[1] < 0.0:
                p_2[1] = 1
            if p_3[1] < 0.0:
                p_2[1] = 1

            pm.move(p_1[0], p_1[1], p_1[2], p_1[3], ws=True)
            pm.move(p_2[0], p_2[1], p_2[2], p_2[3], ws=True)
            pm.move(p_3[0], p_3[1], p_3[2], p_3[3], ws=True)

    def PhysicsStep(self, dt):
        #print("Physics step dt = " + str(dt))
        self.ComputeForces(dt)
        self.IntegrateVerlet(dt)
        self.UpdatePlaceholderSpheres()

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
        iterations = 40

        for i in range(iterations):
            #print(self.TIME_STEP)
            
            cmds.currentTime(i, edit=True)
            self.PhysicsStep(self.TIME_STEP)
            #pm.setKeyframe(insert=True, value=i)

#            objs = pm.ls(regex='pSphere\d+', visible=True, r=True)
#            for obj in objs:
#                print(obj)
#                cmds.setKeyframe(obj, time=i, attribute='translateX')
#                pm.keyframe(at='tx', query=True, index=i, valueChange=True
#                cmds.setKeyframe(obj, time=i, attribute='translateY')
#                cmds.setKeyframe(obj, time=i, attribute='translateZ')

    #def run(self)
        # animation step        

pm.ls(regex='pSphere\d+', visible=True, r=True)
pm.delete()

sim = Clothsim(300, 300)
sim.setup()
sim.draw()

NODES_LIST = pm.ls(regex='pSphere\d+', visible=True, r=True)
ATTRS_LIST = ("tx", "ty", "tz") 
playbackStartTime  = 1
playbackEndTime    = 30
TIMES_LIST = [i for i in range(playbackStartTime, playbackEndTime+1, SET_KEY_STEP)] #Creates the list 1,5,9,13,17,21...

pm.setKeyframe( NODES_LIST, attribute=ATTRS_LIST, time=TIMES_LIST) #Set all the keys at the same time

pm.playbackOptions(ast=playbackStartTime, aet=playbackEndTime, max=playbackEndTime, min=playbackStartTime)
