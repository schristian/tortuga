/*
 * Copyright (C) 2010 Robotics at Maryland
 * Copyright (C) 2010 Jonathan Wonders <jwonders@umd.edu>
 * All rights reserved.
 *
 * Author: Jonathan Wonders <jwonders@umd.edu>
 * File:  packages/estimation/src/modules/BasicDepthEstimationModule.cpp
 */

// STD Includes
#include <iostream>

// Library Includes
#include <boost/smart_cast.hpp>
#include <log4cpp/Category.hh>

// Project Includes
#include "vehicle/include/Events.h"
#include "estimation/include/modules/DepthAveragingModule.h"

static log4cpp::Category& LOGGER(log4cpp::Category::getInstance("StEstDepth"));

namespace ram {
namespace estimation {

DepthAveragingModule::DepthAveragingModule(
    core::ConfigNode config,
    core::EventHubPtr eventHub) :
    EstimationModule(eventHub, "DepthAveragingModule")
{
    /* initialization of estimator from config values should be done here */
    LOGGER.info("% Name EstDepth RawDepth Correction");
}

void DepthAveragingModule::update(
    core::EventPtr event, 
    EstimatedStatePtr estimatedState)
{
    /* Attempt to cast the event to a RawDepthSensorDataEventPtr */
    vehicle::RawDepthSensorDataEventPtr ievent =
        boost::dynamic_pointer_cast<vehicle::RawDepthSensorDataEvent>(event);

    /* Return if the cast failed and let people know about it. */
    if(!ievent){
        LOGGER.warn("DepthAveragingModule: update: Invalid Event Type");
        return;
    }

    /* This is where the estimation should be done
       The result should be stored in estimatedState */

    // Determine depth correction
    math::Vector3 location = ievent->sensorLocation;
    math::Vector3 currentSensorLocation = 
        estimatedState->getEstimatedOrientation() * location;
    math::Vector3 sensorMovement = 
        currentSensorLocation - location;
    double correction = sensorMovement.z;

    double timestep = ievent->timestep;

    // grab the depth and calculate the depth rate
    double depth = ievent->rawDepth + correction;
    double depthRate = (depth - m_previousDepth) / timestep;

    // put the depth into the averaging filter
    m_filteredDepth.addValue(depth);
    m_filteredDepthRate.addValue(depthRate);

    /* Return the corrected depth (its addition and not subtraction because
     * depth is positive down) */

    estimatedState->setEstimatedDepth(m_filteredDepth.getValue());
    estimatedState->setEstimatedDepthRate(m_filteredDepthRate.getValue());

    LOGGER.infoStream() << m_name << " "
                        << depth + correction << " "
                        << depth << " "
                        << correction;
}

} // namespace estimation
} // namespace ram