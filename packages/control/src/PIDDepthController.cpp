/*
 * Copyright (C) 2010 Robotics at Maryland
 * Copyright (C) 2010 Jonathan Wonders <jwonders@umd.edu>
 * All rights reserved.
 *
 * Author: Jonathan Wonders <jwonders@umd.edu>
 * File:  packages/control/include/PIDDepthController.cpp
 */
#include <cmath>
#include <stdlib.h>
#include "control/include/PIDDepthController.h"
#include "control/include/ControllerMaker.h"

namespace ram {
namespace control {

static DepthControllerImpMakerTemplate<
    PIDDepthController>
registerPIDDepthController(
    "PIDDepthController");

PIDDepthController::PIDDepthController(ram::core::ConfigNode config) :
    DepthControllerBase(config),
    m_depthSumError(0),
    m_prevDepth(0),
    m_kp(0),
    m_kd(0),
    m_ki(0),
    dt_min(0),
    dt_max(100000)
{
    m_kp = config["kp"].asDouble();
    m_kd = config["kd"].asDouble();
    m_ki = config["ki"].asDouble();
    dt_min = config["dtMin"].asDouble();
    dt_max = config["dtMax"].asDouble();
}

math::Vector3 PIDDepthController::depthUpdate(double timestep, double depth,
                                              math::Quaternion orientation)
{
    {
        core::ReadWriteMutex::ScopedWriteLock lock(m_stateMutex);
        m_currentDepth = depth;
        m_currentOrientation = orientation;
    }

    if(timestep < dt_min)
        timestep = dt_min;
    if(timestep > dt_max)
        timestep = dt_max;

    double error = m_currentDepth - m_desiredDepth;
    double errorDot = (m_currentDepth - m_prevDepth)/timestep;
    double errorInt = m_depthSumError+error*timestep;

    {
        core::ReadWriteMutex::ScopedWriteLock lock(m_stateMutex);
        m_depthSumError = errorInt;
        m_prevDepth = m_currentDepth;
    }

    double depthControlSignal = - (m_kp*error + m_kd*errorDot + m_ki*errorInt);


    math::Vector3 controlSignal(0,0,-depthControlSignal);

    return controlSignal;
}

} // namespace control
} // namespace ram