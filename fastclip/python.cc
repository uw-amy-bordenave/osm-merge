//
// Copyright (c) 2025 OpenStreetMap US
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, either version 3 of the License, or
//     (at your option) any later version.
//
//     Underpass is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with Underpass.  If not, see <https://www.gnu.org/licenses/>.
//

// This is generated by autoconf
#ifdef HAVE_CONFIG_H
#include "fconfig.h"
#endif

// This code should actually not be built at all unless --enable-python
// is passed to configure. So we should never get, but let's be paranoid
// and wrap it with a conditional anyway.

#ifdef USE_PYTHON

#define BOOST_BIND_GLOBAL_PLACEHOLDERS 1
#include <boost/python.hpp>
#include <iostream>

#include "fastclip.hh"

namespace logging = boost::log;
using namespace boost::python;

void make_foo(const std::string &wkt) {
    std::cout << "FastClip::make_geometry(wkt) called" << std::endl;
}

BOOST_PYTHON_MODULE(fastclip)
{
    class_<FastClip, boost::noncopyable>("FastClip")
        .def("make_foo", &make_foo);
}
#endif

// local Variables:
// mode: C++
// indent-tabs-mode: nil
// End:
