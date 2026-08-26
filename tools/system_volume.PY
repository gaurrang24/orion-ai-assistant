from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def _get_volume_interface():

    devices = AudioUtilities.GetSpeakers()

    # New pycaw versions
    if hasattr(devices, "EndpointVolume"):
        return devices.EndpointVolume

    # Older pycaw versions
    interface = devices.Activate(
        IAudioEndpointVolume._iid_,
        None,
        None
    )

    return interface.QueryInterface(IAudioEndpointVolume)


def set_system_volume(level):
    """
    Set Windows master volume.
    level must be between 0.0 and 1.0.
    """

    level = max(0.0, min(1.0, float(level)))

    volume = _get_volume_interface()

    volume.SetMasterVolumeLevelScalar(level, None)


def volume_up(step=0.1):

    volume = _get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    new_volume = min(current + step, 1.0)

    volume.SetMasterVolumeLevelScalar(new_volume, None)


def volume_down(step=0.1):

    volume = _get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    new_volume = max(current - step, 0.0)

    volume.SetMasterVolumeLevelScalar(new_volume, None)
