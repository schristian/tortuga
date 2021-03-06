# Copyright (C) 2008 Maryland Robotics Club
# Copyright (C) 2008 Joseph Lisee <jlisee@umd.edu>
# All rights reserved.
#
# Author: Joseph Lisee <jlisee@umd.edu>
# Edited, 2013: Johnny Mao <jmao@umd.edu> 
# File:  packages/python/ram/ai/gate.py

"""
A state machine to go through the gate:
 - Waits for Switch
 - Dives to depth
 - Goes forward while looking for a gate
 - 'Approaches' the gate
 - Moves forward through the gate.
 
 
Requires the following subsystems:
 - timerManager - ram.timer.TimerManager
 - motionManager - ram.motion.MotionManager
 - controller - ext.control.IController
"""

# TODO: Add some way for required subsystems to be checked more throughly

# Project Imports
import ext.core as core
import ext.math as math

from ext.control import yawVehicleHelper

import ram.ai.state as state
import ram.ai.Utility as utility
import ram.ai.Approach as approach
import ram.motion as motion
import ram.motion.search
from  ram.motion.basic import Frame

#imports added as of 2013
import ext.vision as vision
import ram.timer as timer

# Denotes when this state machine finishes
COMPLETE = core.declareEventType('COMPLETE')

# global variables

# -- Used to store the last known locations of the image and robot
# -- before the image was lost
global lastVisionEvent
global lastLocation
global lastDepth
# --

class Wait(state.State):
    @staticmethod
    def transitions():
        # TODO: Replace with a start event from the vehicle or sensor board
        return {"Start" : Start}

class IMAGATE(state.State):

    @staticmethod
    def transitions():
        return { vision.EventType.GATE_FOUND : IMAGATE }


    def GATE_FOUND(self, event):
        print '----------'
        print 'X: ' + str(event.x)
        print 'Y: ' + str(event.y)
        print 'Size: ' + str(event.range)


# Start state --
class Start(utility.MotionState):
    """
    This Start state dives down to a depth at which the gate should be around.
    Translate into a state that moves forward to look for the gate.
    """

    @staticmethod
    def transitions():
        return { motion.basic.MotionManager.FINISHED : Start,
                 utility.DONE : FindGate }

    @staticmethod
    def getattr():
        return { 'rate': 0.3 }
    
    def enter(self):
        self.visionSystem.gateDetectorOn()
        self.dive(3, self._rate)
 
    def exit(self):
        utility.freeze(self)
        self.motionManager.stopCurrentMotion()    
#end of Start state
       
# added as of 2013
# FindGate state --
class FindGate(state.State):

    """
    The robot should be facing in the general direction of the gate at start off.
    Now the robot will move forward bit by bit until it "sees" the gate
    Will transition to approach to draw closer to the gate.
    """
    DONE = core.declareEventType('DONE')

    @staticmethod
    def transitions():
        return { vision.EventType.GATE_FOUND : GateApproachApproach,
                 motion.basic.MotionManager.FINISHED : End }

    @staticmethod
    def getattr():
        return { 'avgRate' : 0.15, 'distance' : 5 }

    def enter(self):
        forwardTrajectory = motion.trajectories.Vector2CubicTrajectory(
            initialValue = math.Vector2.ZERO,
            finalValue = math.Vector2(self._distance, 0),
            initialRate = self.stateEstimator.getEstimatedVelocity(),
            avgRate = self._avgRate)
        forwardMotion = motion.basic.Translate(
            trajectory = forwardTrajectory,
            frame = Frame.LOCAL)
        self.motionManager.setMotion(forwardMotion)

    def exit(self):
        utility.freeze(self)
        self.motionManager.stopCurrentMotion()
# end of FindGate state

# start of GateApproachApproach
class GateApproachApproach(approach.SuperApproach):


    
    
    @staticmethod
    def transitions():
            return { approach.DONE : Forward,
                     vision.EventType.GATE_FOUND : GateApproachApproach,
                     vision.EventType.GATE_LOST : GateReacquire }

    @staticmethod
    def getattr():
        return { 'dx' : .35,'dy' : -.25, 'dz' : .25,
                 'fDisp' : .4 ,  'sDisp' : .2,
                 'xmin' : -0.035 , 'xmax' : 0.035,
                 'zmin' : 0, 'zmax': 0.5,
                 'rmin' : 375, 'rmax' : 425,
                 'xDisp' : 0, 'yDisp' : 0, 'zDisp' : 0 }

    def enter(self):
       pass

    def GATE_FOUND(self, event):
        global lastLocation
        global lastDepth
        lastLocation = self.stateEstimator.getEstimatedPosition()
        lastDepth = self.stateEstimator.getEstimatedDepth()
        print '----------'
        print 'X: ' + str(event.x)
        print 'Y: ' + str(event.y)
        print 'Range: ' + str(event.range)
        self.run(event)
        

    def end_cond(self, event):
        return ( (self.decideY(event) == 0) and \
                 (self.decideX(event) == 0) and \
                 (self.decideZ(event) == 0) )

    def exit(self):
        utility.freeze(self)
        self.motionManager.stopCurrentMotion()
    

# end of GateApproachApproach state


# added as of 2013
# GateReacquire state --
# Small note: critRange is a global variable, it is used here to determine if the robot 
# has overshot its stopping position. lastLocation is also a global variable that stores 
# the last event prior to being lost. Both were set in the previous state, Gateapproach 
# and both will be used to determine the proper location of the robot before losing the gate.
class GateReacquire(state.State):

    """
    This state positions itself using that last known coordinates of the gate as close to its 
    desired location as possible. If the gate is not found when in transition to its desired
    location the robot will go into its forward state.
    Forward state
    """
   

    DONE = core.declareEventType('DONE')

    @staticmethod
    def transitions():
        return { motion.basic.MotionManager.FINISHED : Forward,
                 vision.EventType.GATE_FOUND : GateApproachApproach,
                 GateReacquire.DONE : Forward }

    @staticmethod
    def getattr():
        return { 'speed' : 0.15 }

    def enter(self):
        global lastLocation
        global lastVisionEvent # not used at the moment
        global lastDepth
        #TranslateMotion
        XYCorrectionTrajectory = motion.trajectories.Vector2CubicTrajectory(
            initialValue = self.stateEstimator.getEstimatedPosition(),
            finalValue = lastLocation,
            initialRate = self.stateEstimator.getEstimatedVelocity(),
            avgRate = self._speed)
        XYMotion = motion.basic.Translate(
            trajectory = XYCorrectionTrajectory,
            frame = Frame.LOCAL)

        #Dive Motion
        diveTrajectory = motion.trajectories.ScalarCubicTrajectory(
            initialValue = self.stateEstimator.getEstimatedDepth(),
            finalValue = lastDepth,
            initialRate = self.stateEstimator.getEstimatedDepthRate(),
            avgRate = self._speed)
        diveMotion = motion.basic.ChangeDepth(
            trajectory = diveTrajectory)

        self.motionManager.setMotion(XYMotion, diveMotion)
        
        
    def exit(self):
        self.motionManager.stopCurrentMotion()
# end of GateReacquire state


# added as of 2013
# Forward state --
class Forward(state.State):
    """
    A state in which the vehicle will move forward a specified amount
    """

    @staticmethod
    def transitions():
        return { motion.basic.MotionManager.FINISHED : End }

    @staticmethod
    def getattr():
        return { 'avgRate' : 0.15, 'distance' : 5 }


    def enter(self):
        self.visionSystem.gateDetectorOff()
        forwardTrajectory = motion.trajectories.Vector2CubicTrajectory(
            initialValue = math.Vector2.ZERO,
            finalValue = math.Vector2(self._distance, 0),
            initialRate = self.stateEstimator.getEstimatedVelocity(),
            avgRate = self._avgRate)
        forwardMotion = motion.basic.Translate(
            trajectory = forwardTrajectory,
            frame = Frame.LOCAL)

        self.motionManager.setMotion(forwardMotion)


    def exit(self):
        self.motionManager.stopCurrentMotion()
# end of Forward state


# End state --
class End(state.State):
    def enter(self):
        self.publish(COMPLETE, core.Event())
# end
