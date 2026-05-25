"""Resolve configuracao OSD com hierarquia device > tenant > default."""

DEFAULT_OSD_CONFIG = {
    "show_current_audio": True,
    "position": "top_right",
    "duration_seconds": 8,
    "opacity": 0.6,
    "font_size": "medium",
}


def _value(value):
    return value.value if hasattr(value, "value") else value


def resolve_osd_config(device=None, tenant=None) -> dict:
    tenant_config = {
        "show_current_audio": getattr(tenant, "osd_show_current_audio", None),
        "position": _value(getattr(tenant, "osd_position", None)),
        "duration_seconds": getattr(tenant, "osd_duration_seconds", None),
        "opacity": getattr(tenant, "osd_opacity", None),
        "font_size": _value(getattr(tenant, "osd_font_size", None)),
    }
    device_config = {
        "show_current_audio": getattr(device, "osd_show_current_audio", None),
        "position": _value(getattr(device, "osd_position", None)),
        "duration_seconds": getattr(device, "osd_duration_seconds", None),
        "opacity": getattr(device, "osd_opacity", None),
        "font_size": _value(getattr(device, "osd_font_size", None)),
    }

    resolved = {}
    for key, default in DEFAULT_OSD_CONFIG.items():
        value = device_config.get(key)
        if value is None:
            value = tenant_config.get(key)
        if value is None:
            value = default
        if key == "opacity":
            value = float(value)
        resolved[key] = value
    return resolved


def resolve_osd_local(device=None) -> dict:
    opacity = getattr(device, "osd_opacity", None)
    return {
        "show_current_audio": getattr(device, "osd_show_current_audio", None),
        "position": _value(getattr(device, "osd_position", None)),
        "duration_seconds": getattr(device, "osd_duration_seconds", None),
        "opacity": float(opacity) if opacity is not None else None,
        "font_size": _value(getattr(device, "osd_font_size", None)),
    }
