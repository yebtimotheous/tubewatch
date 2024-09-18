import multiprocessing
import time
import logging
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import socket
import os
import uuid
import shutil
import asyncio
from concurrent.futures import ProcessPoolExecutor
import signal

# Constants
CONSENT_BUTTON_XPATH_HOMEPAGE = "//button[@aria-label='Accept all']"
CONSENT_BUTTON_XPATH_VIDEO = "//button[@aria-label='Accept the use of cookies and other data for the purposes described']"
VIDEO_LINKS_CLASS_NAME = "yt-simple-endpoint.ytd-thumbnail"
ADS_BUTTON_SELECTOR = "button.ytp-ad-skip-button"
MUTE_BUTTON_CLASS = "ytp-mute-button"
REPLAY_XPATH = '//*[@title="Replay"]'
PLAYBACK_RATE = 2.0  # Desired playback speed
TIMEOUTS = {
    "consent": 10,
    "ads": 5,
    "mute": 5,
    "replay": 10,
    "page_load": 15,
    "ad_skip": 10,
}
MAX_RETRIES = 3
LOG_FILE = "tubewatch_advanced.log"
VIDEO_PLAY_DURATION = 3600  # Play each video for 1 hour
VIDEO_REPETITIONS = 100  # Number of repetitions per video
NUM_WINDOWS = 5  # Number of concurrent windows
PROFILES_DIR = "profiles_advanced"
CLEANUP_PROFILES = False

# Suppress urllib3 warnings related to SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class YouTubeAutoPlayer:
    def __init__(self, link, headless=False):
        self.link = link
        self.headless = headless
        self.driver = None
        self.profile_path = None

    def setup_logging(self):
        """Configure logging for the script."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def find_free_port(self):
        """Find a free port on the host machine."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def ensure_profiles_dir(self):
        """Ensure that the profiles directory exists."""
        if not os.path.exists(PROFILES_DIR):
            os.makedirs(PROFILES_DIR)
            logging.info(f"Created profiles directory at {os.path.abspath(PROFILES_DIR)}")
        else:
            logging.info(f"Profiles directory exists at {os.path.abspath(PROFILES_DIR)}")

    def init_driver(self, window_size=(1280, 720)):
        """Initialize and return a Selenium WebDriver with a unique user profile."""
        chrome_options = Options()
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        # Additional options to improve stability
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Ensure profiles directory exists
        self.ensure_profiles_dir()

        # Generate a unique profile directory using UUID
        profile_id = uuid.uuid4()
        self.profile_path = os.path.join(PROFILES_DIR, f"chrome_profile_{profile_id}")
        chrome_options.add_argument(f"user-data-dir={self.profile_path}")

        # Unique port for each instance
        free_port = self.find_free_port()
        service = Service(ChromeDriverManager().install(), port=free_port)

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info(f"WebDriver initialized successfully on port {free_port} with profile {self.profile_path}")
        except WebDriverException as e:
            logging.error(f"Error initializing WebDriver on port {free_port}: {e}")
            self.driver = None

    def close_driver(self):
        """Close the WebDriver and clean up profiles if necessary."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed successfully.")
                if CLEANUP_PROFILES and self.profile_path and os.path.exists(self.profile_path):
                    shutil.rmtree(self.profile_path)
                    logging.info(f"Removed profile directory: {self.profile_path}")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")

    def click_element(self, by, identifier, timeout=10):
        """Click an element specified by the locator strategy."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, identifier))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element)
            time.sleep(0.5)
            element.click()
            logging.info(f"Clicked element: {identifier}")
            return True
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            logging.warning(f"Element not found or not clickable: {identifier}. Exception: {e}")
            # Attempt to click via JavaScript
            try:
                element = self.driver.find_element(by, identifier)
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f"Clicked element via JavaScript: {identifier}")
                return True
            except Exception as js_e:
                logging.error(f"Failed to click element via JavaScript: {identifier}. Exception: {js_e}")
                return False

    def set_playback_rate(self):
        """Set and continuously maintain the video playback rate."""
        script = f"""
        function setPlaybackRate() {{
            var video = document.querySelector('video');
            if (video && video.playbackRate !== {PLAYBACK_RATE}) {{
                video.playbackRate = {PLAYBACK_RATE};
            }}
        }}
        setPlaybackRate();
        setInterval(setPlaybackRate, 1000);
        """
        self.driver.execute_script(script)
        logging.info(f"Set playback rate to {PLAYBACK_RATE}x.")

    def enable_looping(self):
        """Enable video looping."""
        try:
            self.driver.execute_script("""
                var video = document.querySelector('video');
                if (video) {
                    video.loop = true;
                }
            """)
            logging.info("Enabled video looping.")
        except WebDriverException as e:
            logging.error(f"Failed to enable looping: {e}")

    def set_video_quality(self, quality='360p'):
        """Set the video quality to the specified resolution."""
        try:
            logging.info(f"Setting video quality to {quality}.")
            settings_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-settings-button"))
            )
            settings_button.click()
            time.sleep(1)

            quality_menu = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ytp-menuitem') and contains(text(), 'Quality')]"))
            )
            quality_menu.click()
            time.sleep(1)

            desired_quality = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{quality}')]")
            desired_quality.click()
            logging.info(f"Video quality set to {quality}.")
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Failed to set video quality to {quality}: {e}")

    def mute_video(self):
        """Mute the video."""
        try:
            mute_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-mute-button"))
            )
            if 'muted' not in mute_button.get_attribute('aria-label').lower():
                mute_button.click()
                logging.info("Video muted.")
            else:
                logging.info("Video is already muted.")
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Failed to mute video: {e}")

    def skip_ads(self):
        """Attempt to skip ads using multiple strategies."""
        try:
            wait = WebDriverWait(self.driver, TIMEOUTS['ad_skip'])

            # Strategy 1: Click 'Skip Ads' button
            try:
                skip_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ytp-ad-skip-button') or contains(text(), 'Skip Ads')]"))
                )
                skip_button.click()
                logging.info("Skipped ad using 'Skip Ads' button.")
                return
            except (NoSuchElementException, TimeoutException):
                logging.debug("'Skip Ads' button not found.")

            # Strategy 2: Click ad overlay close button
            try:
                close_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Close') and contains(@class, 'ytp-ad-overlay-close-button')]"))
                )
                close_button.click()
                logging.info("Closed ad overlay using close button.")
                return
            except (NoSuchElementException, TimeoutException):
                logging.debug("Ad overlay close button not found.")

            # Strategy 3: Press 'Escape' key
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                logging.info("Attempted to skip ad by sending 'Escape' key.")
                return
            except Exception as e:
                logging.warning(f"Failed to skip ad using 'Escape' key: {e}")

            # Strategy 4: Hide ad elements via JavaScript
            try:
                self.driver.execute_script("""
                    var adElements = document.querySelectorAll('.ytp-ad-player-overlay, .video-ads .ad-container');
                    adElements.forEach(function(element) {
                        element.style.display = 'none';
                    });
                """)
                logging.info("Hid ad elements using JavaScript.")
            except Exception as e:
                logging.error(f"Failed to hide ad elements: {e}")

        except Exception as e:
            logging.error(f"Unexpected error while skipping ads: {e}", exc_info=True)

    def ensure_video_playing(self):
        """Ensure the video is playing and handle ads if detected."""
        try:
            is_playing = self.driver.execute_script("""
                return !document.querySelector('.ad-showing');
            """)
            if not is_playing:
                logging.info("Ad detected. Attempting to skip.")
                self.skip_ads()
                time.sleep(2)
            else:
                logging.debug("Video is playing normally.")
        except Exception as e:
            logging.error(f"Error while ensuring video is playing: {e}", exc_info=True)

    def process_video(self):
        """Process the video playback."""
        try:
            self.driver.get(self.link)
            WebDriverWait(self.driver, TIMEOUTS["page_load"]).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            logging.info(f"Navigated to video: {self.link}")

            # Handle consent on video page
            self.click_element(By.XPATH, CONSENT_BUTTON_XPATH_VIDEO, TIMEOUTS["consent"])

            # Set video quality, mute, and playback rate
            self.set_video_quality('360p')
            self.mute_video()
            self.set_playback_rate()
            self.enable_looping()

            # Play the video for the desired duration
            logging.info(f"Starting video playback for {VIDEO_PLAY_DURATION} seconds with looping enabled.")
            start_time = time.time()
            while time.time() - start_time < VIDEO_PLAY_DURATION:
                self.ensure_video_playing()
                time.sleep(5)  # Check playback status periodically

            logging.info(f"Finished playing video for {VIDEO_PLAY_DURATION} seconds.")

        except Exception as e:
            logging.error(f"Error processing video {self.link}: {e}", exc_info=True)
        finally:
            self.close_driver()

    def run(self):
        """Run the video processing."""
        self.setup_logging()
        for attempt in range(MAX_RETRIES):
            try:
                self.init_driver()
                if not self.driver:
                    logging.error("Driver initialization failed. Retrying...")
                    time.sleep(2)
                    continue
                self.process_video()
                break
            except Exception as e:
                logging.error(f"Exception during video processing: {e}", exc_info=True)
                logging.info(f"Retrying video '{self.link}' (Attempt {attempt + 2}/{MAX_RETRIES})...")
                time.sleep(5)
            finally:
                self.close_driver()
        else:
            logging.critical(f"Failed to process video '{self.link}' after {MAX_RETRIES} attempts.")


def setup_logging():
    """Configure logging for the main process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )


def find_free_port():
    """Find a free port on the host machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def ensure_profiles_dir():
    """Ensure that the profiles directory exists."""
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)
        logging.info(f"Created profiles directory at {os.path.abspath(PROFILES_DIR)}")
    else:
        logging.info(f"Profiles directory exists at {os.path.abspath(PROFILES_DIR)}")


def get_video_links():
    """Retrieve video links based on user input."""
    choice = input("Enter '1' for channel URL or '2' for direct video URL: ").strip()
    
    if choice == '1':
        channel_url = input("Please provide channel URL: ").strip()
        return get_channel_links(channel_url)
    elif choice == '2':
        video_url = input("Please provide direct video URL: ").strip()
        return [video_url]
    else:
        logging.error("Invalid choice. Please run the script again.")
        return []


def get_channel_links(channel_url):
    """Retrieve all video links from the specified YouTube channel."""
    player = YouTubeAutoPlayer(channel_url)
    player.init_driver()
    if not player.driver:
        return []

    try:
        logging.info(f"Navigating to channel URL: {channel_url}")
        player.driver.get(channel_url)
        WebDriverWait(player.driver, TIMEOUTS["page_load"]).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Channel page loaded successfully.")

        # Handle consent on homepage
        player.click_element(By.XPATH, CONSENT_BUTTON_XPATH_HOMEPAGE, TIMEOUTS["consent"])

        # Scroll to load videos
        scroll_to_load_videos(player.driver)

        # Extract video links
        link_elements = player.driver.find_elements(By.CLASS_NAME, VIDEO_LINKS_CLASS_NAME)
        links = list(set([
            elem.get_attribute("href")
            for elem in link_elements
            if elem.get_attribute("href") and "/watch?v=" in elem.get_attribute("href")
        ]))
        logging.info(f"Found {len(links)} unique video links.")
        return links
    except Exception as e:
        logging.error(f"Error retrieving channel links: {e}")
        return []
    finally:
        player.close_driver()


def scroll_to_load_videos(driver, scroll_pause_time=2, max_scrolls=10):
    """Scroll the channel page to load more videos."""
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    for scroll in range(max_scrolls):
        logging.info(f"Scrolling {scroll + 1}/{max_scrolls} to load more videos.")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            logging.info("No more videos to load.")
            break
        last_height = new_height


def distribute_links(links, num_windows):
    """Distribute video links among the specified number of windows."""
    return [links[i::num_windows] for i in range(num_windows)]


def run_window(links):
    """Run a single window, processing multiple links sequentially."""
    for link in links:
        player = YouTubeAutoPlayer(link, headless=False)
        player.run()


def main():
    """Main function to orchestrate video playback on multiple windows."""
    setup_logging()
    logging.info("Script started.")

    all_links = get_video_links()
    if not all_links:
        logging.error("No links to process. Exiting.")
        return

    links_per_window = distribute_links(all_links, NUM_WINDOWS)
    processes = []

    with ProcessPoolExecutor(max_workers=NUM_WINDOWS) as executor:
        for window_links in links_per_window:
            if window_links:
                executor.submit(run_window, window_links)

    if CLEANUP_PROFILES:
        try:
            shutil.rmtree(PROFILES_DIR)
            logging.info(f"Cleaned up all profiles in {PROFILES_DIR}")
        except Exception as e:
            logging.error(f"Error cleaning up profiles directory: {e}")

    logging.info("Finished processing videos on all windows.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Script interrupted by user. Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)