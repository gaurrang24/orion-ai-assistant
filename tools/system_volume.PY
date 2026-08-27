from pycaw.pycaw import AudioUtilities


def _get_volume_interface():
    devices = AudioUtilities.GetSpeakers()

    # Newer pycaw versions
    if hasattr(devices, "EndpointVolume"):
        return devices.EndpointVolume

    # Older pycaw versions
    interface = devices._dev.Activate(
        devices._iid_,
        23,
        None
    )

    return interface


def set_system_volume(level):
    """Set Windows master volume from 0.0 to 1.0."""

    level = max(0.0, min(1.0, float(level)))

    volume = _get_volume_interface()
    volume.SetMasterVolumeLevelScalar(level, None)


def volume_up(step=0.1):
    """Increase system volume by 10%."""

    volume = _get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()
    new_volume = min(current + step, 1.0)

    volume.SetMasterVolumeLevelScalar(new_volume, None)


def volume_down(step=0.1):
    """Decrease system volume by 10%."""

    volume = _get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()
    new_volume = max(current - step, 0.0)

    volume.SetMasterVolumeLevelScalar(new_volume, None)