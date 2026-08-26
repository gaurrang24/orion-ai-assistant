import time


class YouTubeAdTool:

    def __init__(self, driver):
        self.driver = driver

    def skip_ad(self):
        try:
            # YouTube skip button
            selectors = [
                ".ytp-ad-skip-button",
                ".ytp-ad-skip-button-modern",
                ".ytp-ad-skip-button-container button",
            ]

            for selector in selectors:
                try:
                    buttons = self.driver.find_elements("css selector", selector)

                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            print("Orion: YouTube ad skipped.")
                            return True

                except Exception:
                    continue

            print("Orion: No skippable ad found.")
            return False

        except Exception as e:
            print(f"Skip Ad Error: {e}")
            return False