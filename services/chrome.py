import time
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# ==========================================================
# ORION CHROME CONFIG
# ==========================================================

CHROME_PROFILE = r"C:\Users\prach\OneDrive\Desktop\orion v1.0\orion\orion_chrome_profile"

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

DEBUG_PORT = 9222


class ChromeService:

    def __init__(self):
        self.driver = None
        self.chrome_process = None

    # ======================================================
    # CREATE CHROME
    # ======================================================

    def create_driver(self):

        print("Starting Orion Chrome...")

        # Start Chrome with Orion's dedicated profile
        self.chrome_process = subprocess.Popen([
            CHROME_EXE,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={CHROME_PROFILE}",
            "--disable-notifications",
            "--start-maximized",
            "--no-first-run",
            "--no-default-browser-check",
            "--remote-allow-origins=*"
        ])

        print("Chrome process started.")

        # Give Chrome time to start
        time.sleep(3)

        # ==================================================
        # CONNECT SELENIUM
        # ==================================================

        options = Options()

        options.add_experimental_option(
            "debuggerAddress",
            f"127.0.0.1:{DEBUG_PORT}"
        )

        try:

            self.driver = webdriver.Chrome(options=options)

            print("Selenium connected to Chrome.")

            # Open YouTube
            self.driver.get("https://www.youtube.com")

            time.sleep(2)

            print("Chrome ready.")

            return self.driver

        except Exception as e:

            print("Chrome connection error:", e)

            self.driver = None

            return None

    # ======================================================
    # CHECK CHROME / SELENIUM SESSION
    # ======================================================

    def is_alive(self):

        try:

            if self.driver is None:
                return False

            self.driver.current_url

            return True

        except Exception:

            return False

    # ======================================================
    # CLOSE CHROME COMPLETELY
    # ======================================================

    def stop(self):

        print("Stopping Orion Chrome...")

        # Close Selenium session
        try:

            if self.driver is not None:
                self.driver.quit()

        except Exception:
            pass

        self.driver = None

        # Stop Chrome process started by Orion
        try:

            if self.chrome_process is not None:

                if self.chrome_process.poll() is None:

                    self.chrome_process.terminate()

                    try:
                        self.chrome_process.wait(timeout=3)

                    except subprocess.TimeoutExpired:
                        self.chrome_process.kill()

                self.chrome_process = None

        except Exception as e:

            print("Chrome process cleanup error:", e)

        time.sleep(2)

    # ======================================================
    # RESTART CHROME
    # ======================================================

    def restart(self):

        print("Restarting Chrome session...")

        # Close old Chrome
        self.stop()

        time.sleep(2)

        # Start new Chrome
        return self.create_driver()