import os
import time
import socket
import psutil
import datetime
import subprocess
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI(title="NodePulse — Server Telemetry & Power Manager")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_battery_info():
    if os.environ.get("VERCEL"):
        return {
            "capacity": 88,
            "status": "Idle (AC Online)",
            "power_w": 14.2,
            "voltage_v": 12.1,
            "time_left": "Tersambung Listrik (AC Online)",
            "ac_online": True,
            "health": "Good (100% SOH)"
        }
    bat = {
        "capacity": 0,
        "status": "Unknown",
        "power_w": 0.0,
        "voltage_v": 0.0,
        "time_left": "N/A",
        "ac_online": False,
        "health": "Good"
    }
    path = "/sys/class/power_supply/BAT0"
    if os.path.exists(path):
        def read(f):
            try:
                with open(os.path.join(path, f), "r") as fp:
                    return fp.read().strip()
            except Exception:
                return ""
        bat["capacity"] = int(read("capacity") or 0)
        bat["status"] = read("status") or "Unknown"
        power_uw = float(read("power_now") or 0)
        energy_now_uwh = float(read("energy_now") or 0)
        bat["power_w"] = round(power_uw / 1_000_000, 2)
        bat["voltage_v"] = round(float(read("voltage_now") or 0) / 1_000_000, 2)
        
        if power_uw > 0 and energy_now_uwh > 0 and bat["status"].lower() == "discharging":
            hours = energy_now_uwh / power_uw
            h = int(hours)
            m = int((hours % 1) * 60)
            bat["time_left"] = f"{h} jam {m} mnt"
        elif bat["status"].lower() == "charging":
            bat["time_left"] = "Mengisi Daya (Charging)"
        elif bat["capacity"] >= 95:
            bat["time_left"] = "Baterai Penuh"
        else:
            bat["time_left"] = "Standby"

    ac_path = "/sys/class/power_supply/ADP1/online"
    if os.path.exists(ac_path):
        try:
            with open(ac_path, "r") as fp:
                bat["ac_online"] = (fp.read().strip() == "1")
        except Exception:
            pass
    return bat

def get_cpu_temp():
    if os.environ.get("VERCEL"):
        return 43.5
    for i in range(10):
        t_type = f"/sys/class/thermal/thermal_zone{i}/type"
        t_temp = f"/sys/class/thermal/thermal_zone{i}/temp"
        if os.path.exists(t_type) and os.path.exists(t_temp):
            try:
                name = open(t_type).read().strip()
                if "x86_pkg_temp" in name or "acpitz" in name or "cpu" in name.lower():
                    c = float(open(t_temp).read().strip()) / 1000.0
                    if 15 <= c <= 110:
                        return round(c, 1)
            except Exception:
                pass
    return 42.0

def get_wifi_info():
    if os.environ.get("VERCEL"):
        return {"ssid": "NetVerse_5G", "signal": 92, "ip": "192.168.1.10 (Homelab)"}
    wifi = {"ssid": "Disconnected", "signal": 0, "ip": "127.0.0.1"}
    try:
        out = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid,signal", "dev", "wifi"], text=True, timeout=2)
        for line in out.splitlines():
            if line.startswith("yes:"):
                parts = line.split(":")
                wifi["ssid"] = parts[1]
                wifi["signal"] = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 80
                break
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        wifi["ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        wifi["ip"] = "192.168.1.10"
    return wifi

def check_port(port):
    if os.environ.get("VERCEL"):
        return port in [8050, 8000, 9090, 5432]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def get_disk_info():
    disk = psutil.disk_usage("/")
    physical_gb = 256
    model = "NVMe SSD"
    try:
        if os.path.exists("/sys/block/nvme0n1/size"):
            sectors = int(open("/sys/block/nvme0n1/size").read().strip())
            physical_gb = int(round((sectors * 512) / (1000**3)))
        if os.path.exists("/sys/block/nvme0n1/device/model"):
            m = open("/sys/block/nvme0n1/device/model").read().strip()
            if m:
                model = m
    except Exception:
        pass

    return {
        "total_gb": round(disk.total / (1024**3), 1),
        "used_gb": round(disk.used / (1024**3), 1),
        "free_gb": round(disk.free / (1024**3), 1),
        "percent": disk.percent,
        "physical_gb": physical_gb,
        "model": model
    }

def get_full_telemetry():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_count(logical=True)
    cpu_temp = get_cpu_temp()

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk
    disk = get_disk_info()

    # Battery
    battery = get_battery_info()

    # Network / WiFi
    wifi = get_wifi_info()

    # Uptime
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now = datetime.datetime.now()
    delta = now - boot_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours} jam {minutes} menit"

    # Services
    services = [
        {"name": "AssetDesk (IT Asset Management)", "port": 8050, "icon": "🏢", "active": check_port(8050), "url": "https://assetdesk-itam.vercel.app" if os.environ.get("VERCEL") else f"http://{wifi['ip']}:8050"},
        {"name": "DeskCraft (Provisioning)", "port": 8000, "icon": "🖥️", "active": check_port(8000), "url": "https://deskcraft-app.vercel.app" if os.environ.get("VERCEL") else f"http://{wifi['ip']}:8000"},
        {"name": "Local Database Sentinel", "port": 5432, "icon": "💾", "active": True, "url": None},
        {"name": "9router AI Gateway", "port": 20128, "icon": "🧠", "active": check_port(20128), "url": None},
        {"name": "SSH Remote Terminal", "port": 22, "icon": "🔒", "active": check_port(22), "url": None}
    ]

    return {
        "hostname": socket.gethostname(),
        "model": "Infinix INBook X1 (Laptop Server)",
        "os": "Ubuntu 26.04 LTS (Kernel 7.0)",
        "uptime": uptime_str,
        "timestamp": now.strftime("%H:%M:%S"),
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_cores,
            "temp": cpu_temp,
            "name": "Intel Core i5-1035G1 (8 Cores)"
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
            "swap_percent": swap.percent,
            "swap_used_mb": int(swap.used / (1024**2))
        },
        "disk": disk,
        "battery": battery,
        "wifi": wifi,
        "services": services
    }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    telemetry = get_full_telemetry()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"t": telemetry}
    )

@app.get("/api/telemetry")
async def api_telemetry():
    return get_full_telemetry()

@app.post("/api/power/reboot")
async def api_reboot():
    def do_reboot():
        time.sleep(1)
        subprocess.run(["systemctl", "reboot"])
    
    import threading
    threading.Thread(target=do_reboot, daemon=True).start()
    return {"status": "ok", "message": "Server sedang me-restart dalam 1 detik..."}

@app.post("/api/power/shutdown")
async def api_shutdown():
    def do_shutdown():
        time.sleep(1)
        subprocess.run(["systemctl", "poweroff"])
    
    import threading
    threading.Thread(target=do_shutdown, daemon=True).start()
    return {"status": "ok", "message": "Server sedang mematikan daya (shutdown)..."}

@app.post("/api/action/clean-ram")
async def api_clean_ram():
    try:
        subprocess.run(["sync"], timeout=5)
        return {"status": "ok", "message": "RAM buffer disinkronisasi ke disk."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
