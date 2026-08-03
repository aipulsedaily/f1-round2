
import bpy, os, sys
ROOT = '/home/zany/f1-round2'
for p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "world", "items")):
    sys.path.insert(0, p)
BY_INDEX = True

import pont_girder as PG
import marshal_post_column as HS

if BY_INDEX:
    # Reproduce R2-070 EXACTLY: route the by-name write back through the
    # by-integer one, at the index `Normal` used to occupy.
    def _broken(self, node, name, v):
        self._feed(node, 5, v)
    HS.NG._feed_named = _broken

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
PG._simple_mat("SIA_REAL_%s" % ("BROKEN" if BY_INDEX else "FIXED"),
               [(0.0165, 0.0165, 0.0170), (0.0345, 0.0345, 0.0355),
                (0.048, 0.047, 0.045), (0.058, 0.056, 0.052)],
               0.72, (900.0, 900.0))
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
