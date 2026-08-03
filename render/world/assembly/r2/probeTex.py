import bpy, json
n_img_nodes = 0; offenders = []
for m in bpy.data.materials:
    if not m.use_nodes or m.node_tree is None: continue
    for nd in m.node_tree.nodes:
        if nd.type in ("TEX_IMAGE", "TEX_ENVIRONMENT"):
            n_img_nodes += 1; offenders.append((m.name, nd.type, getattr(nd.image, 'name', None)))
for ng in bpy.data.node_groups:
    for nd in ng.nodes:
        if nd.type in ("TEX_IMAGE", "TEX_ENVIRONMENT"):
            n_img_nodes += 1; offenders.append((ng.name, nd.type, getattr(nd.image, 'name', None)))
w = bpy.data.worlds
for wd in w:
    if wd.use_nodes and wd.node_tree:
        for nd in wd.node_tree.nodes:
            if nd.type in ("TEX_IMAGE", "TEX_ENVIRONMENT"):
                n_img_nodes += 1; offenders.append((wd.name, nd.type, getattr(nd.image, 'name', None)))
print("[TEX] image/environment texture nodes:", n_img_nodes)
print("[TEX] bpy.data.images:", [i.name for i in bpy.data.images])
print("[TEX] offenders:", offenders[:20])
print("[TEX] materials:", len(bpy.data.materials), "node_groups:", len(bpy.data.node_groups))
