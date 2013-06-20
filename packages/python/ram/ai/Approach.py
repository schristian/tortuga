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

    #user must overwrite this for their own means
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

class XZCenter(VSDirect2ControlConst):

    @staticmethod
    def getattr():
        return { 'dDisp' : .01 ,  'sDisp' : .02,
                 'xmin' : -0.05 , 'xmax' : 0.05,
                 'zmin' : -0.4 , 'zmax' : 0.4, 
                 'xDisp' : 0, 'yDisp' : 0, 'zDisp' : 0} 

    def decideX(self, event):
        if(event.x<self._xmin):
            return -1#go the other way
        else:
            if(event.x>self._xmax):
                return 1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def decideZ(self, event):
        if(event.y<self._zmin):
            return 1#go the other way
        else:
            if(event.y>self._zmax):
                return -1#go the other way
            else:
            #inside the bounds, don't move
                return 0

    def xFunc(self, event):
        return self._sDisp

    def zFunc(self, event):
        return self._dDisp

    def moveX(self, dirct, event):
        self._xDisp = dirct*self.xFunc(event)

    def moveZ(self, dirct, event):
        self._zDisp = dirct*self.zFunc(event)
    

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
