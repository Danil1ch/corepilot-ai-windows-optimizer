"""
CorePilot Recommendation Engine
Rule-based, без Qwen. Принимает system snapshot + actions + applied,
возвращает recommended / neutral / caution.
"""

from typing import Dict, List


def is_nvidia_gpu(system_data: Dict) -> bool:
    gpu = (system_data.get("gpu") or "").lower()
    return "nvidia" in gpu or "geforce" in gpu or "rtx" in gpu or "gtx" in gpu


def is_amd_gpu(system_data: Dict) -> bool:
    gpu = (system_data.get("gpu") or "").lower()
    return "amd" in gpu or "radeon" in gpu


def is_integrated_gpu(system_data: Dict) -> bool:
    gpu = (system_data.get("gpu") or "").lower()
    if not gpu or gpu == "unknown":
        return True
    return "intel" in gpu and not any(x in gpu for x in ["arc", "xe"])


def is_powerful_pc(system_data: Dict) -> bool:
    return (
        system_data.get("ram_gb", 0) >= 16
        and system_data.get("is_ssd", False)
        and not is_integrated_gpu(system_data)
    )


def get_recommendations(
    system_data: Dict,
    actions: List[Dict],
    applied_ids: List[str]
) -> Dict[str, List[Dict]]:
    """
    Возвращает:
    {
        "recommended": [{"id": ..., "score": ..., "reason_tags": [...], ...action_fields}],
        "neutral":      [...],
        "caution":      [...]
    }
    """
    applied = set(applied_ids)

    startup_count = system_data.get("startup_apps_count", 0) or 0
    disk_free_pct = system_data.get("disk_free_percent", 100) or 100
    is_hdd        = system_data.get("is_hdd", False)
    is_ssd        = system_data.get("is_ssd", False)
    power_plan    = (system_data.get("power_plan") or "").lower()
    power_guid    = (system_data.get("power_plan_guid") or "").lower()
    ram_gb        = system_data.get("ram_gb", 16) or 16

    nvidia    = is_nvidia_gpu(system_data)
    amd       = is_amd_gpu(system_data)
    integrated = is_integrated_gpu(system_data)
    powerful  = is_powerful_pc(system_data)

    rules: Dict[str, List] = {}

    def add_rule(action_id: str, delta: int, tag: str):
        rules.setdefault(action_id, []).append((delta, tag))

    # --- Автозагрузка ---
    if startup_count >= 12:
        add_rule("recommend_startup_cleanup", +6, "startup_critical")
    elif startup_count >= 8:
        add_rule("recommend_startup_cleanup", +4, "startup_heavy")
    elif startup_count <= 3:
        add_rule("recommend_startup_cleanup", -3, "startup_light")

    # --- Место на диске ---
    if disk_free_pct < 10:
        add_rule("clean_temp",    +6, "very_low_disk")
        add_rule("clean_winsxs", +5, "very_low_disk")
        add_rule("compact_os",   +4, "very_low_disk")
        add_rule("hibernate_off",+4, "very_low_disk")
    elif disk_free_pct < 15:
        add_rule("clean_temp",    +4, "low_disk_space")
        add_rule("clean_winsxs", +3, "low_disk_space")
        add_rule("compact_os",   +2, "low_disk_space")
        add_rule("hibernate_off",+2, "low_disk_space")
    elif disk_free_pct > 25:
        add_rule("clean_winsxs", -1, "disk_ok")
        add_rule("compact_os",   -1, "disk_ok")

    # --- HDD ---
    if is_hdd:
        add_rule("disable_sysmain",      +3, "hdd_detected")
        add_rule("disable_search_index", +3, "hdd_detected")
        add_rule("optimize_ntfs",        +2, "hdd_detected")

    # --- SSD ---
    if is_ssd:
        add_rule("disable_sysmain",      -2, "ssd_detected")
        add_rule("disable_search_index", -1, "ssd_detected")

    # --- План питания (GUID не зависит от языка ОС; строка — запасной вариант) ---
    _max_guids = (
        "e9a42b02-d5df-448d-aa00-03f14749eb61",  # Ultimate
        "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",  # High performance
    )
    _bal_guid = "381b4222-f694-41f0-9685-ff5bb260df2e"
    if power_guid in _max_guids or (
        "максимальная" in power_plan
        or "ultimate" in power_plan
        or "high performance" in power_plan
        or "высокая производительность" in power_plan
    ):
        add_rule("power_max",      -5, "already_max_power")
        add_rule("power_balanced", +1, "already_max_power")
    elif power_guid == _bal_guid or "сбалансир" in power_plan or "balanced" in power_plan:
        add_rule("power_balanced", -5, "already_balanced_power")
        add_rule("power_max",      +1, "already_balanced_power")

    # --- Мало RAM ---
    if ram_gb < 8:
        add_rule("disable_sysmain",         +2, "low_ram")
        add_rule("optimize_visual_effects", +2, "low_ram")
        add_rule("optimize_visual_hybrid",  +2, "low_ram")

    # --- GPU: NVIDIA ---
    if nvidia:
        add_rule("clear_shader_cache", +3, "nvidia_gpu")
        add_rule("gpu_pref_high",      +2, "nvidia_gpu")

    # --- GPU: AMD ---
    if amd:
        add_rule("clear_shader_cache", -2, "amd_gpu")

    # --- GPU: Integrated ---
    if integrated:
        add_rule("gpu_pref_high",           -2, "integrated_gpu")
        add_rule("optimize_visual_effects", +2, "integrated_gpu")
        add_rule("optimize_visual_hybrid",  +2, "integrated_gpu")

    # --- Дискретная GPU → gaming tweaks ---
    if not integrated:
        add_rule("game_mode_on",  +2, "discrete_gpu")
        add_rule("gpu_pref_high", +2, "discrete_gpu")

    # --- Мощный ПК → не тащить visual tweaks ---
    if powerful:
        add_rule("optimize_visual_effects", -2, "powerful_pc")
        add_rule("optimize_visual_hybrid",  -1, "powerful_pc")

    BASE_SCORE = 5

    recommended = []
    neutral     = []
    caution     = []

    for action in actions:
        action_id  = action.get("id", "")
        risk_level = action.get("risk_level", "low")

        if action_id in applied:
            continue

        score = BASE_SCORE
        reason_tags = []
        for delta, tag in rules.get(action_id, []):
            score += delta
            if tag not in reason_tags:
                reason_tags.append(tag)

        scored = {**action, "score": score, "reason_tags": reason_tags}

        if risk_level == "high":
            caution.append(scored)
            continue

        if score >= 7:
            recommended.append(scored)
        else:
            neutral.append(scored)

    recommended.sort(key=lambda x: x["score"], reverse=True)
    neutral.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommended": recommended,
        "neutral":     neutral,
        "caution":     caution,
    }
