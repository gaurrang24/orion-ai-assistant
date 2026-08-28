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

        # If an old Selenium session exists, clean it first
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass

            self.driver = None

        # Start Chrome
        try:

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

        except Exception as e:

            print("Chrome start error:", repr(e))
            return None

        # ==================================================
        # WAIT FOR CHROME
        # ==================================================

        print("Waiting for Chrome...")

        time.sleep(5)

        # ==================================================
        # CONNECT SELENIUM
        # ==================================================

        options = Options()

        options.add_experimental_option(
            "debuggerAddress",
            f"127.0.0.1:{DEBUG_PORT}"
        )

        # Try connection several times
        for attempt in range(5):

            try:

                print(
                    f"Connecting Selenium to Chrome "
                    f"(attempt {attempt + 1}/5)..."
                )

                self.driver = webdriver.Chrome(options=options)

                print("Selenium connected to Chrome.")

                # Test session
                self.driver.title

                print("Chrome Selenium session is alive.")

                # Open YouTube
                self.driver.get("https://www.youtube.com")

                time.sleep(3)

                print("Chrome ready.")

                return self.driver

            except Exception as e:

                print(
                    "Selenium connection failed:",
                    repr(e)
                )

                self.driver = None

                time.sleep(2)

        print("Could not connect Selenium to Chrome.")

        return None

    # ======================================================
    # CHECK CHROME / SELENIUM SESSION
    # ======================================================

    def is_alive(self):

        try:

            if self.driver is None:

                print("Chrome DEBUG: driver is None")

                return False

            # Test Selenium session
            self.driver.title

            print(
                "Chrome DEBUG: Selenium session is alive"
            )

            return True

        except Exception as e:

            print(
                "Chrome DEBUG: Selenium session error:",
                repr(e)
            )

            self.driver = None

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

                        self.chrome_process.wait(
                            timeout=3
                        )

                    except subprocess.TimeoutExpired:

                        self.chrome_process.kill()

                self.chrome_process = None

        except Exception as e:

            print(
                "Chrome process cleanup error:",
                repr(e)
            )

        time.sleep(2)

    # ======================================================
    # RESTART CHROME
    # ======================================================

    def restart(self):

        print("Restarting Chrome session...")

        self.stop()

        time.sleep(2)

        return self.create_driver()