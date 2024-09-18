#======== V1.0.0.0

# import multiprocessing
# import time
# import logging
# import sys
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     NoSuchElementException,
#     TimeoutException,
#     WebDriverException,
#     ElementClickInterceptedException,
# )
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.action_chains import ActionChains

# # Constants
# CONSENT_BUTTON_XPATH_HOMEPAGE = "//button[@aria-label='Accept all']"
# CONSENT_BUTTON_XPATH_VIDEO = "//button[@aria-label='Accept the use of cookies and other data for the purposes described']"
# VIDEO_LINKS_CLASS_NAME = "yt-simple-endpoint.ytd-thumbnail"
# ADS_BUTTON_SELECTOR = "button.ytp-ad-skip-button"
# MUTE_BUTTON_CLASS = "ytp-mute-button"
# REPLAY_XPATH = '//*[@title="Replay"]'
# PLAYBACK_RATE = 2  # Set to your desired speed (e.g., 1.5, 1.75, or 2)
# TIMEOUTS = {
#     "consent": 10,
#     "ads": 5,
#     "mute": 5,
#     "replay": 10,
#     "page_load": 15,
# }
# MAX_RETRIES = 3
# LOG_FILE = "tubewatch.log"
# VIDEO_PLAY_DURATION = 3600  # Play each video for 1 hour (3600 seconds)
# VIDEO_REPETITIONS = 100  # Number of times to repeat each video

# # Suppress urllib3 warnings related to SSL
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# def setup_logging():
#     """Configure logging for the script."""
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
#         handlers=[
#             logging.FileHandler(LOG_FILE),
#             logging.StreamHandler(sys.stdout),
#         ],
#     )


# def init_driver(window_size=(800, 600), headless=False):
#     """Initialize and return a Selenium WebDriver with desired options."""
#     chrome_options = Options()
#     chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
#     if headless:
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--disable-notifications")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
#     # Additional options to improve stability
#     chrome_options.add_argument("--disable-infobars")
#     chrome_options.add_argument("--disable-extensions")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

#     try:
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()),
#             options=chrome_options,
#         )
#         logging.info("WebDriver initialized successfully.")
#         return driver
#     except WebDriverException as e:
#         logging.error(f"Error initializing WebDriver: {e}")
#         return None


# def click_element(driver, by, identifier, timeout=10):
#     """
#     Clicks an element specified by the locator strategy.
#     Attempts to handle elements that are not immediately clickable.
#     """
#     try:
#         element = WebDriverWait(driver, timeout).until(
#             EC.element_to_be_clickable((by, identifier))
#         )
#         # Scroll to the element to ensure it's in view
#         driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element)
#         time.sleep(0.5)  # Brief pause to allow any animations to complete
#         element.click()
#         logging.info(f"Clicked element: {identifier}")
#         return True
#     except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
#         logging.warning(f"Element not found or not clickable: {identifier}. Exception: {e}")
#         # Attempt to click via JavaScript as a workaround
#         try:
#             element = driver.find_element(by, identifier)
#             driver.execute_script("arguments[0].click();", element)
#             logging.info(f"Clicked element via JavaScript: {identifier}")
#             return True
#         except Exception as js_e:
#             logging.error(f"Failed to click element via JavaScript: {identifier}. Exception: {js_e}")
#             return False


# def set_and_maintain_playback_rate(driver):
#     """Set and continuously maintain the video playback rate."""
#     script = f"""
#     function setPlaybackRate() {{
#         var video = document.querySelector('video');
#         if (video && video.playbackRate !== {PLAYBACK_RATE}) {{
#             video.playbackRate = {PLAYBACK_RATE};
#         }}
#     }}
#     setPlaybackRate();
#     setInterval(setPlaybackRate, 1000);  // Check every second
#     """
#     driver.execute_script(script)
#     logging.info(f"Set up continuous playback rate maintenance at {PLAYBACK_RATE}x.")


# def replay_video(driver):
#     """Configure the video to replay automatically upon ending."""
#     try:
#         driver.execute_script(f"""
#             var video = document.querySelector('video');
#             if (video) {{
#                 video.onended = function() {{
#                     video.currentTime = 0;
#                     video.play();
#                 }};
#                 video.playbackRate = {PLAYBACK_RATE};
#             }}
#         """)
#         logging.info("Configured video to replay automatically upon ending.")
#     except WebDriverException as e:
#         logging.error(f"Failed to configure replay logic: {e}")


# def get_video_links():
#     """Get video links based on user input."""
#     choice = input("Enter '1' for channel URL or '2' for direct video URL: ").strip()
    
#     if choice == '1':
#         channel_url = input("Please provide channel URL: ").strip()
#         return get_channel_links(channel_url)
#     elif choice == '2':
#         video_url = input("Please provide direct video URL: ").strip()
#         return [video_url]  # Return as a list for consistency
#     else:
#         logging.error("Invalid choice. Please run the script again.")
#         return []


# def get_channel_links(channel_url):
#     """Retrieve all video links from the specified YouTube channel."""
#     driver = init_driver()
#     if not driver:
#         return []

#     try:
#         logging.info(f"Navigating to channel URL: {channel_url}")
#         driver.get(channel_url)
#         WebDriverWait(driver, TIMEOUTS["page_load"]).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )
#         logging.info("Page loaded successfully.")

#         # Handle consent on homepage
#         click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_HOMEPAGE, TIMEOUTS["consent"])

#         # Scroll to load videos
#         scroll_to_load_videos(driver)

#         # Extract video links
#         link_elements = driver.find_elements(By.CLASS_NAME, VIDEO_LINKS_CLASS_NAME)
#         links = list(set([
#             elem.get_attribute("href")
#             for elem in link_elements
#             if elem.get_attribute("href") and "/watch?v=" in elem.get_attribute("href")
#         ]))
#         logging.info(f"Found {len(links)} unique video links.")

#         return links
#     except Exception as e:
#         logging.error(f"Error retrieving channel links: {e}")
#         return []
#     finally:
#         try:
#             driver.quit()
#             logging.info("WebDriver closed after retrieving channel links.")
#         except Exception as e:
#             logging.error(f"Error closing WebDriver: {e}")


# def scroll_to_load_videos(driver, scroll_pause_time=2, max_scrolls=5):
#     """Scroll the channel page to load more videos."""
#     last_height = driver.execute_script("return document.documentElement.scrollHeight")
#     for scroll in range(max_scrolls):
#         logging.info(f"Scrolling {scroll + 1}/{max_scrolls} to load more videos.")
#         driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
#         time.sleep(scroll_pause_time)
#         new_height = driver.execute_script("return document.documentElement.scrollHeight")
#         if new_height == last_height:
#             logging.info("No more videos to load.")
#             break
#         last_height = new_height


# def is_video_playing(driver):
#     try:
#         return driver.execute_script("""
#             var video = document.querySelector('video');
#             return video && !video.paused && video.currentTime > 0 && !video.ended;
#         """)
#     except Exception:
#         return False


# def skip_ad(driver):
#     """Attempt to skip an ad if possible."""
#     try:
#         # Look for various skip ad button selectors
#         skip_button_selectors = [
#             "button.ytp-ad-skip-button",
#             "button.videoAdUiSkipButton",
#             "//button[contains(@class, 'ytp-ad-skip-button')]",
#             "//button[contains(text(), 'Skip')]",
#             "//button[contains(text(), 'Skip')]"
#         ]
        
#         for selector in skip_button_selectors:
#             try:
#                 if selector.startswith("//"):
#                     skip_button = WebDriverWait(driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH, selector))
#                     )
#                 else:
#                     skip_button = WebDriverWait(driver, 5).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
#                     )
#                 skip_button.click()
#                 logging.info(f"Ad skipped using selector: {selector}")
#                 return True
#             except:
#                 continue
        
#         logging.info("No skip button found or ad not skippable.")
#         return False
#     except Exception as e:
#         logging.error(f"Error while trying to skip ad: {e}")
#         return False


# def set_video_quality(driver, quality='144p'):
#     """Set the video quality to the specified resolution."""
#     try:
#         # Wait for the video player to be ready
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "button.ytp-settings-button"))
#         )
        
#         # Click the settings button
#         settings_button = driver.find_element(By.CSS_SELECTOR, "button.ytp-settings-button")
#         ActionChains(driver).move_to_element(settings_button).click().perform()
#         logging.info("Clicked the settings button.")
#         time.sleep(1)  # Short pause to allow menu to open
        
#         # Click the quality menu
#         quality_menu = WebDriverWait(driver, 15).until(
#             EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ytp-panel-menu')]//div[contains(text(), 'Quality')]"))
#         )
#         quality_menu.click()
#         logging.info("Clicked the Quality menu.")
#         time.sleep(1)  # Short pause to allow submenu to open
        
#         # Select the desired quality
#         quality_options = WebDriverWait(driver, 15).until(
#             EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'ytp-quality-menu')]//div[contains(@class, 'ytp-menuitem')]"))
#         )
#         for option in quality_options:
#             if quality in option.text:
#                 option.click()
#                 logging.info(f"Selected video quality: {quality}")
#                 break
#         else:
#             logging.warning(f"Quality {quality} not found. Selecting lowest available quality.")
#             quality_options[-1].click()  # Select the last (lowest) quality option
        
#         # Verify the quality change
#         time.sleep(2)  # Wait for quality to change
#         current_quality = driver.execute_script("""
#             var video = document.querySelector('video');
#             return video.getVideoPlaybackQuality ? video.getVideoPlaybackQuality().height : video.videoHeight;
#         """)
#         logging.info(f"Current video quality height: {current_quality}p")
        
#     except Exception as e:
#         logging.error(f"An error occurred while setting video quality: {e}")


# def run_video(link, headless=False):
#     """Core function to handle video playback operations."""
#     attempt = 0
#     while attempt < MAX_RETRIES:
#         driver = init_driver(headless=headless)
#         if not driver:
#             logging.error("Driver initialization failed. Retrying...")
#             attempt += 1
#             time.sleep(2)
#             continue

#         try:
#             logging.info(f"Processing video: {link}")
#             driver.get(link)
#             WebDriverWait(driver, TIMEOUTS["page_load"]).until(
#                 EC.presence_of_element_located((By.TAG_NAME, "video"))
#             )
#             logging.info("Video page loaded successfully.")

#             # Handle consent on video page
#             click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_VIDEO, TIMEOUTS["consent"])

#             # Set video quality once before starting repetitions
#             set_video_quality(driver, '144p')
#             set_and_maintain_playback_rate(driver)
#             replay_video(driver)  # Set up automatic replay

#             for repetition in range(VIDEO_REPETITIONS):
#                 logging.info(f"Starting repetition {repetition + 1} of {VIDEO_REPETITIONS}")

#                 # Ensure the video is playing
#                 driver.execute_script("document.querySelector('video').play();")
#                 logging.info("Video playback started.")

#                 # Wait for the video to complete its duration
#                 # Alternatively, wait for the 'onended' event to trigger
#                 start_time = time.time()
#                 while time.time() - start_time < VIDEO_PLAY_DURATION:
#                     if skip_ad(driver):
#                         time.sleep(1)  # Short pause after skipping ad
#                         continue
#                     if not is_video_playing(driver):
#                         logging.warning("Video not playing. Attempting to resume.")
#                         driver.execute_script("document.querySelector('video').play();")
#                         time.sleep(2)
#                     time.sleep(5)  # Check playback status periodically

#                 logging.info(f"Finished repetition {repetition + 1} of video")

#                 # Optional: Pause briefly before the next repetition
#                 time.sleep(2)

#             logging.info(f"Finished playing video {VIDEO_REPETITIONS} times")
#             break

#         except Exception as e:
#             logging.error(f"Error processing video {link}: {e}")
#             attempt += 1
#             logging.info(f"Retrying ({attempt}/{MAX_RETRIES})...")
#             time.sleep(2)
#         finally:
#             try:
#                 driver.quit()
#                 logging.info("WebDriver closed after video processing.")
#             except Exception as e:
#                 logging.error(f"Error closing WebDriver: {e}")

#     if attempt == MAX_RETRIES:
#         logging.error(f"Failed to process video after {MAX_RETRIES} attempts: {link}")


# def main():
#     """Main function to orchestrate video playback."""
#     setup_logging()
#     logging.info("Script started.")

#     links = get_video_links()
#     if not links:
#         logging.error("No links to process. Exiting.")
#         return

#     for link in links[:2]:  # Process only the first two links
#         run_video(link)

#     logging.info("Finished processing videos.")


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         logging.warning("Script interrupted by user. Exiting gracefully.")
#         sys.exit(0)
#     except Exception as e:
#         logging.critical(f"Unexpected error: {e}", exc_info=True)
#         sys.exit(1)

##===== V1.1.00
# import multiprocessing
# import time
# import logging
# import sys
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     NoSuchElementException,
#     TimeoutException,
#     WebDriverException,
#     ElementClickInterceptedException,
# )
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.action_chains import ActionChains

# # Constants
# CONSENT_BUTTON_XPATH_HOMEPAGE = "//button[@aria-label='Accept all']"
# CONSENT_BUTTON_XPATH_VIDEO = "//button[@aria-label='Accept the use of cookies and other data for the purposes described']"
# VIDEO_LINKS_CLASS_NAME = "yt-simple-endpoint.ytd-thumbnail"
# ADS_BUTTON_SELECTOR = "button.ytp-ad-skip-button"
# MUTE_BUTTON_CLASS = "ytp-mute-button"
# REPLAY_XPATH = '//*[@title="Replay"]'
# PLAYBACK_RATE = 2  # Set to your desired speed (e.g., 1.5, 1.75, or 2)
# TIMEOUTS = {
#     "consent": 10,
#     "ads": 5,
#     "mute": 5,
#     "replay": 10,
#     "page_load": 15,
# }
# MAX_RETRIES = 3
# LOG_FILE = "tubewatch.log"
# VIDEO_PLAY_DURATION = 3600  # Play each video for 1 hour (3600 seconds)
# VIDEO_REPETITIONS = 100  # Number of times to repeat each video

# # Suppress urllib3 warnings related to SSL
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# def setup_logging():
#     """Configure logging for the script."""
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
#         handlers=[
#             logging.FileHandler(LOG_FILE),
#             logging.StreamHandler(sys.stdout),
#         ],
#     )


# def init_driver(window_size=(800, 600), headless=False):
#     """Initialize and return a Selenium WebDriver with desired options."""
#     chrome_options = Options()
#     chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
#     if headless:
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--disable-notifications")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
#     # Additional options to improve stability
#     chrome_options.add_argument("--disable-infobars")
#     chrome_options.add_argument("--disable-extensions")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

#     try:
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()),
#             options=chrome_options,
#         )
#         logging.info("WebDriver initialized successfully.")
#         return driver
#     except WebDriverException as e:
#         logging.error(f"Error initializing WebDriver: {e}")
#         return None


# def click_element(driver, by, identifier, timeout=10):
#     """
#     Clicks an element specified by the locator strategy.
#     Attempts to handle elements that are not immediately clickable.
#     """
#     try:
#         element = WebDriverWait(driver, timeout).until(
#             EC.element_to_be_clickable((by, identifier))
#         )
#         # Scroll to the element to ensure it's in view
#         driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element)
#         time.sleep(0.5)  # Brief pause to allow any animations to complete
#         element.click()
#         logging.info(f"Clicked element: {identifier}")
#         return True
#     except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
#         logging.warning(f"Element not found or not clickable: {identifier}. Exception: {e}")
#         # Attempt to click via JavaScript as a workaround
#         try:
#             element = driver.find_element(by, identifier)
#             driver.execute_script("arguments[0].click();", element)
#             logging.info(f"Clicked element via JavaScript: {identifier}")
#             return True
#         except Exception as js_e:
#             logging.error(f"Failed to click element via JavaScript: {identifier}. Exception: {js_e}")
#             return False


# def set_and_maintain_playback_rate(driver):
#     """Set and continuously maintain the video playback rate."""
#     script = f"""
#     function setPlaybackRate() {{
#         var video = document.querySelector('video');
#         if (video && video.playbackRate !== {PLAYBACK_RATE}) {{
#             video.playbackRate = {PLAYBACK_RATE};
#         }}
#     }}
#     setPlaybackRate();
#     setInterval(setPlaybackRate, 1000);  // Check every second
#     """
#     driver.execute_script(script)
#     logging.info(f"Set up continuous playback rate maintenance at {PLAYBACK_RATE}x.")


# def replay_video(driver):
#     """Configure the video to replay automatically upon ending."""
#     try:
#         driver.execute_script(f"""
#             var video = document.querySelector('video');
#             if (video) {{
#                 video.onended = function() {{
#                     video.currentTime = 0;
#                     video.play();
#                 }};
#                 video.playbackRate = {PLAYBACK_RATE};
#             }}
#         """)
#         logging.info("Configured video to replay automatically upon ending.")
#     except WebDriverException as e:
#         logging.error(f"Failed to configure replay logic: {e}")


# def get_video_links():
#     """Get video links based on user input."""
#     choice = input("Enter '1' for channel URL or '2' for direct video URL: ").strip()
    
#     if choice == '1':
#         channel_url = input("Please provide channel URL: ").strip()
#         return get_channel_links(channel_url)
#     elif choice == '2':
#         video_url = input("Please provide direct video URL: ").strip()
#         return [video_url]  # Return as a list for consistency
#     else:
#         logging.error("Invalid choice. Please run the script again.")
#         return []


# def get_channel_links(channel_url):
#     """Retrieve all video links from the specified YouTube channel."""
#     driver = init_driver()
#     if not driver:
#         return []

#     try:
#         logging.info(f"Navigating to channel URL: {channel_url}")
#         driver.get(channel_url)
#         WebDriverWait(driver, TIMEOUTS["page_load"]).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )
#         logging.info("Page loaded successfully.")

#         # Handle consent on homepage
#         click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_HOMEPAGE, TIMEOUTS["consent"])

#         # Scroll to load videos
#         scroll_to_load_videos(driver)

#         # Extract video links
#         link_elements = driver.find_elements(By.CLASS_NAME, VIDEO_LINKS_CLASS_NAME)
#         links = list(set([
#             elem.get_attribute("href")
#             for elem in link_elements
#             if elem.get_attribute("href") and "/watch?v=" in elem.get_attribute("href")
#         ]))
#         logging.info(f"Found {len(links)} unique video links.")

#         return links
#     except Exception as e:
#         logging.error(f"Error retrieving channel links: {e}")
#         return []
#     finally:
#         try:
#             driver.quit()
#             logging.info("WebDriver closed after retrieving channel links.")
#         except Exception as e:
#             logging.error(f"Error closing WebDriver: {e}")


# def scroll_to_load_videos(driver, scroll_pause_time=2, max_scrolls=5):
#     """Scroll the channel page to load more videos."""
#     last_height = driver.execute_script("return document.documentElement.scrollHeight")
#     for scroll in range(max_scrolls):
#         logging.info(f"Scrolling {scroll + 1}/{max_scrolls} to load more videos.")
#         driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
#         time.sleep(scroll_pause_time)
#         new_height = driver.execute_script("return document.documentElement.scrollHeight")
#         if new_height == last_height:
#             logging.info("No more videos to load.")
#             break
#         last_height = new_height


# def is_video_playing(driver):
#     try:
#         return driver.execute_script("""
#             var video = document.querySelector('video');
#             return video && !video.paused && video.currentTime > 0 && !video.ended;
#         """)
#     except Exception:
#         return False


# def skip_ad(driver):
#     """Attempt to skip an ad if possible."""
#     try:
#         # Look for various skip ad button selectors
#         skip_button_selectors = [
#             "button.ytp-ad-skip-button",
#             "button.videoAdUiSkipButton",
#             "//button[contains(@class, 'ytp-ad-skip-button')]",
#             "//button[contains(text(), 'Skip')]",
#             "//button[contains(text(), 'Skip')]"
#         ]
        
#         for selector in skip_button_selectors:
#             try:
#                 if selector.startswith("//"):
#                     skip_button = WebDriverWait(driver, 5).until(
#                         EC.element_to_be_clickable((By.XPATH, selector))
#                     )
#                 else:
#                     skip_button = WebDriverWait(driver, 5).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
#                     )
#                 skip_button.click()
#                 logging.info(f"Ad skipped using selector: {selector}")
#                 return True
#             except:
#                 continue
        
#         logging.info("No skip button found or ad not skippable.")
#         return False
#     except Exception as e:
#         logging.error(f"Error while trying to skip ad: {e}")
#         return False


# def set_video_quality(driver, quality='144p'):
#     """Set the video quality to the specified resolution."""
#     try:
#         logging.info(f"Attempting to set video quality to {quality}")
        
#         # First, try to set quality using JavaScript
#         js_script = f"""
#         var player = document.querySelector('#movie_player');
#         if (player && player.setPlaybackQualityRange) {{
#             player.setPlaybackQualityRange('{quality}', '{quality}');
#             return true;
#         }}
#         return false;
#         """
#         quality_set = driver.execute_script(js_script)
        
#         if quality_set:
#             logging.info(f"Video quality set to {quality} using JavaScript")
#             return
        
#         # If JavaScript method fails, try UI method
#         settings_button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-settings-button"))
#         )
#         settings_button.click()
#         logging.info("Clicked the Settings button")

#         quality_menu = WebDriverWait(driver, 5).until(
#             EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Quality')]"))
#         )
#         quality_menu.click()
#         logging.info("Opened quality menu")

#         desired_quality = WebDriverWait(driver, 5).until(
#             EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(),'{quality}')]"))
#         )
#         desired_quality.click()
#         logging.info(f"Selected {quality} from menu")

#         # Close settings menu
#         settings_button.click()
        
#         # Verify quality change
#         time.sleep(2)  # Wait for quality change to take effect
#         current_quality = driver.execute_script("return document.querySelector('video').videoHeight;")
#         logging.info(f"Current video height: {current_quality}p")

#     except Exception as e:
#         logging.error(f"Failed to set video quality: {e}")


# def mute_video(driver):
#     """Mute the video if it's not already muted."""
#     try:
#         # Use JavaScript to mute the video
#         mute_script = """
#         var video = document.querySelector('video');
#         if (video) {
#             video.muted = true;
#             return true;
#         }
#         return false;
#         """
#         muted = driver.execute_script(mute_script)
        
#         if muted:
#             logging.info("Video muted successfully using JavaScript.")
#         else:
#             logging.warning("Could not find video element to mute.")
            
#             # Fallback to clicking mute button if JavaScript method fails
#             mute_button = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-mute-button"))
#             )
            
#             if 'ytp-mute-button-active' not in mute_button.get_attribute('class'):
#                 mute_button.click()
#                 logging.info("Video muted by clicking mute button.")
#             else:
#                 logging.info("Video was already muted.")
        
#     except Exception as e:
#         logging.error(f"An error occurred while muting the video: {e}")


# def run_video(link, headless=False):
#     """Core function to handle video playback operations."""
#     attempt = 0
#     while attempt < MAX_RETRIES:
#         driver = init_driver(headless=headless)
#         if not driver:
#             logging.error("Driver initialization failed. Retrying...")
#             attempt += 1
#             time.sleep(2)
#             continue

#         try:
#             logging.info(f"Processing video: {link}")
#             driver.get(link)
#             WebDriverWait(driver, TIMEOUTS["page_load"]).until(
#                 EC.presence_of_element_located((By.TAG_NAME, "video"))
#             )
#             logging.info("Video page loaded successfully.")

#             # Handle consent on video page
#             click_element(driver, By.XPATH, CONSENT_BUTTON_XPATH_VIDEO, TIMEOUTS["consent"])

#             # Set video quality and mute before starting repetitions
#             set_video_quality(driver, '144p')
#             mute_video(driver)
#             set_and_maintain_playback_rate(driver)
#             replay_video(driver)  # Set up automatic replay

#             for repetition in range(VIDEO_REPETITIONS):
#                 logging.info(f"Starting repetition {repetition + 1} of {VIDEO_REPETITIONS}")

#                 # Ensure the video is playing
#                 driver.execute_script("document.querySelector('video').play();")
#                 logging.info("Video playback started.")

#                 # Wait for the video to complete its duration
#                 start_time = time.time()
#                 while time.time() - start_time < VIDEO_PLAY_DURATION:
#                     if skip_ad(driver):
#                         time.sleep(1)  # Short pause after skipping ad
#                         continue
#                     if not is_video_playing(driver):
#                         logging.warning("Video not playing. Attempting to resume.")
#                         driver.execute_script("document.querySelector('video').play();")
#                         mute_video(driver)  # Ensure video is still muted
#                         time.sleep(2)
#                     time.sleep(5)  # Check playback status periodically

#                 logging.info(f"Finished repetition {repetition + 1} of video")

#                 # Optional: Pause briefly before the next repetition
#                 time.sleep(2)

#             logging.info(f"Finished playing video {VIDEO_REPETITIONS} times")
#             break

#         except Exception as e:
#             logging.error(f"Error processing video {link}: {e}")
#             attempt += 1
#             logging.info(f"Retrying ({attempt}/{MAX_RETRIES})...")
#             time.sleep(2)
#         finally:
#             try:
#                 driver.quit()
#                 logging.info("WebDriver closed after video processing.")
#             except Exception as e:
#                 logging.error(f"Error closing WebDriver: {e}")

#     if attempt == MAX_RETRIES:
#         logging.error(f"Failed to process video after {MAX_RETRIES} attempts: {link}")


# def main():
#     """Main function to orchestrate video playback."""
#     setup_logging()
#     logging.info("Script started.")

#     links = get_video_links()
#     if not links:
#         logging.error("No links to process. Exiting.")
#         return

#     for link in links[:2]:  # Process only the first two links
#         run_video(link)

#     logging.info("Finished processing videos.")


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         logging.warning("Script interrupted by user. Exiting gracefully.")
#         sys.exit(0)
#     except Exception as e:
#         logging.critical(f"Unexpected error: {e}", exc_info=True)
#         sys.exit(1)

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
}
MAX_RETRIES = 3
LOG_FILE = "tubewatch.log"
VIDEO_PLAY_DURATION = 3600  # Play each video for 1 hour (3600 seconds)
VIDEO_REPETITIONS = 100  # Number of times to repeat each video

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


def init_driver(window_size=(800, 600), headless=False):
    """Initialize and return a Selenium WebDriver with desired options."""
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

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
        logging.info("WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
        return None


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
    driver = init_driver()
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
    """Attempt to skip an ad if possible."""
    try:
        # Look for various skip ad button selectors
        skip_button_selectors = [
            "button.ytp-ad-skip-button",
            "button.videoAdUiSkipButton",
            "//button[contains(@class, 'ytp-ad-skip-button')]",
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Skip')]"
        ]
        
        for selector in skip_button_selectors:
            try:
                if selector.startswith("//"):
                    skip_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    skip_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                skip_button.click()
                logging.info(f"Ad skipped using selector: {selector}")
                return True
            except:
                continue
        
        logging.info("No skip button found or ad not skippable.")
        return False
    except Exception as e:
        logging.error(f"Error while trying to skip ad: {e}")
        return False


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
    attempt = 0
    while attempt < MAX_RETRIES:
        driver = init_driver(headless=headless)
        if not driver:
            logging.error("Driver initialization failed. Retrying...")
            attempt += 1
            time.sleep(2)
            continue

        try:
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
                if skip_ad(driver):
                    time.sleep(1)  # Short pause after skipping ad
                if not is_video_playing(driver):
                    logging.warning("Video not playing. Attempting to resume.")
                    ensure_video_playing(driver)
                time.sleep(5)  # Check playback status periodically

            logging.info(f"Finished playing video for {VIDEO_PLAY_DURATION} seconds.")
            break

        except Exception as e:
            logging.error(f"Error processing video {link}: {e}")
            attempt += 1
            logging.info(f"Retrying ({attempt}/{MAX_RETRIES})...")
            time.sleep(2)
        finally:
            try:
                driver.quit()
                logging.info("WebDriver closed after video processing.")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")

    if attempt == MAX_RETRIES:
        logging.error(f"Failed to process video after {MAX_RETRIES} attempts: {link}")

def ensure_video_playing(driver):
    """Ensure the video is playing, handling various scenarios."""
    try:
        # Check if video element exists
        video = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        
        # Check if the video is paused or not playing
        is_playing = driver.execute_script("""
            var video = document.querySelector('video');
            return video && !video.paused && video.currentTime > 0 && !video.ended && video.readyState > 2;
        """)
        
        if not is_playing:
            logging.info("Video is not playing. Attempting to play via JavaScript.")
            driver.execute_script("""
                var video = document.querySelector('video');
                if (video) {
                    video.play();
                }
            """)
            time.sleep(2)  # Allow time for the video to start playing
            
            # Verify if the video started playing
            is_playing = driver.execute_script("""
                var video = document.querySelector('video');
                return video && !video.paused && video.currentTime > 0 && !video.ended && video.readyState > 2;
            """)
            
            if not is_playing:
                logging.warning("Video did not start playing via JavaScript. Attempting to click the play button.")
                play_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-play-button"))
                )
                play_button.click()
                time.sleep(2)  # Allow time for the video to start playing
                
                # Final verification
                is_playing = driver.execute_script("""
                    var video = document.querySelector('video');
                    return video && !video.paused && video.currentTime > 0 && !video.ended && video.readyState > 2;
                """)
                
                if is_playing:
                    logging.info("Video playback ensured by clicking the play button.")
                else:
                    logging.error("Failed to start video playback after multiple attempts.")
            else:
                logging.info("Video playback ensured by JavaScript.")
        
        else:
            logging.info("Video is already playing.")
        
        # Ensure video is muted
        mute_video(driver)
        
    except Exception as e:
        logging.error(f"Error ensuring video playback: {e}")


def main():
    """Main function to orchestrate video playback."""
    setup_logging()
    logging.info("Script started.")

    links = get_video_links()
    if not links:
        logging.error("No links to process. Exiting.")
        return

    for link in links[:2]:  # Process only the first two links
        run_video(link)

    logging.info("Finished processing videos.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Script interrupted by user. Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
