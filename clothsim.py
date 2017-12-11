# import sys
import pymel.core as pm

# Spring class
# pos_a: first position
# pos_b: second position
# ks: spring constant
# rest length: rest length of string
class spring():
    STIFFNESS = 1

    def __init__(self,a,b,ks,rest_length,spring_type)
        self.pos_a = a
        self.pos_b = b
        self.ks = ks
        self.rest_length = rest_length
        self.spring_type = spring_type

# Simulation class
class clothsim():
    #cloth_area = [[5,0,0], [-5,0,0], [-1,0,0], [1,0,0]]
    #vertex_density = 0.5
    VERTEX_MASS = 5
    STRUCTURAL_SPRING_TYPE = 0
    SHEAR_SPRING_TYPE = 1
    GRAVITY_FORCE = 9.8

    def __init__(self,w,h):
        self.width = w
        self.height = h
        self.num_x = 10
        self.num_y = 10
        #self.total_verts = (num_x+1)*(num_y+1)
        self.sim_u = num_x+1
        self.sim_v = num_y+1

    def add_spring(self, a, b, ks, spring_type)
        s = spring(a,b,ks,a-b,spring_type)
        self.springs.append(s)

    def setup(self)
        # calculate initial vertices
        # add structural springs
        # add shear springs

    #def run(self)
        # animation step        
