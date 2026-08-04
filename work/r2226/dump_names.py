import bpy, sys, json
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
src = argv[0]; out = argv[1]
rep = {}
with bpy.data.libraries.load(src, link=True) as (df, dt):
    rep["objects"] = list(df.objects)
    rep["collections"] = list(df.collections)
    rep["meshes"] = list(df.meshes)
    rep["materials"] = list(df.materials)
json.dump(rep, open(out, "w"))
print("objects=%d collections=%d meshes=%d materials=%d"
      % (len(rep["objects"]), len(rep["collections"]), len(rep["meshes"]), len(rep["materials"])))
print(">> STAGE RESULT: OK")
