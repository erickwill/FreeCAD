# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Joseph Coffland <joseph@cauldrondevelopment.com>   *
# *                                                                         *
# *   This file is part of FreeCAD.                                         *
# *                                                                         *
# *   FreeCAD is free software: you can redistribute it and/or modify it    *
# *   under the terms of the GNU Lesser General Public License as           *
# *   published by the Free Software Foundation, either version 2.1 of the  *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful, but        *
# *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with FreeCAD. If not, see                               *
# *   <https://www.gnu.org/licenses/>.                                      *
# *                                                                         *
# ***************************************************************************

"""FreeCAD JSON exporter"""

import json
from builtins import open as pyopen

import FreeCAD
import Draft
import Mesh
import Part

if FreeCAD.GuiUp:
    import FreeCADGui
    from draftutils.translate import translate

else:
    FreeCADGui = None
    def translate(ctxt, txt): return txt


def export(exportList, filename):
    "exports the given objects to a .json file"

    # Convert objects
    data = {
        'version': '0.0.1',
        'description': 'Mesh data exported from FreeCAD',
        'objects': [getObjectData(obj) for obj in exportList]
        }

    # Write file
    outfile = pyopen(filename, "w")
    json.dump(data, outfile, separators = (',', ':'))
    outfile.close()

    # Success
    FreeCAD.Console.PrintMessage(
        translate("Arch", "Successfully written") + ' ' + filename + "\n")


def getObjectData(obj):
    result = {'name': str(obj.Label.encode("utf8"))}
    if hasattr(obj, "Description"): result['description'] = str(obj.Description)

    if FreeCADGui:
        result['color'] = \
            Draft.getrgb(obj.ViewObject.ShapeColor, testbw = False)

    if obj.isDerivedFrom("Part::Feature"):
        mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))

        # Add wires
        wires = []
        for f in obj.Shape.Faces:
            for w in f.Wires:
                wo = Part.Wire(Part.__sortEdges__(w.Edges))
                wires.append([[v.x, v.y, v.z]
                              for v in wo.discretize(QuasiDeflection = 0.1)])

        result['wires'] = wires

    elif obj.isDerivedFrom("Mesh::Feature"): mesh = obj.Mesh

    # Add vertices
    count = 0
    vertices = []
    vIndex = {}

    for p in mesh.Points:
        v = p.Vector
        vIndex[p.Index] = count
        count += 1
        vertices.append([v.x, v.y, v.z])

    result['vertices'] = vertices

    # Add facets & normals
    facets = [[vIndex[i] for i in f.PointIndices] for f in mesh.Facets]
    normals = [[f.Normal.x, f.Normal.y, f.Normal.z] for f in mesh.Facets]

    result['normals'] = normals
    result['facets'] = facets

    return result
