/*
 * Copyright (C) 2007 Robotics at Maryland
 * Copyright (C) 2007 Joseph Lisee <jlisee@umd.edu>
 * All rights reserved.
 *
 * Author: Joseph Lisee <jlisee@umd.edu>
 * File:  packages/packages/vehicle/test/src/TestTortuga.cxx
 */

// STD Includes
#include <set>
#include <iostream>

// Library Includes
#include <UnitTest++/UnitTest++.h>
#include <boost/bind.hpp>
#include <boost/foreach.hpp>
#include <boost/assign/list_of.hpp>

// Project Includes
#include "vehicle/include/Vehicle.h"
#include "vehicle/include/device/IThruster.h"

#include "core/include/ConfigNode.h"
#include "core/include/EventConnection.h"
#include "core/include/EventHub.h"

#include "math/test/include/MathChecks.h"
#include "math/include/Events.h"

#include "vehicle/test/include/MockDevice.h"
#include "vehicle/test/include/MockIMU.h"
#include "vehicle/test/include/MockThruster.h"
#include "vehicle/test/include/MockDepthSensor.h"
#include "vehicle/test/include/MockVelocitySensor.h"
#include "vehicle/test/include/MockPositionSensor.h"

using namespace ram;


static const std::string CONFIG("{'name' : 'TestVehicle'}");

struct VehicleFixture
{
    VehicleFixture() :
        eventHub(new core::EventHub()),
        veh(new vehicle::Vehicle(core::ConfigNode::fromString(CONFIG),
                                 boost::assign::list_of(eventHub)))
    {
    }
    
    ~VehicleFixture() {
        delete veh;
    }

    core::EventHubPtr eventHub;
    vehicle::Vehicle* veh;
};

void eventHelper(std::string* eventType, ram::core::EventPtr event)
{
    *eventType = event->type;
}

TEST(DeviceCreation)
{
    std::string config =
            "{"
            "'name' : 'TestVehicle',"
            "'Devices' : {"
            "    'IMU' : {'type' : 'MockIMU'},"
            "    'PSU' : {'type' : 'MockDevice'}"
            " },"
            "}";

    core::EventHubPtr eventHub(new core::EventHub());
    vehicle::IVehicle* veh = 
        new vehicle::Vehicle(core::ConfigNode::fromString(config),
                             boost::assign::list_of(eventHub));
    
    CHECK_EQUAL("IMU", veh->getDevice("IMU")->getName());
    CHECK_EQUAL("PSU", veh->getDevice("PSU")->getName());

    // Check to make sure the device got the right vehicle
    MockDevice* dev = dynamic_cast<MockDevice*>(veh->getDevice("PSU").get());
    CHECK(dev);
    CHECK_EQUAL(veh, dev->vehicle.get());
    
    // Check to make sure the list of names matches
    std::set<std::string> expNames = boost::assign::list_of("IMU")("PSU");
    std::set<std::string> givenNames;
    std::vector<std::string> names = veh->getDeviceNames();

    BOOST_FOREACH(std::string name, names)
    {
        givenNames.insert(name);
    }

    CHECK_EQUAL(2u, givenNames.size());
    CHECK(expNames == givenNames);

    // Make sure events get through
    std::string eventType;

    eventHub->subscribeToType(
        vehicle::device::IThruster::FORCE_UPDATE,
        boost::bind(eventHelper, &eventType, _1));

    veh->getDevice("IMU")->publish(vehicle::device::IThruster::FORCE_UPDATE,
                                   core::EventPtr(new core::Event()));

    CHECK_EQUAL(vehicle::device::IThruster::FORCE_UPDATE, eventType);
    delete veh;
}

TEST_FIXTURE(VehicleFixture, IMU)
{
    MockIMU* imu = new MockIMU("IMU");
    veh->_addDevice(vehicle::device::IDevicePtr(imu));
    
    math::Vector3 accel(1,2,3);
    math::Vector3 angularRate(4,5,6);
    math::Quaternion orientation(7,8,9,10);
    
    imu->linearAcceleration = accel;
    imu->angularRate = angularRate;
    imu->orientation = orientation;
    CHECK_EQUAL(accel, veh->getLinearAcceleration());
    CHECK_EQUAL(angularRate, veh->getAngularRate());
    CHECK_EQUAL(orientation, veh->getOrientation());
}

TEST_FIXTURE(VehicleFixture, DepthSensor)
{
    // Create mock depth sensor and IMU
    MockDepthSensor* depthSensor = new MockDepthSensor("SensorBoard");
    MockIMU* imu = new MockIMU("IMU");
    imu->orientation = math::Quaternion::IDENTITY;

    // Add the mock devices to our vehicle
    veh->_addDevice(vehicle::device::IDevicePtr(depthSensor));
    veh->_addDevice(vehicle::device::IDevicePtr(imu));

    // Check the depth
    double depth = 2.6;
    depthSensor->depth = depth;
    CHECK_EQUAL(depth, veh->getDepth());

    // Now check depth correction for orientation

    // The sensor is in the back, left, and upper corner of the vehicle
    depthSensor->location = math::Vector3(-1, -0.2, 0.2);
    // We are pitched forward down by 15 degrees
    math::Quaternion orientation(math::Degree(15), math::Vector3::UNIT_Y);
    imu->orientation = orientation;
    // We add to the expected depth because the downward pitch moves our sensor
    // to a shallow depth then we are really at
    double expectedDepth = depth + 0.252;
    CHECK_CLOSE(expectedDepth, veh->getDepth(), 0.00001);
}

TEST_FIXTURE(VehicleFixture, VelocitySensor)
{
    // Create mock velocity sensor and IMU
    MockVelocitySensor* velocitySensor =
        new MockVelocitySensor("VelocitySensor");
//    MockIMU* imu = new MockIMU("IMU");
//    imu->orientation = math::Quaternion::IDENTITY;

    // Add the mock devices to our vehicle
    veh->_addDevice(vehicle::device::IDevicePtr(velocitySensor));
//    veh->_addDevice(vehicle::device::IDevicePtr(imu));

    // Check the velocity
    math::Vector2 velocity = math::Vector2(2,5);
    velocitySensor->velocity = velocity;
    CHECK_CLOSE(velocity, veh->getVelocity(), 0.0001);

    // Now check velocity correction for orientation

    // The sensor is in the back, left, and upper corner of the vehicle
    //velocitySensor->location = math::Vector3(-1, -0.2, 0.2);
    // We are pitched forward down by 15 degrees
    //math::Quaternion orientation(math::Degree(15), math::Vector3::UNIT_Y);
    //imu->orientation = orientation;
    // We add to the expected velocity because the downward pitch moves our sensor
    // to a shallow velocity then we are really at
    //math::Vector2 expectedVelocity = velocity + 0.252;
    //CHECK_CLOSE(expectedVelocity, veh->getVelocity(), 0.00001);
}

TEST_FIXTURE(VehicleFixture, PositionSensor)
{
    // Create mock position sensor and IMU
    MockPositionSensor* positionSensor =
        new MockPositionSensor("PositionSensor");
//    MockIMU* imu = new MockIMU("IMU");
//    imu->orientation = math::Quaternion::IDENTITY;

    // Add the mock devices to our vehicle
    veh->_addDevice(vehicle::device::IDevicePtr(positionSensor));
//    veh->_addDevice(vehicle::device::IDevicePtr(imu));

    // Check the position
    math::Vector2 position = math::Vector2(2, 5);
    positionSensor->position = position;
    CHECK_CLOSE(position, veh->getPosition(), 0.0001);

    // Now check position correction for orientation

    // The sensor is in the back, left, and upper corner of the vehicle
    //positionSensor->location = math::Vector3(-1, -0.2, 0.2);
    // We are pitched forward down by 15 degrees
    //math::Quaternion orientation(math::Degree(15), math::Vector3::UNIT_Y);
    //imu->orientation = orientation;
    // We add to the expected position because the downward pitch moves our sensor
    // to a shallow position then we are really at
    //math::Vector2 expectedPosition = position + 0.252;
    //CHECK_CLOSE(expectedPosition, veh->getPosition(), 0.00001);
}


TEST_FIXTURE(VehicleFixture, _addDevice)
{
    MockDevice* mockDevice = new MockDevice("TestName");
    veh->_addDevice(vehicle::device::IDevicePtr(mockDevice));

    CHECK_EQUAL(mockDevice, veh->getDevice("TestName").get());
    CHECK_EQUAL("TestName", veh->getDevice("TestName")->getName());
}

void orientationHelper(math::Quaternion* result, ram::core::EventPtr event)
{
    math::OrientationEventPtr oevent =
    boost::dynamic_pointer_cast<ram::math::OrientationEvent>(event);
    *result = oevent->orientation;
}

TEST_FIXTURE(VehicleFixture, Event_ORIENTATION_UPDATE)
{
    MockIMU* imu = new MockIMU("IMU");  
    veh->_addDevice(vehicle::device::IDevicePtr(imu));
    
    math::Quaternion result = math::Quaternion::IDENTITY;
    math::Quaternion expected(7,8,9,10);
    imu->orientation = expected;
    
    // Subscribe to the event
    core::EventConnectionPtr conn = veh->subscribe(
        vehicle::IVehicle::ORIENTATION_UPDATE,
        boost::bind(orientationHelper, &result, _1));

    veh->update(0);
    imu->publishUpdate(expected);
    CHECK_EQUAL(expected, result);
    
    conn->disconnect();
}

void depthHelper(double* result, ram::core::EventPtr event)
{
    math::NumericEventPtr nevent =
    boost::dynamic_pointer_cast<ram::math::NumericEvent>(event);
    *result = nevent->number;
}

TEST_FIXTURE(VehicleFixture, Event_DEPTH_UPDATE)
{
    MockDepthSensor* depthSensor = new MockDepthSensor("SensorBoard");
    MockIMU* imu = new MockIMU("IMU");

    veh->_addDevice(vehicle::device::IDevicePtr(depthSensor));
    veh->_addDevice(vehicle::device::IDevicePtr(imu));
    
    double result = 0;
    double expected = 5.7;
    depthSensor->depth = expected;
    
    // Subscribe to the event
    core::EventConnectionPtr conn = veh->subscribe(
        vehicle::IVehicle::DEPTH_UPDATE,
        boost::bind(depthHelper, &result, _1));

    veh->update(0);
    depthSensor->publishUpdate(expected);
    CHECK_EQUAL(expected, result);
    
    conn->disconnect();
}

void vector2Helper(math::Vector2* result, ram::core::EventPtr event)
{
    math::Vector2EventPtr nevent =
    boost::dynamic_pointer_cast<ram::math::Vector2Event>(event);
    *result = nevent->vector2;
}

TEST_FIXTURE(VehicleFixture, Event_POSITION_UPDATE)
{
    MockPositionSensor* positionSensor =
        new MockPositionSensor("PositionSensor");
//    MockIMU* imu = new MockIMU("IMU");

    veh->_addDevice(vehicle::device::IDevicePtr(positionSensor));
//    veh->_addDevice(vehicle::device::IDevicePtr(imu));
    
    math::Vector2 result(0, 0);
    math::Vector2 expected(5.7, 2);
    positionSensor->position = expected;
    
    // Subscribe to the event
    core::EventConnectionPtr conn = veh->subscribe(
        vehicle::IVehicle::POSITION_UPDATE,
        boost::bind(vector2Helper, &result, _1));

    veh->update(0);
    positionSensor->publishUpdate(expected);
    CHECK_EQUAL(expected, result);
    
    conn->disconnect();
}

TEST_FIXTURE(VehicleFixture, Event_VELOCITY_UPDATE)
{
    MockVelocitySensor* velocitySensor =
        new MockVelocitySensor("VelocitySensor");
//    MockIMU* imu = new MockIMU("IMU");

    veh->_addDevice(vehicle::device::IDevicePtr(velocitySensor));
//    veh->_addDevice(vehicle::device::IDevicePtr(imu));
    
    math::Vector2 result(0, 0);
    math::Vector2 expected(5.7, 2);
    velocitySensor->velocity = expected;
    
    // Subscribe to the event
    core::EventConnectionPtr conn = veh->subscribe(
        vehicle::IVehicle::VELOCITY_UPDATE,
        boost::bind(vector2Helper, &result, _1));

    veh->update(0);
    velocitySensor->publishUpdate(expected);
    CHECK_EQUAL(expected, result);
    
    conn->disconnect();
}


struct ThrusterVehicleFixture
{
    ThrusterVehicleFixture() :
        eventHub(new core::EventHub()),
        veh(new vehicle::Vehicle(core::ConfigNode::fromString(CONFIG),
                                 boost::assign::list_of(eventHub))),
        starboard(new MockThruster("StarboardThruster")),
        port(new MockThruster("PortThruster")),
        fore(new MockThruster("ForeThruster")),
        aft(new MockThruster("AftThruster")),
        top(new MockThruster("TopThruster")),
        bottom(new MockThruster("BottomThruster"))
    {
        veh->_addDevice(vehicle::device::IDevicePtr(starboard));
        veh->_addDevice(vehicle::device::IDevicePtr(port));
        veh->_addDevice(vehicle::device::IDevicePtr(fore));
        veh->_addDevice(vehicle::device::IDevicePtr(aft));
        veh->_addDevice(vehicle::device::IDevicePtr(top));
        veh->_addDevice(vehicle::device::IDevicePtr(bottom));

        for (int i = 0; i < 6; ++i)
            forceArray[i] = 0.0;
    }
    
    ~ThrusterVehicleFixture() {
        delete veh;
    }

    double* thrusterForceArray()
    {
        forceArray[0] = starboard->force;
        forceArray[1] = port->force;
        forceArray[2] = fore->force;
        forceArray[3] = aft->force;
        forceArray[4] = top->force;
        forceArray[5] = bottom->force;
        return forceArray;
    }
    
    core::EventHubPtr eventHub;
    vehicle::Vehicle* veh;
    MockThruster* starboard;
    MockThruster* port;
    MockThruster* fore;
    MockThruster* aft;
    MockThruster* top;
    MockThruster* bottom;
private:
    double forceArray[6];
};

TEST_FIXTURE(ThrusterVehicleFixture, applyForcesAndTorque)
{
    // Make all thrusters have the same offset
    starboard->offset = 1.0;
    port->offset = 1.0;
    fore->offset = 1.0;
    aft->offset = 1.0;
    top->offset = 1.0;
    bottom->offset = 1.0;

    // +X Torque
    veh->applyForcesAndTorques(ram::math::Vector3::ZERO,
                               ram::math::Vector3(5, 0, 0));
    double expectedForcesPosXTorque[] = {
        0.0, // Starboard
        0.0, // Port
        0.0, // Fore
        0.0, // Aft
        2.5, // Top
        -2.5, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosXTorque, thrusterForceArray(), 6);

    // +Y Force
    veh->applyForcesAndTorques(ram::math::Vector3(0, 5, 0),
                               ram::math::Vector3::ZERO);
    double expectedForcesPosYForce[] = {
        0.0, // Starboard
        0.0, // Port
        0.0, // Fore
        0.0, // Aft
        2.5, // Top
        2.5, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosYForce, thrusterForceArray(), 6);

    /// @TODO FIX ME!!!
    // +Y Torque (THIS IS BROKEN)
    veh->applyForcesAndTorques(ram::math::Vector3::ZERO,
                               ram::math::Vector3(0, 6, 0));
    double expectedForcesPosYTorque[] = {
        0.0, // Starboard
        0.0, // Port
        -3.0, // Fore
        3.0, // Aft
        0.0, // Top
        0.0, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosYTorque, thrusterForceArray(), 6);

    // +Z Force
    veh->applyForcesAndTorques(ram::math::Vector3(0, 0, 6),
                               ram::math::Vector3::ZERO);
    double expectedForcesPosZForce[] = {
        0.0, // Starboard
        0.0, // Port
        3.0, // Fore
        3.0, // Aft
        0.0, // Top
        0.0, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosZForce, thrusterForceArray(), 6);

    // +Z Torque (THIS IS BROKEN)
    veh->applyForcesAndTorques(ram::math::Vector3::ZERO,
                               ram::math::Vector3(0, 0, 7.5));
    double expectedForcesPosZTorque[] = {
        3.75,  // Starboard
        -3.75, // Port
        0.0, // Fore
        0.0, // Aft
        0.0, // Top
        0.0, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosZTorque, thrusterForceArray(), 6);

    // +X Force
    veh->applyForcesAndTorques(ram::math::Vector3(7.5, 0, 0),
                               ram::math::Vector3::ZERO);
    double expectedForcesPosXForce[] = {
        3.75, // Starboard
        3.75, // Port
        0.0, // Fore
        0.0, // Aft
        0.0, // Top
        0.0, // Bottom
    };
    CHECK_ARRAY_EQUAL(expectedForcesPosXForce, thrusterForceArray(), 6);
}

TEST_FIXTURE(ThrusterVehicleFixture, safeThrusters)
{
    starboard->enabled = true;
    port->enabled = true;
    fore->enabled = true;
    aft->enabled = true;
    top->enabled = true;
    bottom->enabled = true;

    veh->safeThrusters();

    CHECK_EQUAL(false, starboard->enabled);
    CHECK_EQUAL(false, port->enabled);
    CHECK_EQUAL(false, fore->enabled);
    CHECK_EQUAL(false, aft->enabled);
    CHECK_EQUAL(false, top->enabled);
    CHECK_EQUAL(false, bottom->enabled);
}

TEST_FIXTURE(ThrusterVehicleFixture, unsafeThrusters)
{
    veh->unsafeThrusters();

    CHECK_EQUAL(true, starboard->enabled);
    CHECK_EQUAL(true, port->enabled);
    CHECK_EQUAL(true, fore->enabled);
    CHECK_EQUAL(true, aft->enabled);
    CHECK_EQUAL(true, top->enabled);
    CHECK_EQUAL(true, bottom->enabled);
}
