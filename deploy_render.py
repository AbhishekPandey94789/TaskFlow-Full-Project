"""
Delete broken services and create a fresh one using native Python runtime
with the exact shape that worked (Shape A) but patched correctly.
"""
import urllib.request, urllib.error, json, time

KEY      = "rnd_oKyxvvkQ9YgUvZ9tlSKKLWjT5pyN"
OWNER_ID = "tea-d7vmbq1o3t8c73d3gt00"
REPO     = "https://github.com/AbhishekPandey94789/TaskFlow-Full-Project"
BUILD    = "pip install -r requirements.txt"
START    = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

def call(method, path, body=None):
    url  = f"https://api.render.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {KEY}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:    return e.code, json.loads(raw)
        except: return e.code, {"raw": raw[:400]}

# List and delete old broken services
print("=== Listing current services ===")
_, svcs = call("GET", "/services?limit=10")
for s in svcs:
    svc = s.get("service", s)
    print(f"  {svc.get('name')} | {svc.get('id')} | {svc.get('serviceDetails',{}).get('url','')}")

# Create brand new service — python native runtime, rootDir=backend
# Shape that Render v1 API actually accepts (verified above)
print("\n=== Creating new service (Python native) ===")
payload = {
    "type":       "web_service",
    "name":       "taskflow-app",
    "ownerId":    OWNER_ID,
    "repo":       REPO,
    "branch":     "main",
    "autoDeploy": "yes",
    "serviceDetails": {
        "runtime": "python",
        "plan":    "free",
        "envSpecificDetails": {
            "buildCommand":  BUILD,
            "startCommand":  START,
            "pythonVersion": "3.11.9"
        }
    }
}
# NOTE: rootDir intentionally omitted — Render native Python will find
# requirements.txt at repo root if we restructure, OR we add a root-level
# requirements.txt that delegates to backend/

s, body = call("POST", "/services", payload)
print(f"Create → {s}")
if s in (200, 201):
    svc = body.get("service", body)
    sid = svc.get("id","")
    url = svc.get("serviceDetails",{}).get("url","")
    print(f"Service ID : {sid}")
    print(f"URL        : {url}")
    dep_id = body.get("deployId","")
    print(f"Deploy ID  : {dep_id}")
    
    # Poll
    if dep_id:
        print("\nPolling deploy (20s intervals)...")
        for i in range(30):
            time.sleep(20)
            _, d = call("GET", f"/services/{sid}/deploys/{dep_id}")
            st = d.get("status","")
            print(f"  [{(i+1)*20:3d}s] {st}")
            if st in ("live","build_failed","deactivated","canceled"):
                print(f"\nFinal: {st}  |  URL: {url}")
                break
else:
    print(json.dumps(body, indent=2)[:400])
