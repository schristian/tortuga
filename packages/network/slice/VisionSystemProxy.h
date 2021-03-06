/*
 * Copyright (C) 2010 Robotics at Maryland
 * Copyright (C) 2010 Jonathan Sternberg <jsternbe@umd.edu>
 * All rights reserved.
 *
 * Author: Jonathan Sternberg <jsternbe@umd.edu>
 * File:  packages/network/slice/VisionSystemProxy.h
 */

#ifndef RAM_VISION_SLICE_VISIONSYSTEMPROXY_H_12_14_2010
#define RAM_VISION_SLICE_VISIONSYSTEMPROXY_H_12_14_2010

// Library Includes
#include <boost/shared_ptr.hpp>
#include <Ice/Ice.h>

// Project Includes
#include "core/include/Subsystem.h"
#include "vision.h"

namespace ram {
namespace vision {
class VisionSystem;
typedef boost::shared_ptr<VisionSystem> VisionSystemPtr;
} // namespace vision
} // namespace ram

namespace proxy {
namespace vision {

class VisionSystemProxy : virtual public VisionSystem
{
public:
    VisionSystemProxy(ram::core::SubsystemPtr impl);

    virtual ~VisionSystemProxy();

    virtual void redLightDetectorOn(const Ice::Current &);
    virtual void redLightDetectorOff(const Ice::Current &);
    virtual void buoyDetectorOn(const Ice::Current &);
    virtual void buoyDetectorOff(const Ice::Current &);
    virtual void binDetectorOn(const Ice::Current &);
    virtual void binDetectorOff(const Ice::Current &);
    virtual void pipeLineDetectorOn(const Ice::Current &);
    virtual void pipeLineDetectorOff(const Ice::Current &);
    virtual void ductDetectorOn(const Ice::Current &);
    virtual void ductDetectorOff(const Ice::Current &);
    virtual void downwardSafeDetectorOn(const Ice::Current &);
    virtual void downwardSafeDetectorOff(const Ice::Current &);
    virtual void gateDetectorOn(const Ice::Current &);
    virtual void gateDetectorOff(const Ice::Current &);
    virtual void targetDetectorOn(const Ice::Current &);
    virtual void targetDetectorOff(const Ice::Current &);
    virtual void windowDetectorOn(const Ice::Current &);
    virtual void windowDetectorOff(const Ice::Current &);
    virtual void barbedWireDetectorOn(const Ice::Current &);
    virtual void barbedWireDetectorOff(const Ice::Current &);
    virtual void hedgeDetectorOn(const Ice::Current &);
    virtual void hedgeDetectorOff(const Ice::Current &);
    virtual void velocityDetectorOn(const Ice::Current &);
    virtual void velocityDetectorOff(const Ice::Current &);

private:
    ram::vision::VisionSystemPtr m_impl;
};

} // namespace vision
} // namespace proxy

#endif // RAM_VISION_SLICE_VISIONSYSTEMPROXY_H
