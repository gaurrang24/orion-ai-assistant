import time
import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class YouTubeTool:

    def __init__(self, chrome):
        self.chrome = chrome

    @property
    def driver(self):
        return self.chrome.driver

    def driver_is_alive(self):
        return self.chrome.is_alive()

    def driver_is_alive(self):
        try:
            self.driver.current_url
            return True
        except Exception:
            return False

    def play(self, song):
        print(f"Playing: {song}")

        if not self.driver_is_alive():
            print("Chrome session is not available.")
            return False

        try:
            search_url = (
                "https://www.youtube.com/results?search_query="
                + urllib.parse.quote(song)
            )

            print("Searching YouTube...")
            self.driver.get(search_url)

            wait = WebDriverWait(self.driver, 10)

            first_video = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
                )
            )

            self.driver.execute_script(
                "arguments[0].click();",
                first_video
            )

            print("Song opened successfully.")
            time.sleep(2)

            return True

        except Exception as e:
            print("YouTube play error:", e)
            return False

    def pause(self):
        if not self.driver_is_alive():
            print("Chrome session is not available.")
            return False

        try:
            result = self.driver.execute_script("""
                const video = document.querySelector('video');

                if (video) {
                    video.pause();
                    return true;
                }

                return false;
            """)

            if result:
                print("Music paused.")
                return True

            print("YouTube video player not found.")
            return False

        except Exception as e:
            print("YouTube pause error:", e)
            return False

    def resume(self):
        if not self.driver_is_alive():
            print("Chrome session is not available.")
            return False

        try:
            result = self.driver.execute_script("""
                const video = document.querySelector('video');

                if (video) {
                    video.play();
                    return true;
                }

                return false;
            """)

            if result:
                print("Music resumed.")
                return True

            print("YouTube video player not found.")
            return False

        except Exception as e:
            print("YouTube resume error:", e)
            return False