import winreg
import psutil
import wmi
import re
import subprocess

from utils import cli_error


UNKNOWN = "unknown"


# ---------- CPU ----------
def get_cpu_info():
    try:
        c = wmi.WMI()
        cpu_name = c.Win32_Processor()[0].Name.strip()
        cpu_name = re.sub(r"\s+@\s+[\d\.]+GHz?", "", cpu_name, flags=re.IGNORECASE)
        cpu_name = re.sub(r"\((R|TM|C)\)", "", cpu_name, flags=re.IGNORECASE)
        cpu_name = re.sub(r"\s+", " ", cpu_name).strip()
        return cpu_name or UNKNOWN
    except Exception as e:
        cli_error(f"CPU error: {e}")
        return UNKNOWN


# ---------- GPU ----------
def get_gpu_info():
    try:
        c = wmi.WMI()
        gpus = c.Win32_VideoController()
        if not gpus:
            return UNKNOWN

        def safe_name(gpu):
            return (getattr(gpu, "Name", None) or "").strip()

        valid_gpus = [g for g in gpus if safe_name(g)]
        if not valid_gpus:
            return UNKNOWN

        nvidia = [g for g in valid_gpus if "nvidia" in safe_name(g).lower()]
        amd = [g for g in valid_gpus if any(x in safe_name(g).lower() for x in ("amd", "radeon", "ati"))]
        intel = [g for g in valid_gpus if "intel" in safe_name(g).lower()]

        if nvidia:
            return safe_name(nvidia[0])
        if amd:
            return safe_name(amd[0])
        if intel:
            intel_name = safe_name(intel[0]).lower()
            if "microsoft basic display" not in intel_name:
                return safe_name(intel[0])

        for g in valid_gpus:
            name = safe_name(g).lower()
            if "microsoft basic display" not in name:
                return safe_name(g)

        return safe_name(valid_gpus[0]) or UNKNOWN
    except Exception as e:
        cli_error(f"GPU error: {e}")
        return UNKNOWN


# ---------- RAM ----------
def get_ram_info():
    try:
        mem_bytes = psutil.virtual_memory().total
        mem_gb = mem_bytes / (1024 ** 3)
        return {
            "value_gb": round(mem_gb, 2),
            "total_bytes": int(mem_bytes),
        }
    except Exception as e:
        cli_error(f"RAM error: {e}")
        return {"value_gb": 0.0, "total_bytes": 0}


# ---------- Disk type ----------
def get_disk_type(drive_letter="C:"):
    """Returns 'SSD', 'HDD' or 'unknown'."""
    try:
        ps_cmd = f"""
        try {{
            $letter = '{drive_letter[0]}'
            $disk = Get-Partition -DriveLetter $letter -ErrorAction Stop | Get-Disk -ErrorAction Stop
            $mt = $disk.MediaType
            if ($mt -eq 4) {{ 'SSD' }}
            elseif ($mt -eq 3 -or $mt -eq 0) {{ 'HDD' }}
            else {{
                $pd = Get-PhysicalDisk | Where-Object {{ $_.DeviceID -eq $disk.Number }}
                if ($pd.MediaType -eq 'SSD') {{ 'SSD' }}
                elseif ($pd.MediaType -eq 'HDD') {{ 'HDD' }}
                else {{ 'unknown' }}
            }}
        }} catch {{ 'unknown' }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=8,
        )
        if result.returncode == 0:
            out = result.stdout.strip()
            if out in ("SSD", "HDD"):
                return out
    except Exception as e:
        cli_error(f"PowerShell disk type error: {e}")

    try:
        c = wmi.WMI()
        logical = c.Win32_LogicalDisk(DeviceID=drive_letter)
        if not logical:
            return UNKNOWN
        partition = logical[0].associators(wmi_result_class="Win32_DiskPartition")
        if not partition:
            return UNKNOWN
        disk = partition[0].associators(wmi_result_class="Win32_DiskDrive")
        if not disk:
            return UNKNOWN
        model = (disk[0].Model or "").lower()
        if any(k in model for k in ["ssd", "nvme", "solid state", "m.2", "pcie"]):
            return "SSD"
        return UNKNOWN
    except Exception as e:
        cli_error(f"WMI disk error: {e}")
        return UNKNOWN


# ---------- Disk ----------
def get_disk_info(drive_letter="C:"):
    try:
        usage = psutil.disk_usage(drive_letter)
        total_gb = usage.total / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_percent = (usage.free / usage.total) * 100 if usage.total else 0.0
        used_percent = (usage.used / usage.total) * 100 if usage.total else 0.0
        disk_type = get_disk_type(drive_letter)
        return {
            "drive_letter": drive_letter,
            "type": disk_type,
            "total_gb": round(total_gb, 2),
            "free_gb": round(free_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_percent": round(free_percent, 1),
            "used_percent": round(used_percent, 1),
            "total_bytes": int(usage.total),
            "free_bytes": int(usage.free),
            "used_bytes": int(usage.used),
        }
    except Exception as e:
        cli_error(f"Disk error: {e}")
        return {
            "drive_letter": drive_letter, "type": UNKNOWN,
            "total_gb": 0.0, "free_gb": 0.0, "used_gb": 0.0,
            "free_percent": 0.0, "used_percent": 0.0,
            "total_bytes": 0, "free_bytes": 0, "used_bytes": 0,
        }


# ---------- Windows ----------
def get_windows_info():
    try:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            product = winreg.QueryValueEx(key, "ProductName")[0]
            build = winreg.QueryValueEx(key, "CurrentBuild")[0]
            try:
                display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            except FileNotFoundError:
                try:
                    display_version = winreg.QueryValueEx(key, "ReleaseId")[0]
                except FileNotFoundError:
                    display_version = None
        if int(build) >= 22000 and product.startswith("Windows 10"):
            product = product.replace("Windows 10", "Windows 11", 1)
        return {
            "product_name": product or UNKNOWN,
            "display_version": display_version,
            "build": build,
            "full_name": f"{product} {display_version}".strip() if display_version else (product or UNKNOWN),
        }
    except Exception as e:
        cli_error(f"Windows error: {e}")
        return {"product_name": UNKNOWN, "display_version": None, "build": None, "full_name": UNKNOWN}


# ---------- Power plan ----------
def get_power_plan_info():
    """
    Имя плана из WMI (на языке Windows) + GUID схемы из InstanceID (языконезависимо).
    GUID извлекается из InstanceID (стандартная схема Microsoft:PowerPlan + идентификатор в фигурных скобках).
    """
    try:
        c = wmi.WMI(namespace=r"root\cimv2\power")
        plan = c.Win32_PowerPlan(IsActive=True)
        if not plan:
            return UNKNOWN, ""
        p = plan[0]
        name = (getattr(p, "ElementName", None) or "").strip() or UNKNOWN
        iid = (getattr(p, "InstanceID", None) or "").strip()
        guid = ""
        m = re.search(r"\{([a-fA-F0-9-]+)\}", iid)
        if m:
            guid = m.group(1).lower()
        return name, guid
    except Exception as e:
        cli_error(f"Power plan error: {e}")
        return UNKNOWN, ""


def get_power_plan():
    """Локализованное имя от Windows (для совместимости и LLM-контекста)."""
    name, _ = get_power_plan_info()
    return name


# ---------- Startup apps ----------
def get_startup_apps():
    try:
        c = wmi.WMI()
        items = c.Win32_StartupCommand()
        return {"count": len(items)}
    except Exception as e:
        cli_error(f"Startup error: {e}")
        return {"count": 0}


# ---------- Full system snapshot ----------
def get_system_snapshot():
    ram = get_ram_info()
    disk = get_disk_info()
    startup = get_startup_apps()
    windows = get_windows_info()

    disk_type = disk["type"]
    ram_gb = ram["value_gb"]
    startup_count = startup["count"]
    power_name, power_guid = get_power_plan_info()

    return {
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),

        "ram_gb": ram_gb,
        "ram_total_bytes": ram["total_bytes"],

        "disk_system_letter": disk["drive_letter"],
        "disk_type": disk_type,
        "disk_total_gb": disk["total_gb"],
        "disk_free_gb": disk["free_gb"],
        "disk_used_gb": disk["used_gb"],
        "disk_free_percent": disk["free_percent"],
        "disk_used_percent": disk["used_percent"],
        "disk_total_bytes": disk["total_bytes"],
        "disk_free_bytes": disk["free_bytes"],
        "disk_used_bytes": disk["used_bytes"],

        "is_hdd": disk_type == "HDD",
        "is_ssd": disk_type == "SSD",
        "is_low_disk_space": disk["free_percent"] < 10.0,
        "is_low_ram": ram_gb < 8.0,

        "windows_product_name": windows["product_name"],
        "windows_display_version": windows["display_version"],
        "windows_build": windows["build"],
        "windows_full_name": windows["full_name"],

        "power_plan": power_name,
        "power_plan_guid": power_guid,

        "startup_apps_count": startup_count,
        "is_startup_heavy": startup_count >= 8,
    }


if __name__ == "__main__":
    snapshot = get_system_snapshot()
    for key, value in snapshot.items():
        print(f"{key}: {value}")
