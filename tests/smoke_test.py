"""
Smoke test for Sprint 0.1.1.
Verifies:
  1. Backend starts and GET /health returns 200 with {"status": "ok"}
  2. Frontend builds successfully
"""

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
HEALTH_URL = "http://localhost:18001/health"

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}" + (f"  -- {detail}" if detail else ""))
        failed += 1


def test_backend_health():
    print("\n[Backend Health Check]")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "18001"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(3)
        req = urllib.request.Request(HEALTH_URL, method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        status_code = resp.getcode()
        check("HTTP 200 status", status_code == 200, f"got {status_code}")
        check('Response body is {"status":"ok"}', data == '{"status":"ok"}', f"got {data}")
    except Exception as e:
        check("Backend reachable", False, str(e))
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_frontend_build():
    print("\n[Frontend Build Check]")
    result = subprocess.run(
        "npm run build",
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    check("Frontend build exits 0", result.returncode == 0, f"exit code {result.returncode}")
    dist_index = FRONTEND_DIR / "dist" / "index.html"
    check("dist/index.html exists", dist_index.exists())
    dist_assets = list((FRONTEND_DIR / "dist" / "assets").glob("*.js"))
    check("dist/assets/*.js exists", len(dist_assets) > 0, f"found {len(dist_assets)} js files")
    if result.returncode != 0:
        print("  Build stderr:", result.stderr[:500])
    else:
        print("  Build output:", result.stdout[-300:].strip())


def main():
    print("=" * 50)
    print("Sprint 0.1.1 Smoke Tests")
    print("=" * 50)
    test_backend_health()
    test_frontend_build()
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'=' * 50}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
