/*
 * Copyright (C) 2010 Robotics at Maryland
 * Copyright (C) 2010 Jonathan Wonders <jwonders@umd.edu>
 * All rights reserved.
 *
 * Author: Jonathan Wonders <jwonders@umd.edu>
 * File:  packages/control/src/NonlinearPDRotationalController.cpp
 */

#include <iostream>
#include "control/include/NonlinearPDRotationalController.h"
#include "control/include/ControllerMaker.h"
#include "math/include/Matrix3.h"

#include "math/include/Helpers.h"


namespace ram {
namespace control {

static RotationalControllerImpMakerTemplate<NonlinearPDRotationalController>
registerNonlinearPDRotationalController("NonlinearPDRotationalController");

NonlinearPDRotationalController::NonlinearPDRotationalController(
    core::ConfigNode config) :
    RotationalControllerBase(config),
    dtMin(0.001),dtMax(0.05),
    angularPGain(0), angularDGain(0)
{
    angularPGain = config["kp"].asDouble(0);
    angularDGain = config["kd"].asDouble(0);
    dtMin = config["dtMin"].asDouble(0.001);
    dtMax = config["dtMax"].asDouble(0.05);

    inertiaEstimate[0][0] = config["inertia"][0][0].asDouble(0.201);
    inertiaEstimate[0][1] = config["inertia"][0][1].asDouble(0);
    inertiaEstimate[0][2] = config["inertia"][0][2].asDouble(0);
    inertiaEstimate[1][0] = config["inertia"][1][0].asDouble(0);
    inertiaEstimate[1][1] = config["inertia"][1][1].asDouble(1.288);
    inertiaEstimate[1][2] = config["inertia"][1][2].asDouble(0);
    inertiaEstimate[2][0] = config["inertia"][2][0].asDouble(0);
    inertiaEstimate[2][1] = config["inertia"][2][1].asDouble(0);
    inertiaEstimate[2][2] = config["inertia"][2][2].asDouble(1.288);
}


math::Vector3 NonlinearPDRotationalController::rotationalUpdate(
    double timestep,
    math::Quaternion orientation,
    math::Vector3 angularRate)
{

    //don't need this timing information in this function, but will keep it here in case it is needed in the future
    if(timestep < dtMin)
        timestep = dtMin;

    if(timestep > dtMax)
        timestep = dtMax;

    //put inertia estimate in OGRE
    math::Matrix3 J(inertiaEstimate);

    //compute error quaternion
    math::Quaternion q_tilde;
    math::Quaternion q_meas(orientation);
    math::Quaternion q_des(m_desiredOrientation);
    //i think this should be q_tilde = q_meas.errorQuaternion(q_des) 
    q_tilde = q_meas.errorQuaternion(q_des);  
    //break up quaternion into vector and scalar parts for later convenience
    math::Vector3 epsilon_tilde(q_tilde.x, q_tilde.y, q_tilde.z);
    double eta_tilde = q_tilde.w;

    //compute angular rate error
    math::Vector3 w_error(angularRate[0],
                          angularRate[1],
                          angularRate[2]);

    //compute matrix needed for gyroscopic term
    math::Matrix3 w_tilde;
    w_tilde.ToSkewSymmetric(w_error);

    //compute control signal
    math::Vector3 u;
    double kp = angularPGain;
    double kd = angularDGain;
    u = - kp*J*(math::sign(eta_tilde))*epsilon_tilde - kd*J*w_error + w_tilde*J*w_error;

    //put back into non-OGRE format
    math::Vector3 rotationalTorques(0,0,0);
    *((double*)(rotationalTorques.ptr()))=u[0];
    *((double*)(rotationalTorques.ptr())+1)=u[1];
    *((double*)(rotationalTorques.ptr())+2)=u[2];
    
    return rotationalTorques;
    
}

} // namespace control
} // namespace ram
