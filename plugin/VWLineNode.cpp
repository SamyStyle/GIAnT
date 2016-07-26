
#include "VWLineNode.h"

#include <base/Exception.h>
#include <base/ScopeTimer.h>
#include <graphics/VertexArray.h>
#include <player/TypeDefinition.h>
#include <player/TypeRegistry.h>

#include <iostream>
#include <string>
#include <math.h>

using namespace avg;
using namespace std;
using namespace boost;

const int WIDTH_WINDOW=5;

void VWLineNode::registerType()
{
    TypeDefinition def = TypeDefinition("vwlinenode", "vectornode", 
            ExportedObject::buildObject<VWLineNode>)
        .addArg(Arg<float>("maxwidth", 1, false, offsetof(VWLineNode, m_MaxWidth)))
        ;
    const char* allowedParentNodeNames[] = {"div", "canvas", "avg", 0};
    TypeRegistry::get()->registerType(def, allowedParentNodeNames);
}

VWLineNode::VWLineNode(const ArgList& args, const string& sPublisherName)
    : VectorNode(args, sPublisherName)
{
    args.setMembers(this);
}

VWLineNode::~VWLineNode()
{
}

static ProfilingZoneID SetValuesProfilingZone("VWLineNode::setValues");

void VWLineNode::setValues(const vector<glm::vec2>& pts, const vector<float>& dists)
{
    ScopeTimer timer(SetValuesProfilingZone);
    m_Pts = pts;
    Pixel32 color = getColor();
    m_VertexCoords.clear();
    m_Colors.clear();
    m_Triangles.clear();

    float avgWidth = 0;
    vector<float> clampedDists;
    vector<float> widths;
    for (int i=0; i<pts.size(); ++i) {
        float dist = max(0.f, min(1.f, dists[i]));
        clampedDists.push_back(dist);
        widths.push_back(calcWidth(dist));
    }

    for (int i=0; i<pts.size(); ++i) {
        int vi = m_VertexCoords.size();

        glm::vec2 pt = pts[i];
        float opacity = calcOpacity(clampedDists[i]);

        bool bStartEnd = false;
        if (i >= WIDTH_WINDOW/2) {
            avgWidth -= widths[i-WIDTH_WINDOW/2];
            bStartEnd = true;
        }
        if (i < pts.size() - WIDTH_WINDOW/2) {
            avgWidth += widths[i+WIDTH_WINDOW/2];
            bStartEnd = true;
        }
        float visWidth;
        if (bStartEnd) {
            visWidth = widths[i];
        } else {
            visWidth = avgWidth;
        }

        glm::vec2 offset(0, visWidth);
        glm::vec2 pt_t = pt - offset;
        glm::vec2 pt_b = pt + offset;
        m_VertexCoords.push_back(pt_t);
        m_VertexCoords.push_back(pt_b);
        appendColors(2, color, opacity);

        if (i>0) {
            m_Triangles.push_back(glm::ivec3(vi-2, vi, vi-1));
            m_Triangles.push_back(glm::ivec3(vi-1, vi, vi+1));
        }
    }

    setDrawNeeded();
}

static ProfilingZoneID SetHighlightsProfilingZone("VWLineNode::setHighlights");

void VWLineNode::setHighlights(vector<float> xPosns, vector<float> widths)
{
    ScopeTimer timer(SetHighlightsProfilingZone);
    if (m_Pts.size() == 0) {
        throw(Exception(AVG_ERR_UNSUPPORTED, "Call setValues before setHighlights."));
    }
    for (int i=0; i<xPosns.size(); ++i) {
        float leftX = xPosns[i];
        float w = max(widths[i], 2.f);
        float rightX = leftX + w;
        glm::vec2 curPt = posOnLine(leftX);
        m_VertexCoords.push_back(curPt + glm::vec2(0,-3));
        m_VertexCoords.push_back(curPt + glm::vec2(0,3));
        appendColors(2, Pixel32(255,255,255,255), 255);
        for (float x = leftX+1; x < rightX; ++x) {
            int vi = m_VertexCoords.size();
            curPt = posOnLine(x);
            m_VertexCoords.push_back(curPt + glm::vec2(0,-3));
            m_VertexCoords.push_back(curPt + glm::vec2(0,3));
            appendColors(2, Pixel32(255,255,255,255), 255);
            m_Triangles.push_back(glm::ivec3(vi-2, vi+1, vi-1));
            m_Triangles.push_back(glm::ivec3(vi-2, vi  , vi+1));
        }
    }
}

void VWLineNode::calcVertexes(const VertexDataPtr& pVertexData, Pixel32 color)
{
    for (unsigned int i = 0; i < m_VertexCoords.size(); i++) {
        pVertexData->appendPos(m_VertexCoords[i], glm::vec2(0,0), m_Colors[i]);
    }

    for (unsigned int i = 0; i < m_Triangles.size(); i++) {
        pVertexData->appendTriIndexes(m_Triangles[i].x, m_Triangles[i].y, 
                m_Triangles[i].z);
    }
}

void VWLineNode::appendColors(int numEntries, avg::Pixel32 color, float opacity)
{
    color.setA(opacity*255);
    for (int i=0; i < numEntries; i++) {
        m_Colors.push_back(color);
    }
}

float VWLineNode::calcWidth(float dist)
{
    return 1 + dist * m_MaxWidth;
}

float VWLineNode::calcOpacity(float dist)
{
    return pow(1-dist, 2);
}

glm::vec2 VWLineNode::posOnLine(float x) const
{
    int ptIndex = 0;
    while (m_Pts[ptIndex].x < x && ptIndex < m_Pts.size()-1) {
        ptIndex++;
    }
    glm::vec2 curPt;
    if (ptIndex == 0 || ptIndex == m_Pts.size()-1) {
        curPt = glm::vec2(x, m_Pts[ptIndex].y);
    } else {
        float part = (x - m_Pts[ptIndex-1].x)/(m_Pts[ptIndex].x - m_Pts[ptIndex-1].x);
        AVG_ASSERT(part >= 0 && part <= 1);
        float y = (1-part)*m_Pts[ptIndex-1].y + part*m_Pts[ptIndex].y;
        curPt = glm::vec2(x, y);
    }
    return curPt;
}
