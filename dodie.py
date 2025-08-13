import os
import sys
import time
import random
import subprocess
from typing import List, Optional
from dataclasses import dataclass, field

import requests
from seleniumbase import SB

# --- Data Classes for Future Extensibility --- #
@dataclass
class StreamStatus:
    username: str
    is_online: bool = False
    checked_at: float = field(default_factory=time.time)
    source: str = "twitch"

@dataclass
class WebDriverTracker:
    drivers: List = field(default_factory=list)
    active_idx: Optional[int] = None

    def register(self, driver):
        self.drivers.append(driver)
        self.active_idx = len(self.drivers) - 1

    def quit_all(self):
        for drv in self.drivers:
            try:
                drv.quit()
            except Exception as e:
                print(f"Warning: Failed to quit driver: {e}")

# --- Utility Functions --- #
def random_delay(a=1, b=4):
    sleep_time = random.uniform(a, b)
    print(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)

def is_stream_online(username: str) -> bool:
    """
    Returns True if the Twitch stream is online, False otherwise.
    Uses the public frontend Client-ID (no OAuth).
    """
    url = f"https://www.twitch.tv/{username}"
    headers = {
        "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",  # Publicly known Client-ID
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        online = "isLiveBroadcast" in resp.text
        print(f"[{username}] Stream online status: {online}")
        return online
    except Exception as e:
        print(f"Error checking stream status: {e}")
        return False

def handle_accept_popup(driver, reconnect_time=4):
    if driver.is_element_present('button:contains("Accept")'):
        print("Accept button found, clicking...")
        driver.uc_click('button:contains("Accept")', reconnect_time=reconnect_time)
    else:
        print("No Accept button found.")

def handle_captcha(driver):
    print("Handling captcha interaction...")
    driver.uc_gui_click_captcha()
    random_delay(1, 2)
    driver.uc_gui_handle_captcha()
    random_delay(2, 4)

def open_and_prepare_page(driver, url, reconnect_time=4):
    print(f"Opening page: {url}")
    driver.uc_open_with_reconnect(url, reconnect_time)
    random_delay(2, 5)
    handle_captcha(driver)
    random_delay(1, 2)
    handle_accept_popup(driver, reconnect_time)

def monitor_kick_and_switch_to_twitch(main_driver, username, tracker: WebDriverTracker):
    kick_url = f"https://kick.com/{username}"
    twitch_url = f"https://www.twitch.tv/{username}"

    open_and_prepare_page(main_driver, kick_url, reconnect_time=4)

    if main_driver.is_element_visible('#injected-channel-player'):
        print("Channel player found, launching secondary driver...")
        secondary_driver = main_driver.get_new_driver(undetectable=True)
        tracker.register(secondary_driver)
        open_and_prepare_page(secondary_driver, kick_url, reconnect_time=5)
        random_delay(9, 11)
        while main_driver.is_element_visible('#injected-channel-player'):
            print("Channel player still visible, monitoring...")
            random_delay(9, 11)
        try:
            main_driver.quit_extra_driver()
        except Exception as e:
            print(f"Error quitting extra driver: {e}")

    random_delay(1, 2)

    if is_stream_online(username):
        print("Switching to Twitch, stream is online!")
        open_and_prepare_page(main_driver, twitch_url, reconnect_time=5)
        secondary_driver = main_driver.get_new_driver(undetectable=True)
        tracker.register(secondary_driver)
        open_and_prepare_page(secondary_driver, twitch_url, reconnect_time=5)
        random_delay(9, 11)
        # Wait for some element (simulate monitoring)
        # Here 'input_field' is not defined, so we simply sleep a few times to simulate.
        for _ in range(2):
            print("Monitoring Twitch driver for input field...")
            random_delay(9, 11)
        try:
            main_driver.quit_extra_driver()
        except Exception as e:
            print(f"Error quitting extra driver: {e}")

    random_delay(1, 2)

# --- Main Script Execution --- #
if __name__ == "__main__":
    username = "brutalles"
    tracker = WebDriverTracker()
    with SB(uc=True, test=True) as main_driver:
        tracker.register(main_driver)
        monitor_kick_and_switch_to_twitch(main_driver, username, tracker)
        tracker.quit_all()
