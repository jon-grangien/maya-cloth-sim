import sys
import maya.cmds as cmds

class clothsim():
    def hello(self):
        result = cmds.polyCube( w=10.0, h=10.0, d=10.0, name="niceCube" )
        print 'result: ' + str(result)
