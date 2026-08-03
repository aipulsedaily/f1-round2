
import bpy, json, sys
sys.path.insert(0, '/home/zany/f1-round2/tools')
import socket_blend_scan as SBS



open(sys.argv[-1], "w").write(json.dumps(SBS.scan_open_blend(), indent=1))
