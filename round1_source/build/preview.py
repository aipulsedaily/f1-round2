"""Mirror the latest offline render into the live Blender UI.

Renders happen in a separate background /opt Blender (the only build that can
drive this GPU), so the live session's own "Render Result" stays empty. This
loads the newest PNG into an Image Editor in the visible window instead, and
reloads it in place so the user just watches one panel update.
"""

import os

import bpy

PREVIEW_NAME = "PEEP_PREVIEW"


def _image_editor_areas():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "IMAGE_EDITOR":
                yield win, area


def _largest_area(win, exclude=("PROPERTIES", "OUTLINER")):
    best = None
    for area in win.screen.areas:
        if area.type in exclude:
            continue
        if best is None or area.width * area.height > best.width * best.height:
            best = area
    return best


def show(path, workspace="Rendering"):
    """Point the preview Image Editor at `path` and refresh it."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return {"error": f"missing {path}"}

    img = bpy.data.images.get(PREVIEW_NAME)
    if img is None:
        img = bpy.data.images.load(path, check_existing=False)
        img.name = PREVIEW_NAME
    else:
        img.filepath = path
        img.source = "FILE"
    img.reload()

    win = bpy.context.window_manager.windows[0]
    if workspace and workspace in bpy.data.workspaces:
        try:
            win.workspace = bpy.data.workspaces[workspace]
        except (AttributeError, TypeError):
            pass

    areas = list(_image_editor_areas())
    if not areas:
        area = _largest_area(win)
        if area is not None:
            area.type = "IMAGE_EDITOR"
            areas = [(win, area)]

    shown = 0
    for _w, area in areas:
        space = area.spaces.active
        space.image = img
        try:
            space.zoom_to_fit = True
        except AttributeError:
            pass
        area.tag_redraw()
        shown += 1

    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()

    return {"shown_in": shown, "path": path,
            "size": list(img.size), "workspace": win.workspace.name}
