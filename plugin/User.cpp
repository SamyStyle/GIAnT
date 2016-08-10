#include "User.h"

Touch::Touch(int userid, const glm::vec2& pos, float time, float duration)
    : m_UserID(userid),
      m_Pos(pos),
      m_Time(time),
      m_Duration(duration)
{
}

const glm::vec2& Touch::getPos() const
{
    return m_Pos;
}

float Touch::getTime() const
{
    return m_Time;
}

float Touch::getDuration() const
{
    return m_Duration;
}


User::User(int userid, float duration)
    : m_UserID(userid),
      m_Duration(duration)
{
}

User::~User()
{
}

void User::addHeadData(const HeadData& head)
{
    m_HeadData.push_back(head);
}

void User::addTouch(const Touch& touch)
{
    m_Touches.push_back(touch);
}

int User::getUserID() const
{
    return m_UserID;
}

const glm::vec3& User::getHeadPos(float time) const
{
    int i = timeToIndex(time);
    return m_HeadData[i].getPos();
}

const glm::vec2& User::getWallViewpoint(float time) const
{
    int i = timeToIndex(time);
    return m_HeadData[i].getWallViewpoint();
}

const glm::vec3& User::getHeadRot(float time) const
{
    int i = timeToIndex(time);
    return m_HeadData[i].getRot();
}

glm::vec3 User::getHeadPosAvg(float time, int smoothness) const
{
    int i = timeToIndex(time);
    glm::vec3 startSum = m_HeadData[fmax(0, i - smoothness/2)].getPosPrefixSum();
    glm::vec3 endSum = m_HeadData[fmin(m_HeadData.size()-1, i + int((smoothness+1)/2))].getPosPrefixSum();
    glm::vec3 headPos = glm::vec3(
            (endSum.x - startSum.x) / smoothness,
            (endSum.y - startSum.y) / smoothness,
            (endSum.z - startSum.z) / smoothness);
    return headPos;
}

float User::getDistTravelled(float startTime, float endTime) const
{
    std::vector<glm::vec2> posns; 
    int start_i = timeToIndex(startTime);
    int end_i = timeToIndex(endTime);
    float dist = 0.0f;
    glm::vec3 headPos = m_HeadData[0].getPos();
    glm::vec2 pos(headPos.x, headPos.z);
    glm::vec2 oldPos;
    for (int i=start_i+1; i<end_i; ++i) {
        oldPos = pos;
        headPos = m_HeadData[i].getPos();
        pos = glm::vec2(headPos.x, headPos.z);
        dist += glm::distance(pos, oldPos);
    }
    return dist;
}
    
std::vector<Touch> User::getTouches(float startTime, float endTime) const
{
    std::vector<Touch> touches;
    for (auto touch: m_Touches) {
        if (startTime <= touch.getTime() && touch.getTime() <= endTime) {
            touches.push_back(touch);
        }
    }
    return touches;
}

std::vector<glm::vec2> User::getHeadXZPosns(float startTime, float endTime) const
{
    std::vector<glm::vec2> posns; 
    int start_i = timeToIndex(startTime);
    int end_i = timeToIndex(endTime);
    for (int i=start_i; i<end_i; ++i) {
        const glm::vec3 pos = m_HeadData[i].getPos();
        posns.push_back(glm::vec2(pos.x, pos.z));
    }
    return posns;
}

std::vector<glm::vec2> User::getHeadViewpoints(float startTime, float endTime) const
{
    std::vector<glm::vec2> viewpts; 
    int start_i = timeToIndex(startTime);
    int end_i = timeToIndex(endTime);
    for (int i=start_i; i<end_i; ++i) {
        viewpts.push_back(m_HeadData[i].getWallViewpoint());
    }
    return viewpts;

}

int User::timeToIndex(float time) const
{
    return int(time * m_HeadData.size() / m_Duration);
}