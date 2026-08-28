import subprocess
from pathlib import Path
from datetime import datetime

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class WindowsControlTool:

    @staticmethod
    def lock():
        subprocess.run(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            check=False
        )

    @staticmethod
    def restart():
        subprocess.run(
            ["shutdown", "/r", "/t", "5"],
            check=False
        )

    @staticmethod
    def shutdown():
        subprocess.run(
            ["shutdown", "/s", "/t", "5"],
            check=False
        )

    @staticmethod
    def sleep():
        subprocess.run(
            [
                "powershell",
                "-Command",
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.Application]::SetSuspendState("
                "'Suspend', $false, $false)"
            ],
            check=False
        )

    @staticmethod
    def screenshot():
        if ImageGrab is None:
            return None

        documents_dir = Path.home() / "Documents" / "Orion Screenshots"
        documents_dir.mkdir(parents=True, exist_ok=True)

        filename = datetime.now().strftime(
            "screenshot_%Y%m%d_%H%M%S.png"
        )

        path = documents_dir / filename

        image = ImageGrab.grab()
        image.save(path)

        return str(path)