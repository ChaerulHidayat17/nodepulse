# ⚡ NodePulse — Headless Server Telemetry & Power Manager

> **Real-time Linux system health monitoring, battery intelligence & headless hardware telemetry platform.**  
> Built by **Chaerul Hidayat** ([@ChaerulHidayat17](https://github.com/ChaerulHidayat17)) for Linux server operations and headless laptop infrastructure.

---

## 🎯 Overview

NodePulse is designed for lightweight, continuous telemetry monitoring of repurposed headless Linux servers (such as laptops converted into 24/7 homelab servers). It monitors hardware thermals, CPU load, memory utilization, network bandwidth, and hardware power states in real-time.

---

## 🚀 Key Features

* **⚡ Real-Time System Telemetry**: CPU utilization, load averages, memory consumption, disk I/O, and storage health via `psutil`.
* **🔋 Advanced Power & Battery Intelligence**: Native Linux sysfs integration (`/sys/class/power_supply/BAT0`) monitoring charging wattage, voltage, battery degradation health, and thermal overheating protection.
* **🌐 Web Dashboard**: Responsive, clean FastAPI + Jinja2 frontend with real-time dynamic refresh.
* **🛡️ Low Overhead Daemon**: Runs continuously as a lightweight systemd user service consuming minimal RAM and CPU cycles.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.14 + FastAPI + Uvicorn
* **System Metrics**: `psutil` + Linux Kernel sysfs
* **Frontend**: HTML5, Tailwind CSS, Jinja2 Templates

---

## 🏃 Local Setup

```bash
# Clone repository
git clone https://github.com/ChaerulHidayat17/nodepulse.git
cd nodepulse

# Create virtual environment & install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run server
uvicorn app:app --host 0.0.0.0 --port 9090
```

Dashboard access: `http://localhost:9090`
