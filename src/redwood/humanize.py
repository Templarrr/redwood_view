_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]


def human_size(size: int) -> str:
    value = float(size)
    for unit in _UNITS:
        if value < 1024 or unit == _UNITS[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)} B"
    return f"{value:.1f} {unit}"
