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
import random
import uuid
import shutil

# Constants
CONSENT_BUTTON_XPATH_HOMEPAGE = "//button[@aria-label='Accept all']"
CONSENT_BUTTON_XPATH_VIDEO = "//button[@aria-label='Accept the use of cookies and other data for the purposes described']"
VIDEO_LINKS_CLASS_NAME = "yt-simple-endpoint.ytd-thumbnail"
ADS_BUTTON_SELECTOR = "button.ytp-ad-skip-button"
MUTE_BUTTON_CLASS = "ytp-mute-button"
REPLAY_XPATH = '//*[@title="Replay"]'
PLAYBACK_RATE = 2  # Set to your desired speed (e.g., 1.5, 1.75, or 2)
TIMEOUTS = {
    "consent": 10,
    "ads": 5,
    "mute": 5,
    "replay": 10,
    "page_load": 15,
    "ad_skip": 10,
}
MAX_RETRIES = 3
LOG_FILE = "tubewatch.log"
VIDEO_PLAY_DURATION = 3600  # Play each video for 1 hour (3600 seconds)
VIDEO_REPETITIONS = 100  # Number of times to repeat each video
NUM_WINDOWS = 5  # Number of windows to run simultaneously
PROFILES_DIR = "profiles"  # Directory to store Chrome profiles
CLEANUP_PROFILES = False  # Set to True to remove profiles after execution

# Suppress urllib3 warnings related to SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def setup_logging():
    """Configure logging for the script."""
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


def init_driver(window_size=(800, 600), headless=False):
    """Initialize and return a Selenium WebDriver with a unique user profile."""
    chrome_options = Options()
    chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    if headless:
        chrome_options.add_argument("--headless")
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
    ensure_profiles_dir()

    # Generate a unique profile directory using UUID
    profile_id = uuid.uuid4()
    profile_path = os.path.join(PROFILES_DIR, f"chrome_profile_{profile_id}")
    chrome_options.add_argument(f"user-data-dir={profile_path}")

    # Unique port for each instance
    free_port = find_free_port()
    service = Service(ChromeDriverManager().install(), port=free_port)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info(f"WebDriver initialized successfully on port {free_port} with profile {profile_path}")
        return driver, profile_path
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver on port {free_port}: {e}")
        return None, None


def click_element(driver, by, identifier, timeout=10):
    """
    Clicks an element specified by the locator strategy.
    Attempts to handle elements that are not immediately clickable.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, identifier))
        )
        # Scroll to the element to ensure it's in view
        driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element)
        time.sleep(0.5)  # Brief pause to allow any animations to complete
        element.click()
        logging.info(f"Clicked element: {identifier}")
        return True
    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
        logging.warning(f"Element not found or not clickable: {identifier}. Exception: {e}")
        # Attempt to click via JavaScript as a workaround
        try:
            element = driver.find_element(by, identifier)
            driver.execute_script("arguments[0].click();", element)
            logging.info(f"Clicked element via JavaScript: {identifier}")
            return True
        except Exception as js_e:
            logging.error(f"Failed to click element via JavaScript: {identifier}. Exception: {js_e}")
            return False


def set_and_maintain_playback_rate(driver):
    """Set and continuously maintain the video playback rate."""
    script = f"""
    function setPlaybackRate() {{
        var video = document.querySelector('video');
        if (video && video.playbackRate !== {PLAYBACK_RATE}) {{
            video.playbackRate = {PLAYBACK_RATE};
        }}
    }}
    setPlaybackRate();
    setInterval(setPlaybackRate, 1000);  // Check every second
    """
    driver.execute_script(script)
    logging.info(f"Set up continuous playback rate maintenance at {PLAYBACK_RATE}x.")


def replay_video(driver):
    """Configure the video to loop automatically."""
    try:
        driver.execute_script(f"""
            var video = document.querySelector('video');
            if (video) {{
                video.loop = true;
                video.playbackRate = {PLAYBACK_RATE};
            }}
        """)
        logging.info("Configured video to loop automatically.")
    except WebDriverException as e:
        logging.error(f"Failed to configure loop logic: {e}")


def get_video_links():
    """Get video links based on user input."""
    choice = input("Enter '1' for channel URL or '2' for direct video URL: ").strip()
    
    if choice == '1':
        channel_url = input("Please provide channel URL: ").strip()
        return get_channel_links(channel_url)
    elif choice == '2':
        video_url = input("Please provide direct video URL: ").strip()
        return [video_url]  # Return as a list for consistency
    else:
        logging.error("Invalid choice. Please run the script again.")
        return []


def get_channel_links(channel_url):
    """Retrieve all video links from the specified YouTube channel."""
    driver, profile_path = init_driver()
    if not driver:
        return []

    try:
        logging.info(f"Navigating to channel URL: {channel_url}")
        driver.get(channel_url)
        WebDriverWait(driver, TIMEOUTS["page_load"]).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Page loaded successfully.")

        # Handle consent on homepage
        click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_HOMEPAGE, TIMEOUTS["consent"])

        # Scroll to load videos
        scroll_to_load_videos(driver)

        # Extract video links
        link_elements = driver.find_elements(By.CLASS_NAME, VIDEO_LINKS_CLASS_NAME)
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
        try:
            driver.quit()
            logging.info("WebDriver closed after retrieving channel links.")
            if CLEANUP_PROFILES and profile_path and os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                logging.info(f"Removed profile directory: {profile_path}")
        except Exception as e:
            logging.error(f"Error closing WebDriver: {e}")


def scroll_to_load_videos(driver, scroll_pause_time=2, max_scrolls=5):
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


def is_video_playing(driver):
    try:
        return driver.execute_script("""
            var video = document.querySelector('video');
            return video && !video.paused && video.currentTime > 0 && !video.ended && video.readyState > 2;
        """)
    except Exception:
        return False


def skip_ad(driver):
    """
    Attempts to detect and skip YouTube ads using multiple strategies.
    """
    try:
        wait = WebDriverWait(driver, TIMEOUTS['ad_skip'])

        # Strategy 1: Click on 'Skip Ads' button if available
        try:
            skip_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'ytp-ad-skip-button') or contains(text(), 'Skip Ads')]")
                )
            )
            skip_button.click()
            logging.info("Skipped ad using 'Skip Ads' button.")
            return
        except (NoSuchElementException, TimeoutException):
            logging.debug("'Skip Ads' button not found.")

        # Strategy 2: Close 'Ad' overlay using close button
        try:
            close_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@aria-label, 'Close') and contains(@class, 'ytp-ad-overlay-close-button')]")
                )
            )
            close_button.click()
            logging.info("Closed ad overlay using close button.")
            return
        except (NoSuchElementException, TimeoutException):
            logging.debug("Ad overlay close button not found.")

        # Strategy 3: Press 'Escape' key to exit ad
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            logging.info("Attempted to skip ad by sending 'Escape' key.")
            return
        except Exception as e:
            logging.warning(f"Failed to skip ad using 'Escape' key: {e}")

        # Strategy 4: Hide ad elements via JavaScript as a last resort
        try:
            driver.execute_script("""
                var adElements = document.querySelectorAll('.ytp-ad-player-overlay, .video-ads .ad-container');
                adElements.forEach(function(element) {
                    element.style.display = 'none';
                });
            """)
            logging.info("Hid ad elements using JavaScript.")
        except Exception as e:
            logging.error(f"Failed to hide ad elements: {e}")

    except Exception as e:
        logging.error(f"An unexpected error occurred while skipping ads: {e}", exc_info=True)


def set_video_quality(driver, quality='144p'):
    """Set the video quality to the specified resolution by interacting with YouTube's player interface."""
    try:
        logging.info(f"Attempting to set video quality to {quality}")
        
        # Wait for the video player to be ready
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ytp-settings-button"))
        )
        
        # Click the settings button
        settings_button = driver.find_element(By.CSS_SELECTOR, ".ytp-settings-button")
        driver.execute_script("arguments[0].click();", settings_button)
        logging.info("Clicked settings button")
        
        # Wait for and click the quality menu item
        quality_menu_item = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ytp-menuitem') and contains(., 'Quality')]"))
        )
        driver.execute_script("arguments[0].click();", quality_menu_item)
        logging.info("Clicked quality menu item")
        
        # Wait for the quality submenu to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ytp-quality-menu"))
        )
        
        # Find and click the specific quality option
        quality_options = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ytp-menuitem"))
        )
        for option in quality_options:
            if quality in option.text:
                driver.execute_script("arguments[0].scrollIntoView(true);", option)
                time.sleep(0.5)  # Allow time for scrolling
                driver.execute_script("arguments[0].click();", option)
                logging.info(f"Selected {quality} from quality menu")
                break
        else:
            logging.warning(f"Quality option {quality} not found in the menu")
        
        # Wait for a moment to let the quality change take effect
        time.sleep(2)
        
        logging.info(f"Video quality should now be set to {quality}")
        
    except Exception as e:
        logging.error(f"Failed to set video quality: {e}")


def mute_video(driver):
    """Mute the video if it's not already muted."""
    try:
        # Use JavaScript to mute the video
        mute_script = """
        var video = document.querySelector('video');
        if (video) {
            video.muted = true;
            return true;
        }
        return false;
        """
        muted = driver.execute_script(mute_script)
        
        if muted:
            logging.info("Video muted successfully using JavaScript.")
        else:
            logging.warning("Could not find video element to mute.")
            
            # Fallback to clicking mute button if JavaScript method fails
            mute_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-mute-button"))
            )
            
            if 'ytp-mute-button-active' not in mute_button.get_attribute('class'):
                mute_button.click()
                logging.info("Video muted by clicking mute button.")
            else:
                logging.info("Video was already muted.")
        
    except Exception as e:
        logging.error(f"An error occurred while muting the video: {e}")


def run_video(link, headless=False):
    """Core function to handle video playback operations with looping."""
    for attempt in range(MAX_RETRIES):
        try:
            driver, profile_path = init_driver(headless=headless)
            if not driver:
                logging.error("Driver initialization failed. Retrying...")
                time.sleep(2)
                continue

            logging.info(f"Processing video: {link}")
            driver.get(link)
            WebDriverWait(driver, TIMEOUTS["page_load"]).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            logging.info("Video page loaded successfully.")

            # Handle consent on video page
            click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_VIDEO, TIMEOUTS["consent"])

            # Set video quality, mute, and playback rate
            set_video_quality(driver, '144p')
            mute_video(driver)
            set_and_maintain_playback_rate(driver)
            replay_video(driver)  # Set up automatic loop

            # Allow the video to play for the desired duration
            logging.info(f"Starting video playback for {VIDEO_PLAY_DURATION} seconds with looping enabled.")
            start_time = time.time()
            while time.time() - start_time < VIDEO_PLAY_DURATION:
                ensure_video_playing(driver)
                time.sleep(5)  # Check playback status periodically

            logging.info(f"Finished playing video for {VIDEO_PLAY_DURATION} seconds.")
            break

        except Exception as e:
            logging.error(f"Error processing video {link}: {e}")
            logging.info(f"Retrying video '{link}' (Attempt {attempt + 2}/{MAX_RETRIES})...")
            time.sleep(5)  # Wait before retrying
        finally:
            try:
                driver.quit()
                logging.info("WebDriver closed after video processing.")
                if CLEANUP_PROFILES and profile_path and os.path.exists(profile_path):
                    shutil.rmtree(profile_path)
                    logging.info(f"Removed profile directory: {profile_path}")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")

    if attempt == MAX_RETRIES - 1:
        logging.critical(f"Failed to process video '{link}' after {MAX_RETRIES} attempts.")


def ensure_video_playing(driver):
    """Ensures that the video is playing. If an ad is detected, attempts to skip it."""
    try:
        is_playing = driver.execute_script("""
            return !document.querySelector('.ad-showing');
        """)
        if not is_playing:
            logging.info("Ad detected. Attempting to skip.")
            skip_ad(driver)
            time.sleep(2)  # Wait for the ad to be skipped
        else:
            logging.debug("Video is currently playing.")
    except Exception as e:
        logging.error(f"Error while ensuring video is playing: {e}", exc_info=True)


def process_video_link(link):
    """Function to be run in each process, handling a single video link."""
    run_video(link, headless=False)


def run_window(links):
    """Function to run a single window, processing multiple links sequentially."""
    for link in links:
        process_video_link(link)


def main():
    """Main function to orchestrate video playback on multiple windows."""
    setup_logging()
    logging.info("Script started.")

    all_links = get_video_links()
    if not all_links:
        logging.error("No links to process. Exiting.")
        return

    # Distribute links among windows
    links_per_window = [all_links[i::NUM_WINDOWS] for i in range(NUM_WINDOWS)]

    # Create and start processes for each window
    processes = []
    for window_links in links_per_window:
        if window_links:  # Only create a process if there are links to process
            p = multiprocessing.Process(target=run_window, args=(window_links,))
            processes.append(p)
            p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # Cleanup profiles if enabled
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