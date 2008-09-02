# Copyright (C) 2007 Maryland Robotics Club
# Copyright (C) 2007 Joseph Lisee <jlisee@umd.edu>
# All rights reserved.
#
# Author: Joseph Lisee <jlisee@umd.edu>
# File:  packages/python/ram/motion.py

# Python Imports
import math as pmath

# Project Imports
import ext.core as core
import ext.control as control
import ext.vehicle as vehicle
import ext.math as math

import ram.timer as timer


class MotionManager(core.Subsystem):
    """
    Starts and stops the AI's currently active ram.motion.basic.Motion
    
    Requires the following subsystems:
     - ext.control.IController
     - ext.vehicle.IVehicle
     - ext.core.EventHub
     - ext.core.QueuedEventHub
    """
    
    def __init__(self, config, deps):
        """
        Create a MotionManager object
        """
        core.Subsystem.__init__(self, config.get('name', 'MotionManager'), deps)
        self._inPlaneMotion = None
        self._depthMotion = None
        self._orientationMotion = None
        
        self._controller = core.Subsystem.getSubsystemOfType(control.IController, 
                                                             deps, 
                                                             nonNone = True)
        
        self._vehicle = core.Subsystem.getSubsystemOfType(vehicle.IVehicle, 
                                                          deps, 
                                                          nonNone = True)
        
        self._qeventHub = core.Subsystem.getSubsystemOfType(core.QueuedEventHub, 
                                                           deps,
                                                           nonNone = True)
        
        self._eventHub = core.Subsystem.getSubsystemOfExactType(
            core.EventHub, deps, nonNone = True)
            
    def setMotion(self, motion):
        """
        Stops the current motion and starts this one
        """
        eventPublisher = core.EventPublisher(self._eventHub)
        started = False
        
        
        if motion.type & Motion.IN_PLANE:
            if self._inPlaneMotion is not None:
                self._stopMotion(self._inPlaneMotion)
            self._inPlaneMotion = motion
            
            self._inPlaneMotion.start(self._controller, self._vehicle, 
                                      self._qeventHub, eventPublisher)
            started = True
            
        if motion.type & Motion.DEPTH:
            if self._depthMotion is not None:
                self._stopMotion(self._depthMotion)
            self._depthMotion = motion
            
            if not started:
                self._depthMotion.start(self._controller, self._vehicle, 
                                        self._qeventHub, eventPublisher)
                started = True
            
        if motion.type & Motion.ORIENTATION:
            if self._orientationMotion is not None:
                self._stopMotion(self._orientationMotion)
            self._orientationMotion = motion
            
            if not started:
                self._orientationMotion.start(self._controller, self._vehicle, 
                                              self._qeventHub, eventPublisher)

    def stopCurrentMotion(self):
        """
        Calls stop() on the current motion if it exists.
        """
        if self._inPlaneMotion is not None:
            self._stopMotion(self._inPlaneMotion)
        if self._depthMotion is not None:
            self._stopMotion(self._depthMotion)
        if self._orientationMotion is not None:
            self._stopMotion(self._orientationMotion)
        
    def stopMotionOfType(self, _type):
        if _type & Motion.IN_PLANE:
            assert not (self._inPlaneMotion is None)
            self._stopMotion(self._inPlaneMotion)
        elif _type & Motion.DEPTH:
            assert not (self._depthMotion is None)
            self._stopMotion(self._depthMotion)
        elif _type & Motion.ORIENTATION:
            assert not (self._orientationMotion is None)
            self._stopMotion(self._orientationMotion)
        
    @property
    def currentMotion(self):
        motionCount = 0
        motion = None
        if not (self._inPlaneMotion is None):
            motionCount += 1
            motion = self._inPlaneMotion
        if not (self._depthMotion is None) and \
          not (motion == self._depthMotion):
            motionCount += 1
            motion = self._depthMotion
        if not (self._orientationMotion is None) and \
          not (motion == self._orientationMotion):
            motionCount += 1
            motion = self._orientationMotion
            
        if motionCount <= 1:
            return motion
        return (self._inPlaneMotion, self._depthMotion, 
                self._orientationMotion)
      
    def _stopMotion(self, motion):
        motion.stop()
        if motion.type & Motion.IN_PLANE:
            assert not (self._inPlaneMotion is None)
            assert motion == self._inPlaneMotion
            self._inPlaneMotion = None
        if motion.type & Motion.DEPTH:
            assert not (self._depthMotion is None)
            assert motion == self._depthMotion
            self._depthMotion = None
        if motion.type & Motion.ORIENTATION:
            assert not (self._orientationMotion is None)
            assert motion == self._orientationMotion
            self._orientationMotion = None
        
    def background(self):
        pass
        
    def backgrounded(self):
        return True
        
    def unbackground(self, join = True):
        pass
        
    def update(self, timeSinceLastUpdate):
        pass
    
core.SubsystemMaker.registerSubsystem('MotionManager', MotionManager)
        
class Motion(object):
    """
    A class which encapsulates some sort of motion of the vehicle.
    """
    
    
    IN_PLANE = 1
    DEPTH = 2
    ORIENTATION = 4
    NORMAL = IN_PLANE | DEPTH | ORIENTATION
    
    FINISHED = core.declareEventType('FINISHED')
    
    def __init__(self, _type = NORMAL):
        self._eventPublisher = None
        self._controller = None
        self._vehicle = None
        self._eventHub = None
        self._type = _type
    
    def start(self, controller, vehicle, eventHub, eventPublisher):
        """
        Called by the motion manager to state main state variables
        
        DO NOT OVERRIED this method directly.  Overrive _start instead.
        
        @type  controller: ext.control.IController 
        @param controller: The current controller of the vehicle
        
        @type  vehicle: ext.vehicle.IVehicle
        @param vehicle: The vehicle we are controlling
        
        @type  eventHub: ext.core.QueuedEventHub
        @param eventHub: The event hub to subscribe to events through 
        """
        self._controller = controller
        self._vehicle = vehicle
        self._eventHub =  eventHub
        self._eventPublisher = eventPublisher
        
        # Set up the publish method to be seemless and easy
        self.publish = self._eventPublisher.publish
        
        self._start()
        
    @property
    def type(self):
        return self._type
        
    def _start(self):
        raise Exception("You must implement this method")
    
    def _finish(self):
        """
        Raises, motion finished event.
        """
        event = core.Event()
        event.motion = self
        self.publish(Motion.FINISHED, event)
        
    def stop(self):
        pass
    
class ChangeDepth(Motion):
    def __init__(self, desiredDepth, steps):
        """
        @type  desiredDepth: float
        @param desiredDepth: Depth you wish the sub to be at
        
        @type  steps: int
        @param steps: Number of increments you wish to change depth in    
        """
        Motion.__init__(self, _type = Motion.DEPTH)
        
        self._steps = steps
        self._desiredHeading = desiredDepth
        self._conn = None
        
    def _start(self):
        # Register to recieve AT_DEPTH events
        self._conn = self._eventHub.subscribe(control.IController.AT_DEPTH,
                                              self._controller, self._atDepth)

        # Start changing depth
        self._nextDepth(self._vehicle.getDepth())
        
    def _nextDepth(self,currentVehicleDepth):
        """
        Descreses depth by one 'step' of the remaing depth change
        """
        depthDifference = self._desiredHeading - currentVehicleDepth 
        depthChange = depthDifference/self._steps
        self._controller.setDepth(currentVehicleDepth + depthChange)
        
    def _atDepth(self, event):
        """
        AT_DEPTH event handler, called when the vehicle reaches the command depth
        """
        self._steps -= 1
        currentVehicleDepth = event.number
        if not (self._steps == 0):
            self._nextDepth(currentVehicleDepth)
        else:
            self._finish()
    
    def _finish(self):
        """
        Finishes off the motion, disconnects events, and putlishes finish event
        """
        Motion._finish(self)
        self._conn.disconnect()

    def stop(self):
        self._conn.disconnect()

class RateChangeDepth(Motion):
    NEXT_DEPTH = core.declareEventType('NEXT_DEPTH')
    
    def __init__(self, desiredDepth, speed, rate = 10):
        """
        @type  desiredDepth: float
        @param desiredDepth: Depth you wish the sub to be at
        
        @type  steps: int
        @param steps: Number of increments you wish to change depth in    
        """

        Motion.__init__(self, _type = Motion.DEPTH)

        self._desiredDepth = desiredDepth
        self._speed = float(speed)
        self._rate = float(rate)
        self._interval = 1 / float(rate)
        self._conn = None
        self._timer = None
        
    def _start(self):
        # Ensure the controller is consistent with vehicle
        currentDepth = self._vehicle.getDepth()
        self._controller.setDepth(currentDepth)
        
        absDepthDifference = pmath.fabs(currentDepth - self._desiredDepth)

        self._stepCount = absDepthDifference / (self._speed / self._rate)
        if self._stepCount != 0:
            self._stepSize = (self._desiredDepth - currentDepth) / self._stepCount
        else:
            self._stepSize = 0.0001
        self._stepCount = int(self._stepCount)
        
        self._timer  = timer.Timer(self, RateChangeDepth.NEXT_DEPTH,
                                   self._interval, repeat = True)
        # Register to NEXT_DEPTH events
        self._conn = self._eventHub.subscribeToType(RateChangeDepth.NEXT_DEPTH,
                                                    self._onTimer)
        self._timer.start()

    def _onTimer(self, event):
        setDepth = self._controller.getDepth()
        depthDiff = pmath.fabs(setDepth - self._desiredDepth)
        
        if (self._stepCount > 0) and (depthDiff > 0.0001):
            self._controller.setDepth(self._controller.getDepth() + \
                                      self._stepSize)
            self._stepCount -= 1
        else:
            self._finish()
        
    def _finish(self):
        """
        Finishes off the motion, disconnects events, and putlishes finish event
        """
        self.stop()
        Motion._finish(self)

    def stop(self):
        if self._timer is not None:
            self._timer.stop()
        if self._conn is not None:
            self._conn.disconnect()
        
class ChangeHeading(Motion):
    def __init__(self, desiredHeading, steps):
        """
        @type  desiredHeading: float
        @param desiredHeading: Heading you wish to sub to be at
        
        @type  steps: int
        @param steps: Number of increments you wish to change heading in    
        """
        Motion.__init__(self)
        
        self._steps = steps
        self._desiredHeading = desiredHeading
        self._conn = None
        
    def _start(self):
        # Register to recieve AT_ORIENTATION events
        self._conn = self._eventHub.subscribe(control.IController.AT_ORIENTATION,
                                              self._controller, 
                                              self._atOrientation)

        # Start changing heading
        self._nextHeading(self._vehicle.getOrientation().getYaw(True).valueDegrees())
        
    def _nextHeading(self, currentVehicleHeading):
        """
        Changes the heading by one 'step' of the remaing heading change
        """
        headingDifference = self._desiredHeading - currentVehicleHeading 
        headingChange = headingDifference/self._steps
        self._controller.yawVehicle(headingChange)
        
    def _atOrientation(self, event):
        """
        AT_ORIENTATION event handler
        
        Called when the vehicle reaches the command orientation
        """
        self._steps -= 1
        currentVehicleHeading = event.orientation.getYaw(True).valueDegrees()
        if not (self._steps == 0):
            self._nextHeading(currentVehicleHeading)
        else:
            self._finish()
    
    def _finish(self):
        """
        Finishes off the motion, disconnects events, and putlishes finish event
        """
        Motion._finish(self)
        self._conn.disconnect()
        
class RateChangeHeading(Motion):
    NEXT_HEADING = core.declareEventType('NEXT_HEADING')
    
    def __init__(self, desiredHeading, speed, rate = 10):
        """
        @type  desiredHeading: float
        @param desiredHeading: Heading you wish to sub to be at
        
        @type  steps: int
        @param steps: Number of increments you wish to change depth in    
        """

        Motion.__init__(self, _type = Motion.ORIENTATION)

        self._desiredHeading = desiredHeading
        self._speed = float(speed)
        self._rate = float(rate)
        self._interval = 1 / float(rate)
        self._conn = None
        self._timer = None
        
        self._rotFactor = 0.0
        self._rotProgress = 0.0
        
    def _start(self):
        # Grab current State
        currentOrient = self._vehicle.getOrientation()
        currentHeading = currentOrient.getYaw(True).valueDegrees()
        
        # Generate our source and dest orientation
        self._srcOrient = math.Quaternion(math.Degree(currentHeading),
                                          math.Vector3.UNIT_Z)
        self._destOrient = math.Quaternion(math.Degree(self._desiredHeading),
                                          math.Vector3.UNIT_Z)
        
        # Ensure the controller is consistent with our start state
        self._controller.setDesiredOrientation(self._srcOrient)
        
        # Determine slerp variables
        absHeadingDifference = pmath.fabs(currentHeading - self._desiredHeading)

        stepCount = absHeadingDifference / (self._speed / self._rate)
        self._rotFactor = 1.0 / (stepCount)
        self._rotProgress = 0.0

        self._timer  = timer.Timer(self, RateChangeHeading.NEXT_HEADING,
                                   self._interval, repeat = True)
        
        # Register to NEXT_HEADING events
        self._conn = self._eventHub.subscribeToType(
            RateChangeHeading.NEXT_HEADING, self._onTimer)
        self._timer.start()

    def _onTimer(self, event):
        self._rotProgress += self._rotFactor
        
        currentHeading = self._controller.getDesiredOrientation().getYaw(True)
        currentHeading = currentHeading.valueDegrees()
        
        if (pmath.fabs(currentHeading - self._desiredHeading) > 0.01):
            newOrien = math.Quaternion.Slerp(self._rotProgress, 
                                             self._srcOrient,
                                             self._destOrient, True)
            self._controller.setDesiredOrientation(newOrien)
        else:
            self._finish()
        
    def _finish(self):
        """
        Finishes off the motion, disconnects events, and putlishes finish event
        """
        self._timer.stop()
        self._conn.disconnect()
        Motion._finish(self)

    def stop(self):
        if self._conn is not None:
            self._conn.disconnect()
        if self._timer is not None:
            self._timer.stop()
        
class MoveDirection(Motion):
    """
    Moves and asbsolute direction regardless of orientation
    """
    
    def __init__(self, desiredHeading, speed):
        Motion.__init__(self, _type = Motion.IN_PLANE)
        
        self._speed = speed
        self._direction = math.Quaternion(math.Degree(desiredHeading),
                                          math.Vector3.UNIT_Z)
        self._connections = []
        
    def _start(self):
        # Register to recieve ORIENTATION_UPDATE events
        conn = self._eventHub.subscribe(vehicle.IVehicle.ORIENTATION_UPDATE,
                                        self._vehicle, self._onOrientation)
        self._connections.append(conn)
        
        self._update()
        
    def _update(self):
        # Start the vehicle forward and create a timer to change the motion
        self._setSpeeds(self._vehicle.getOrientation())
        
    def _setSpeeds(self, orientation):
        """
        Steps the speeds to vehicle based on the given orientation
        """
        # Direction of desired vehicle motion
        desiredDirection = self._direction.getYaw(True).valueDegrees()
        
        # Vehicle heading in degrees
        vehicleHeading =  orientation.getYaw(True).valueDegrees()
        
        yawTransform = vehicleHeading - desiredDirection

        # Find speed in vehicle cordinates
        baseSpeed = math.Vector3(self._speed, 0, 0)
        toVehicleFrame = math.Quaternion(math.Degree(yawTransform),
                                         math.Vector3.UNIT_Z)
        vehicleSpeed = toVehicleFrame * baseSpeed
        
        # Finally set the speeds
        self._controller.setSpeed(vehicleSpeed.x)
        self._controller.setSidewaysSpeed(vehicleSpeed.y)
        
    def _onOrientation(self, event):
        """
        Corrects commanded speed based on vehicle alignment
        """
        self._setSpeeds(event.orientation)
        
    def stop(self):
        """
        Called by the MotionManager when another motion takes over, stops movement
        """
        self._controller.setSpeed(0)
        self._controller.setSidewaysSpeed(0)

        for conn in self._connections:
            conn.disconnect()
            
class TimedMoveDirection(MoveDirection):
    COMPLETE = core.declareEventType('COMPLETE')
    
    def __init__(self, desiredHeading, speed, duration):
        MoveDirection.__init__(self, desiredHeading, speed)
        self._duration = duration
        self._timer = None
        
    def _start(self):
        # Subscribe to our ending event
        conn = self._eventHub.subscribeToType(TimedMoveDirection.COMPLETE,
                                              self._onComplete)
        self._connections.append(conn)
        
        self._startTimer()
        MoveDirection._start(self)
        
    def _onComplete(self, event):
        self.stop()
        self._finish()

    def _startTimer(self):
        self._timer = timer.Timer(self._eventPublisher, 
                                  TimedMoveDirection.COMPLETE,
                                  self._duration)
        self._timer.start()
        
    def stop(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        MoveDirection.stop(self)