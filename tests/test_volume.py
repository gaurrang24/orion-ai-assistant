from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

sessions = AudioUtilities.GetAllSessions()
for session in sessions:
    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
    print("Current volume:", volume.GetMasterVolume())
    volume.SetMasterVolume(0.5, None)  # set to 50%
