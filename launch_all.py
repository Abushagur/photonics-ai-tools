
import subprocess
import os
import time

print("=" * 60)
print("  Professor Abushagur AI Tools Launcher")
print("=" * 60)

# Clean API key
api_key = os.environ.get("ANTHROPIC_API_KEY", "").replace(" ", "")
os.environ["ANTHROPIC_API_KEY"] = api_key
env = os.environ.copy()
env["ANTHROPIC_API_KEY"] = api_key

# Kill any existing streamlit processes
subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
time.sleep(2)

# Available apps
apps = [
    {
        "name": "Photonics App (backup)",
        "file": "/Users/mustafaabushagur/photonics_app_v2_backup.py",
        "port": 8501
    },
    {
        "name": "Research Assistant (51 Papers)",
        "file": "/Users/mustafaabushagur/research_assistant.py",
        "port": 8502
    }
]

for app in apps:
    if os.path.exists(app["file"]):
        subprocess.Popen(
            ["streamlit", "run", app["file"],
             "--server.port", str(app["port"])],
            env=env
        )
        print(f"✓ {app['name']}")
        print(f"  → http://localhost:{app['port']}")
        time.sleep(2)
    else:
        print(f"✗ Not found: {app['name']}")

print()
print("=" * 60)
print("  🔬 Photonics App  → http://localhost:8501")
print("  📚 Research Assistant → http://localhost:8502")
print("=" * 60)
