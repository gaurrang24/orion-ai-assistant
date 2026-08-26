from tools import system_volume

print("Setting volume to 50%...")
system_volume.set_system_volume(0.5)

print("Increasing volume...")
system_volume.volume_up()

print("Decreasing volume...")
system_volume.volume_down()
