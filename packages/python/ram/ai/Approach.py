import math as m
import ram.ai.state as state
import ram.motion as motion
import ext.core as core
import ext.vision as vision
import ext.math as math
import ram.ai.Utility as util
from ram.motion.basic import Frame

DONE = core.declareEventType('DONE')

#general visual servoing motion class
class VSMotion(state.State):

    def xFunc(self, event):
        return 0

    def yFunc(self,event):
        return 0
    
    def zFunc(self,event):
        return 0

    def moveX(self,dirct,event):
        pass

    def moveY(self,dirct,event):
        pass

    def moveZ(self,dirct,event):
        pass

    def runMotion(self,event=0):
        pass

    def decideX(self,event):
        return 0

    def decideY(self,event):
        return 0

    def decideZ(self,event):
        return 0

    def stop(self):
        pass
    
    def end_cond(self,event):
        return True

    def run(self,event):
        if(self.end_cond(event) == True):
            self.stop()
            self.publish(DONE,core.Event())
        else:            
            self.moveX(self.decideX(event),event)
            self.moveY(self.decideY(event),event)
            self.moveZ(self.decideZ(event),event)
            self.runMotion(event)
    
class VSDirect2Control(VSMotion):

    
    def runMotion(self,event):
        d = self.motionManager._estimator.getEstimatedDepth()
        pos = self.motionManager._estimator.getEstimatedPosition()
        if(self.decideZ(event) != 0):
            self.motionManager._controller.changeDepth(self._zDisp+d)
        #print pos
        self.motionManager._controller.translate(math.Vector2(self._yDisp+pos.x,self._xDisp+pos.y))
        
        
class VSDirect2ControlConst(VSDirect2Control):
    @staticmethod
 
    
    def xFunc(self,event):
        return self._cX
    def yFunc(self,event):
        return self._cY
    def zFunc(self,event):
        return self._cZ

class ForwardXYCenter(VSDirect2ControlConst):
    @staticmethod
    def getattr():
        return { 'fDisp' : .01 ,  'sDisp' : .02 ,
                 'xmin' : -0.05 , 'xmax' : 0.05,
                 'rmin' : 0.4 , 'rmax' : 0.5, 
                 'xDisp' : 0, 'yDisp' : 0, 'zDisp' : 0, } 


    def decideX(self,event):
        if(event.x<self._xmin):
            return -1#go the other way
        else:
            if(event.x>self._xmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0
    def decideY(self,event):
        if(event.range<self._rmin):
            return -1#go the other way
        else:
            if(event.range>self._rmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0
    def xFunc(self,event):
        return self._sDisp

    def yFunc(self,event):
        return self._fDisp

    def moveX(self,dirct,event):
        self._xDisp = dirct*self.xFunc(event)

    def moveY(self,dirct,event):
        self._yDisp = dirct*self.yFunc(event)

    def DONE(self,event):
        util.freeze(self)
    





#import ram.ai.Approach as a
class genApproach(ForwardXYCenter):
    def enter(self):
        pass

    def BUOY_FOUND(self,event):
        self.run(event)

    @staticmethod
    def getattr():
        return { 'fDisp' : .1 ,  'sDisp' : .2 ,
                 'xmin' : -0.035 , 'xmax' : 0.035,
                 'rmin' : 4 , 'rmax' : 4.25,  } 

    @staticmethod
    def transitions():
        return {DONE : state.State, vision.EventType.BUOY_FOUND : genApproach}    

    def end_cond(self,event):
        return ((self.decideY(event) == 0) and (self.decideX(event) == 0) )

    def DONE(self,event):
        util.freeze(self)
                                                



class XZCenter(VSDirect2ControlConst):
    @staticmethod
    def getattr():
        return { 'fDisp' : .1 ,  'sDisp' : .2 ,
                 'xmin' : -0.05 , 'xmax' : 0.05, 
                 'zmin' : -0.05 , 'zmax' : 0.05, 
                 'xDisp' : 0, 'yDisp' : 0, 'zDisp' : 0, } 

    def decideX(self,event):
        if(event.x<self._xmin):
            return -1#go the other way
        else:
            if(event.x>self._xmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0
    def decideZ(self,event):
        if(event.y<self._zmin):
            return 1#go the other way
        else:
            if(event.y>self._zmax):
                return -1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def xFunc(self,event):
        return self._sDisp

    def zFunc(self,event):
        return self._fDisp

    def moveX(self,dirct,event):
        self._xDisp = dirct*self.xFunc(event)

    def moveZ(self,dirct,event):
        self._zDisp = dirct*self.zFunc(event)
    
    def DONE(self,event):
        util.freeze(self)

#A 3DOF approach
class SuperApproach(VSDirect2ControlConst):

    @staticmethod
    def getattr():
        return { 'dy' : .1 ,  'dx' : .1 , 'dz' : .1,
                 'xmin' : -0.05 , 'xmax' : 0.05, 
                 'zmin' : -0.05 , 'zmax' : 0.05, 
                 'rmin' : 1.5 , 'rmax' : 1.75, 
                 'xDisp' : 0, 'yDisp' : 0, 'zDisp' : 0, } 
    
    def xFunc(self,event):
        return self._dx

    def yFunc(self,event):
        return self._dy

    def zFunc(self,event):
        return self._dz

    def moveX(self,dirct,event):
        self._xDisp = dirct*self.xFunc(event)

    def moveY(self,dirct,event):
        self._yDisp = dirct*self.yFunc(event)

    def moveZ(self,dirct,event):
        self._zDisp = dirct*self.zFunc(event)

    def decideX(self,event):
        if(event.x<self._xmin):
            return -1#go the other way
        else:
            if(event.x>self._xmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def decideY(self,event):
        if(event.range<self._rmin):
            return -1#go the other way
        else:
            if(event.range>self._rmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0


    def decideZ(self,event):
        if(event.y<self._zmin):
            return 1#go the other way
        else:
            if(event.y>self._zmax):
                return -1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def end_cond(self,event):
        return ((self.decideZ(event) == 0) and (self.decideX(event) == 0) and (self.decideY(event) == 0))

#A 3DOF Visual Servoing controller
class HyperApproach(VSMotion):
    @staticmethod
    def getattr():
        return { 'kx' : .05 ,  'ky' : .4 , 'kz' : .45, 
                 'x_d' : 0, 'r_d' : 1.75 , 'y_d' : 0, 
                 'x_bound': .05, 'r_bound': .25, 'y_bound':.025 ,
                 'minvx': .1, 'minvy': .1 ,'minvz' : .1} 
#define error methods to return the current error
    def yFunc(self,event):
        a = self._ky*(event.x - self._x_d)
        if(abs(a)<self._minvy):
            a = m.copysign(self._minvy,a)
        return a

    def xFunc(self,event):
        a = self._kx*(event.range - self._r_d)
        if(abs(a)<self._minvx):
            a = m.copysign(self._minvx,a)
        return a

    def zFunc(self,event):
        a = self._kz*-(event.y - self._y_d)
        if(abs(a)<self._minvz):
            a = m.copysign(self._minvz,a)
        return a

    def runMotion(self,event):
        self.motionManager._controller.moveVel(self.xFunc(event)*self.decideX(event), self.yFunc(event)*self.decideY(event), self.zFunc(event)*self.decideZ(event))
    
    def stop(self):
        self.motionManager._controller.moveVel(0,0,0)
        util.freeze(self)

    def decideY(self,event):
        if(event.x<(self._x_d - self._x_bound)):
            return 1#go the other way
        else:
            if(event.x>(self._x_d + self._x_bound)):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def decideX(self,event):
        if(event.range<(self._r_d - self._r_bound)):
            return 1#go the other way
        else:
            if(event.range>(self._r_d + self._r_bound)):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def decideZ(self,event):
        if(event.y<(self._y_d - self._y_bound)):
            return 1#go the other way
        else:
            if(event.y>(self._y_d + self._y_bound)):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def end_cond(self,event):
        return ((self.decideZ(event) == 0) and (self.decideX(event) == 0) and (self.decideY(event) == 0))
    #where are the move function definitions?
    #missing, because this variant has no need for such things, thus they aren't defined

class genHyperApproach(HyperApproach):
    def enter(self):
        pass

    def BUOY_FOUND(self,event):
        if(event.color == vision.Color.YELLOW):
            self.run(event)

    @staticmethod
    def transitions():
        return {DONE : state.State, vision.EventType.BUOY_FOUND : genHyperApproach}    

#    def DONE(self,event):
#        util.freeze(self)
                                                

