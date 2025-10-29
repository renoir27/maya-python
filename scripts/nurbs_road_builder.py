"""NURBS road generation utility for Autodesk Maya 2022.

This script builds a full road section from a selected centerline curve
by creating a series of offset curves and lofted surfaces.  A simple UI
is provided so artists can tweak the offsets before generating the road.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import maya.cmds as cmds


@dataclass
class RoadParameters:
    """Container for the offsets that define the road profile."""

    road_offset: float = 3.0
    drain_offset: float = 0.5
    curb_offset: float = 0.2
    curb_height: float = 0.2
    sidewalk_offset: float = 2.0
    sidewalk_curb_offset: float = 0.2


def _as_transform(node: Sequence[str] | str) -> str:
    """Return the transform node for the provided object."""

    if isinstance(node, (list, tuple)):
        node = node[0]
    if cmds.nodeType(node) == "nurbsCurve":
        parents = cmds.listRelatives(node, parent=True, fullPath=True)
        if parents:
            return parents[0]
    return node  # type: ignore[return-value]


def _curve_shape(curve: str) -> str:
    """Return the shape node for a nurbs curve transform."""

    shapes = cmds.listRelatives(curve, shapes=True, fullPath=True) or []
    return shapes[0] if shapes else curve


def _offset_curve(curve: str, distance: float, name: str) -> str:
    """Create an offset curve and rename it."""

    shape = _curve_shape(curve)
    offset = cmds.offsetCurve(
        shape,
        distance=distance,
        ch=False,
        st=True,
        tol=1e-3,
    )
    offset_transform = _as_transform(offset)
    return cmds.rename(offset_transform, name)


def _duplicate_curve(curve: str, name: str, translate_y: float = 0.0) -> str:
    """Duplicate a curve and move it in Y if needed."""

    dup = cmds.duplicate(curve, rr=True)[0]
    dup = cmds.rename(dup, name)
    if translate_y:
        cmds.move(0.0, translate_y, 0.0, dup, relative=True, objectSpace=True)
    return dup


def _loft_surface(curves: Sequence[str], name: str) -> str:
    """Create a loft surface from a sequence of curves."""

    surface = cmds.loft(
        *curves,
        ch=False,
        ar=True,
        d=1,
        u=True,
        name=name,
    )
    return _as_transform(surface)


def build_nurbs_road(main_curve: str, params: RoadParameters) -> Dict[str, List[str]]:
    """Construct the NURBS road system based on the supplied curve."""

    if not cmds.objExists(main_curve):
        raise ValueError("Selected curve does not exist.")

    if cmds.nodeType(_curve_shape(main_curve)) != "nurbsCurve":
        raise ValueError("The selected object must be a NURBS curve.")

    base_name = main_curve.split("|")[-1]

    created_curves: List[str] = []
    created_surfaces: List[str] = []

    # Road edges
    road_left = _offset_curve(main_curve, params.road_offset, f"{base_name}_road_L_crv")
    road_right = _offset_curve(main_curve, -params.road_offset, f"{base_name}_road_R_crv")
    created_curves.extend([road_left, road_right])

    road_surface = _loft_surface(
        [road_left, road_right],
        f"{base_name}_road_srf",
    )
    created_surfaces.append(road_surface)

    # Drain offsets
    drain_left = _offset_curve(road_left, params.drain_offset, f"{base_name}_drain_L_crv")
    drain_right = _offset_curve(road_right, -params.drain_offset, f"{base_name}_drain_R_crv")
    created_curves.extend([drain_left, drain_right])

    left_drain_surface = _loft_surface(
        [road_left, drain_left],
        f"{base_name}_drain_L_srf",
    )
    right_drain_surface = _loft_surface(
        [road_right, drain_right],
        f"{base_name}_drain_R_srf",
    )
    created_surfaces.extend([left_drain_surface, right_drain_surface])

    # Curb base and height
    curb_base_left = _offset_curve(drain_left, params.curb_offset, f"{base_name}_curbBase_L_crv")
    curb_base_right = _offset_curve(drain_right, -params.curb_offset, f"{base_name}_curbBase_R_crv")
    created_curves.extend([curb_base_left, curb_base_right])

    curb_top_left = _duplicate_curve(
        curb_base_left,
        f"{base_name}_curbTop_L_crv",
        translate_y=params.curb_height,
    )
    curb_top_right = _duplicate_curve(
        curb_base_right,
        f"{base_name}_curbTop_R_crv",
        translate_y=params.curb_height,
    )
    created_curves.extend([curb_top_left, curb_top_right])

    # Surfaces for curb walls and cap
    curb_wall_left = _loft_surface(
        [curb_base_left, curb_top_left],
        f"{base_name}_curbWall_L_srf",
    )
    curb_wall_right = _loft_surface(
        [curb_base_right, curb_top_right],
        f"{base_name}_curbWall_R_srf",
    )
    created_surfaces.extend([curb_wall_left, curb_wall_right])

    drain_cap_left = _loft_surface(
        [drain_left, curb_base_left],
        f"{base_name}_drainCap_L_srf",
    )
    drain_cap_right = _loft_surface(
        [drain_right, curb_base_right],
        f"{base_name}_drainCap_R_srf",
    )
    created_surfaces.extend([drain_cap_left, drain_cap_right])

    # Sidewalks
    sidewalk_left = _offset_curve(
        curb_top_left,
        params.sidewalk_offset,
        f"{base_name}_sidewalk_L_crv",
    )
    sidewalk_right = _offset_curve(
        curb_top_right,
        -params.sidewalk_offset,
        f"{base_name}_sidewalk_R_crv",
    )
    created_curves.extend([sidewalk_left, sidewalk_right])

    sidewalk_surface_left = _loft_surface(
        [curb_top_left, sidewalk_left],
        f"{base_name}_sidewalk_L_srf",
    )
    sidewalk_surface_right = _loft_surface(
        [curb_top_right, sidewalk_right],
        f"{base_name}_sidewalk_R_srf",
    )
    created_surfaces.extend([sidewalk_surface_left, sidewalk_surface_right])

    # Sidewalk curbs (outer edge)
    sidewalk_curb_left = _offset_curve(
        sidewalk_left,
        params.sidewalk_curb_offset,
        f"{base_name}_sidewalkCurb_L_crv",
    )
    sidewalk_curb_right = _offset_curve(
        sidewalk_right,
        -params.sidewalk_curb_offset,
        f"{base_name}_sidewalkCurb_R_crv",
    )
    created_curves.extend([sidewalk_curb_left, sidewalk_curb_right])

    sidewalk_border_left = _loft_surface(
        [sidewalk_left, sidewalk_curb_left],
        f"{base_name}_sidewalkBorder_L_srf",
    )
    sidewalk_border_right = _loft_surface(
        [sidewalk_right, sidewalk_curb_right],
        f"{base_name}_sidewalkBorder_R_srf",
    )
    created_surfaces.extend([sidewalk_border_left, sidewalk_border_right])

    # Grouping
    curves_grp = cmds.group(
        created_curves,
        name=f"{base_name}_roadCurves_GRP",
    )
    surfaces_grp = cmds.group(
        created_surfaces,
        name=f"{base_name}_roadSurfaces_GRP",
    )
    master_grp = cmds.group(
        [curves_grp, surfaces_grp],
        name=f"{base_name}_roadSystem_GRP",
    )

    return {
        "curves": created_curves,
        "surfaces": created_surfaces,
        "groups": [curves_grp, surfaces_grp, master_grp],
    }


class RoadBuilderUI:
    """Simple Maya UI wrapper for the road builder."""

    WINDOW_NAME = "nurbsRoadBuilderWindow"

    def __init__(self) -> None:
        self.fields: Dict[str, str] = {}

    def show(self) -> None:
        if cmds.window(self.WINDOW_NAME, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)

        window = cmds.window(
            self.WINDOW_NAME,
            title="NURBS Road Builder",
            sizeable=False,
            widthHeight=(300, 240),
        )
        column = cmds.columnLayout(
            adjustableColumn=True,
            rowSpacing=6,
            columnAlign="left",
            columnAttach=("both", 10),
        )

        cmds.text(label="Select the centerline NURBS curve before running.")
        cmds.separator(height=10, style="in")

        self.fields["road_offset"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Road Offset",
            value1=RoadParameters.road_offset,
        )
        self.fields["drain_offset"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Drain Offset",
            value1=RoadParameters.drain_offset,
        )
        self.fields["curb_offset"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Curb Offset",
            value1=RoadParameters.curb_offset,
        )
        self.fields["curb_height"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Curb Height",
            value1=RoadParameters.curb_height,
        )
        self.fields["sidewalk_offset"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Sidewalk Offset",
            value1=RoadParameters.sidewalk_offset,
        )
        self.fields["sidewalk_curb_offset"] = cmds.floatFieldGrp(
            numberOfFields=1,
            label="Sidewalk Curb Offset",
            value1=RoadParameters.sidewalk_curb_offset,
        )

        cmds.separator(height=10, style="in")
        cmds.button(
            label="Build Road",
            height=35,
            command=lambda *_: self._on_build_pressed(),
        )
        cmds.button(
            label="Close",
            command=lambda *_: cmds.deleteUI(window, window=True),
        )

        cmds.showWindow(window)

    def _on_build_pressed(self) -> None:
        params = RoadParameters(
            road_offset=cmds.floatFieldGrp(self.fields["road_offset"], query=True, value1=True),
            drain_offset=cmds.floatFieldGrp(self.fields["drain_offset"], query=True, value1=True),
            curb_offset=cmds.floatFieldGrp(self.fields["curb_offset"], query=True, value1=True),
            curb_height=cmds.floatFieldGrp(self.fields["curb_height"], query=True, value1=True),
            sidewalk_offset=cmds.floatFieldGrp(
                self.fields["sidewalk_offset"], query=True, value1=True
            ),
            sidewalk_curb_offset=cmds.floatFieldGrp(
                self.fields["sidewalk_curb_offset"], query=True, value1=True
            ),
        )

        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("Please select a NURBS curve to use as the road centerline.")
            return

        try:
            result = build_nurbs_road(selection[0], params)
        except ValueError as exc:
            cmds.warning(str(exc))
            return

        cmds.select(result["groups"][-1])
        cmds.inViewMessage(
            statusMessage="Road system created.",
            pos="midCenter",
            fade=True,
        )


def show() -> None:
    """Entry point to show the UI."""

    RoadBuilderUI().show()


if __name__ == "__main__":
    show()
