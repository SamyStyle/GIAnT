// GIAnT Group Interaction Analysis Toolkit
// Copyright (C) 2017 Interactive Media Lab Dresden
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#include "VWLineNode.h"
#include "ScatterPlotNode.h"
#include "User.h"
#include "HeadData.h"

#include <base/GeomHelper.h>

#include <wrapper/raw_constructor.hpp>
#include <wrapper/WrapHelper.h>

#include <string>

using namespace boost::python;
using namespace std;
using namespace avg;

char VWLineNodeName[] = "vwlinenode";
char ScatterPlotNodeName[] = "scatterplotnode";

BOOST_PYTHON_MODULE(plots)
{
    class_<VWLineNode, bases<avg::VectorNode>, boost::noncopyable>("VWLineNode", no_init)
        .def("__init__", raw_constructor(createNode<VWLineNodeName>))
        .def("setValues", &VWLineNode::setValues)
        .def("setHighlights", &VWLineNode::setHighlights)
        ;

    class_<ScatterPlotNode, bases<avg::RasterNode>, boost::noncopyable>("ScatterPlotNode", no_init)
        .def("__init__", raw_constructor(createNode<ScatterPlotNodeName>))
        .def("setPosns", &ScatterPlotNode::setPosns)
        ;

    class_<User>("User", init<int, float>())
        .def("addHeadData", &User::addHeadData)
        .def("addTouch", &User::addTouch)
        .def("getUserID", &User::getUserID)
        .def("getHeadPos", make_function(&User::getHeadPos, return_value_policy<copy_const_reference>()))
        .def("getWallViewpoint", make_function(&User::getWallViewpoint, return_value_policy<copy_const_reference>()))
        .def("getHeadRot", make_function(&User::getHeadRot, return_value_policy<copy_const_reference>()))
        .def("getHeadPosAvg", &User::getHeadPosAvg)
        .def("getDistTravelled", &User::getDistTravelled)
        .def("getAvgDistFromWall", &User::getAvgDistFromWall)
        .def("getHeadXZPosns", &User::getHeadXZPosns)
        .def("getHeadViewpoints", &User::getHeadViewpoints)
        .def("getTouches", &User::getTouches)
        ;

    class_<HeadData>("HeadData", init<int, const glm::vec3&, const glm::vec3&, double>())
        .def("setWallViewpoint", &HeadData::setWallViewpoint)
        .add_property("userid", &HeadData::getUserID) 
        .add_property("time", &HeadData::getTime)
        .add_property("pos", make_function(&HeadData::getPos, return_value_policy<copy_const_reference>()))
        .add_property("rot", make_function(&HeadData::getRot, return_value_policy<copy_const_reference>()))
        .add_property("posPrefixSum", make_function(&HeadData::getPosPrefixSum, return_value_policy<copy_const_reference>()),
                &HeadData::setPosPrefixSum)
        ;

    class_<Touch>("Touch", init<int, const glm::vec2&, float, float>())
        .add_property("pos", make_function(&Touch::getPos, return_value_policy<copy_const_reference>()))
        .add_property("time", &Touch::getTime)
        .add_property("duration", &Touch::getDuration)
        ;

    to_python_converter<vector<Touch>, to_list<vector<Touch> > >();
}

AVG_PLUGIN_API PyObject* registerPlugin()
{
    VWLineNode::registerType();
    ScatterPlotNode::registerType();
    initplots();
    PyObject* pyVWLineModule = PyImport_ImportModule("plots");

    return pyVWLineModule;
}

