/*
 * Copyright (C) 2007 Robotics at Maryland
 * Copyright (C) 2007 Daniel Hakim
 * All rights reserved.
 *
 * Author: Daniel Hakim <dhakim@umd.edu>
 * File:  packages/vision/include/GateDetector.h
 */

#ifndef RAM_GATE_DETECTOR_H_06_23_2007
#define RAM_GATE_DETECTOR_H_06_23_2007

// Project Includes
#include "vision/include/Common.h"
#include "vision/include/Detector.h"
#include "core/include/ConfigNode.h"
#include "vision/include/GateDetectorKate.h"
#include "vision/include/BuoyDetectorKate.h"
// Must be included last
#include "vision/include/Export.h"

namespace ram {
namespace vision {
    
class RAM_EXPORT GateDetector : public Detector
{
  public:
    bool found;
    GateDetector(core::ConfigNode config,
                 core::EventHubPtr eventHub = core::EventHubPtr());
    GateDetector(Camera*);
    ~GateDetector();
    
    void update();
    void processImage(Image* input, Image* output= 0);
    void publishFoundEvent(foundLines::parallelLinesPairs finalPairs);
    Mat processImageColor(Image* input);
    void publishFoundEventBuoy(foundLines::parallelLinesPairs finalPairs, Color::ColorType color); //hack to trick event system
    void publishLostEventBuoy(Color::ColorType color);
    double getX();
    double getY();
    void show(char* window);
    IplImage* getAnalyzedImage();
    blobfinder blob;

 int returnRedmin(void);
int returnRedmax(void);
int getmaxdiff(); //gets the maximum allowed difference for kate function
int m_maxdiff;

   
    
  private:

bool m_found;
    void init(core::ConfigNode config);
      ColorFilter* m_filter;
/**Filter for Red value for VisionToolV2*/

	//Mat img_whitebalance;    

	int m_redminH;
	int m_redmaxH;
	int m_greenminH;
	int m_greenmaxH;
	int m_yellowminH;
	int m_yellowmaxH;
	int m_minS;
	int m_maxS;
	bool m_checkRed;

    int gateX;
    int gateY;
    double gateXNorm;
    double gateYNorm;
    IplImage* gateFrame;
    IplImage* gateFrameRatios;
    
    Image* frame;
    Camera* cam;


/*Kate edit - same whitebalance image and final output*/
	cv::Mat img_whitebalance;
	cv::Mat img_gate;
	foundLines gate;
cv::Mat erosion_dst,erosion_dst_red, erosion_dst_green, erosion_dst_blue;

};
    
} // namespace vision
} // namespace ram

#endif // RAM_GATE_DETECTOR_H_06_23_2007
