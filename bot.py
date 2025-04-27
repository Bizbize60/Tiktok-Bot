from tiktok_captcha_solver import SeleniumSolver
import os
import time
import random
import threading
import requests
import cv2
from queue import Queue
import numpy as np
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from stem.control import Controller
from stem import Signal
from pynput.keyboard import Controller as KeyboardController
import undetected_chromedriver as uc
from selenium_stealth import stealth
import tempfile
from selenium.common.exceptions import TimeoutException

# Keyboard controller for simulating human-like typing
keyboard = KeyboardController()

# Tor Proxy Settings
TOR_PROXY = "proxy ip"
MAX_RETRIES = 3  # Maximum retry attempts per account
THREAD_COUNT = 10  # Number of concurrent browsers/threads

# Account credentials list
ACCOUNTS = [
    {"email": "zzzzz", "password": "pasword"},
    # Add more accounts as needed
]

def slide_slider(driver, slider_xpath, pixel_offset):
    """
    Simulates human-like slider movement for captcha solving
    Args:
        driver: Selenium WebDriver instance
        slider_xpath: XPath of the slider element
        pixel_offset: Distance to slide the slider
    """
    slider = driver.find_element(By.XPATH, slider_xpath)
    actions = ActionChains(driver)
    
    # Initial aggressive movement
    actions.move_to_element_with_offset(slider, 10, 5).click_and_hold().pause(0.2)
    
    total = 0
    remaining = pixel_offset
    base_speed = pixel_offset * 0.20  # Start with 20% of total distance
    
    while total < pixel_offset:
        # Smooth deceleration (reduced power to 1.5)
        step = min(
            base_speed + (remaining**1.5 * 0.0002),
            remaining
        )
        
        # Add larger variation
        step *= random.uniform(1.0, 1.2)  # Random increase up to 20%
        step = max(3, step)  # Minimum 3px movement
        
        # Micro-adjustments for last 15px
        if remaining < 15:
            step = random.uniform(1.5, 3.5)
        
        actions.move_by_offset(
            step + random.uniform(-0.2, 0.2),
            random.uniform(-0.1, 0.1)
        ).pause(random.uniform(0.02, 0.05))  # Shorter pauses
        
        total += step
        remaining = pixel_offset - total
        base_speed *= 0.90  # Slow down by 10% each step
    
    actions.release().perform()
    print(f"⚡ Slider moved {total:.2f}px (Error: {abs(pixel_offset - total):2f}px)")

def change_tor_ip():
    """Requests a new IP address through the Tor network"""
    try:
        with Controller.from_port(port="int port") as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)  # Request new identity
            print("New Tor IP acquired!")
            time.sleep(5)  # Wait for new IP to activate
    except Exception as e:
        print(f"Failed to change Tor IP! Error: {e}")

def create_browser():
    """Initializes Chrome browser with Tor proxy and anti-detection settings"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--proxy-server={TOR_PROXY}")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    
    # Create unique temporary profile directory
    temp_profile_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile_dir}")
    
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Failed to start browser! Error: {e}")
        return None

def fake_keyboard_activity():
    """Simulates fake keyboard activity (doesn't actually type)"""
    fake_keys = ["a", "s", "d", "f", "j", "k", "l", "space", "enter", "ctrl", "alt"]
    while True:
        key = random.choice(fake_keys)
        time.sleep(random.uniform(10, 20))

def download_image(browser, xpath, filename):
    """
    Downloads or takes screenshot of specified image element
    Args:
        browser: Selenium WebDriver instance
        xpath: XPath of the image element
        filename: Name to save the image as
    """
    try:
        element = WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        # Wait up to 15 seconds for src attribute to populate
        timeout = 15
        poll_interval = 0.5
        waited = 0
        src = element.get_attribute("src")
        
        while (not src or src.strip() == "") and waited < timeout:
            time.sleep(poll_interval)
            waited += poll_interval
            src = element.get_attribute("src")
        
        if not src or src.strip() == "":
            raise Exception(f"{filename} src attribute still empty after {timeout} seconds!")
        
        file_path = f"/{filename}.png"
        if src.startswith("blob:"):
            element.screenshot(file_path)
            print(f"{filename}.png saved as screenshot!")
        else:
            response = requests.get(src)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"{filename}.png saved!")
            else:
                print(f"Failed to download {filename}, status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

def merge_images(background_path, overlay_path):
    """
    Processes and merges two images for captcha solving
    Returns calculated pixel offset for slider
    """
    # Load images in grayscale
    bg = cv2.imread(background_path, cv2.IMREAD_GRAYSCALE)
    ov = cv2.imread(overlay_path, cv2.IMREAD_GRAYSCALE)
    
    if bg is None or ov is None:
        raise FileNotFoundError("Failed to load images!")

    # Contour analysis
    _, thresh = cv2.threshold(ov, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        raise Exception("No contours found!")

    # Calculate rotation angle
    c = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(c)
    angle = rect[-1]

    # Normalize angle to [0, 180) range
    if rect[1][0] < rect[1][1]:  # Width < Height
        angle += 90
    angle = abs(angle % 180)  # Positive value between 0-180

    print(f"Corrected Angle: {angle:.2f}°")
    return calculate_pixel_offset(angle)

def calculate_pixel_offset(angle):
    """Calculates precise pixel offset for slider based on rotation angle"""
    MAX_SLIDER = 348
    CALIBRATION = 0.957  # Optimized calibration value
    OFFSET_CORRECTION = 3.2  # Manual offset adjustment
    
    pixel_offset = (angle / 180) * MAX_SLIDER * CALIBRATION + OFFSET_CORRECTION + 10
    
    print(f"Precise Sliding: {pixel_offset:.2f}px")
    return max(0, min(pixel_offset, MAX_SLIDER))  # Ensure within bounds

def watch_live(email, password):
    """Main function to handle TikTok live watching process"""
    print("Acquiring new IP...")
    change_tor_ip()

    browser = create_browser()
    if not browser:
        print("Failed to start browser! �")
        return

    # Initialize captcha solver
    api_key = "xxxxxxapiley"
    sadcaptcha = SeleniumSolver(
        browser,
        api_key,
        mouse_step_size=1,
        mouse_step_delay_ms=10
    )

    browser.maximize_window()
    
    try:
        # Start fake keyboard activity thread
        keyboard_thread = threading.Thread(target=fake_keyboard_activity, daemon=True)
        keyboard_thread.start()

        # Open TikTok live stream
        browser.get("yayın linki")
        print("TikTok live opened! ✅")
        time.sleep(3)

        # Click login button
        wait = WebDriverWait(browser, 20)
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "header-login-button")))
        ActionChains(browser).move_to_element(login_button).click().perform()
        print("Login button clicked! ✅")
        time.sleep(5)

        # Phone/email login selection
        try:
            # Try different login method selection scenarios
            try:
                second_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/div/div[2]/div[2]'))
                )
                ActionChains(browser).move_to_element(second_button).click().perform()
            except:
                try:
                    second_scenario = WebDriverWait(browser, 6).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/div[1]/div/button[2]'))
                    )
                    ActionChains(browser).move_to_element(second_scenario).click().perform()
                except:
                    try:
                        first_button = WebDriverWait(browser, 6).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/div[4]/div/div[2]'))
                        print("Found div4/div2 button - starting special procedure")
                        ActionChains(browser).move_to_element(first_button).click().perform()
                        second_button = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/div[4]/div[1]/div[2]'))
                        )
                        ActionChains(browser).move_to_element(second_button).click().perform()
                    except:
                        first_button = WebDriverWait(browser, 6).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/div[4]/div[1]/div[2]'))
                        print("Found div4/div2 button - starting special procedure")
                        ActionChains(browser).move_to_element(first_button).click().perform()
        except Exception as e:
            print(f"Phone button click error: {str(e)}")
            browser.quit()
            return

        # Click email login link
        wait = WebDriverWait(browser, 40)
        link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/login/phone-or-email/email"]')))
        link.click()
        print("Email login button clicked!")
        time.sleep(1)

        # Enter email and password
        wait = WebDriverWait(browser, 50)
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Email or username"]')))
        email_input.send_keys(email)
        time.sleep(3)

        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Password"]')))
        password_input.send_keys(password)
        print("Credentials entered! ✅")
        
        # Click login submit button
        try:
            login_enter = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div[2]/form/button')))
            login_enter.click()
            print("Login button clicked! ✅")
        except:
            second_input_button = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="loginContainer"]/div/div/form/button')))
            second_input_button.click()
            print("Button clicked")
            
        # Handle captcha
        print("Waiting for captcha...")
        wait = WebDriverWait(browser, 30)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="captcha-verify-container-main-page"]/div[2]/div[1]/img[1]')))
        print("Captcha page loaded, downloading images...")
            
        verification_success = False
        sadcaptcha.solve_captcha_if_present(15,3)
        
        try:   
            verification_input = WebDriverWait(browser, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//div[21]/div[2]/div[2]/div/div[1]/input | //div[20]/div[2]/div[2]/div/div[1]/input | //div[19]/div[2]/div[2]/div/div[1]/input')
                )
            )
            print("✅ Captcha solved, input box visible!")
            verification_success = True
        except:
            print("1")
                        
        # Email verification process
        print("Captcha verified, proceeding to email check...")
        time.sleep(1.5)
        browser.execute_script("window.open('webmail', '_blank');")
        WebDriverWait(browser, 10).until(lambda d: len(d.window_handles) > 1)
        browser.switch_to.window(browser.window_handles[-1])

        # Email login
        wait = WebDriverWait(browser, 50)
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="rcmloginuser"]')))
        email_input.send_keys(email)
        
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="rcmloginpwd"]')))
        password_input.send_keys(password)
        print("Email credentials entered! ✅")

        login_enter = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rcmloginsubmit"]')))
        login_enter.click()
        print("Email login successful")
        time.sleep(1)

        # Get verification code from email
        element = browser.find_element(
            By.XPATH, "//*[@id='messagelist']/tbody/tr[1]//td[@class='subject']//span[@class='subject']//a//span"
        )
        verification_code = element.text[0:6]
        print(f"Verification code received: {verification_code}")

        # Switch back to TikTok tab
        browser.switch_to.window(browser.window_handles[0])
        print("Switched back to TikTok tab")
        
        # Enter verification code
        try:
            key_input = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[20]/div[2]/div[2]/div/div[1]/input')))
        except:
            key_input = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[21]/div[2]/div[2]/div/div[1]/input')))
            
        for char in verification_code:
            key_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.3))  # Random typing speed
        browser.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", key_input)
        
        # Click submit button
        submit_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, 
                '/html/body/div[20]/div[2]/div[2]/button | '
                '/html/body/div[21]/div[2]/div[2]/button'
            ))
        )
        actions = ActionChains(browser)
        actions.move_to_element(submit_button)

        # Add slight randomness before clicking
        actions.move_by_offset(random.uniform(-5, 5), random.uniform(-5, 5))
        actions.pause(random.uniform(0.3, 0.7))

        # Occasionally simulate double-click
        if random.random() < 0.2:
            actions.click().pause(random.uniform(0.1, 0.2))

        actions.click().perform()
        print("Verification code submitted!")
        
        # Handle potential second captcha
        try:
            verify_puzzle = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="captcha-verify-container-main-page"]/div[2]/div[1]/img[1]')))
            sadcaptcha.solve_captcha_if_present(15,3)
            print("Entered live stream ✅")
        except:
            try:
                verify_puzzle = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[20]/div[2]/div[2]/div[2]')))
                time.sleep(64)
                verify_puzzle.click()
                browser.switch_to.window(browser.window_handles[-1])
                element = browser.find_element(
                    By.XPATH, "//*[@id='messagelist']/tbody/tr[1]//td[@class='subject']//span[@class='subject']//a//span"
                )
                verification_code = element.text[0:6]
                print(f"Verification code received: {verification_code}")
                browser.switch_to.window(browser.window_handles[0])
                for char in verification_code:
                    key_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                browser.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", key_input)
                
                # Click submit button again
                ActionChains(browser)\
                    .move_to_element(submit_button)\
                    .pause(random.uniform(0.3, 0.7))\
                    .click()\
                    .perform()
            
                print("Verification code submitted! Entered live stream ✅")
            except:
                print("Entered stream ✅")
        
        # Keep the browser alive
        while True:
            time.sleep(60)

    except Exception as e:
        print(f"Error during process: {e}")
        browser.quit()

def worker():
    """Worker function for multi-threaded account processing"""
    while True:
        account = account_queue.get()
        email = account["email"]
        
        # Check retry count for this account
        if retry_counts[email] >= MAX_RETRIES:
            print(f"⛔ Max retries reached for {email}, stopping!")
            account_queue.task_done()
            continue
        
        try:
            print(f"🌀 Starting process for {email}... ({retry_counts[email] + 1}. attempt)")
            watch_live(email, account['password'])
            print(f"✅ {email} completed successfully!")
        except Exception as e:
            print(f"❌ {email} encountered error: {str(e)} - Retrying...")
            retry_counts[email] += 1
            account_queue.put(account)  # Requeue for retry
            time.sleep(2)  # Short delay to prevent collisions
        finally:
            account_queue.task_done()

if __name__ == "__main__":
    # Initialize account queue and retry counters
    account_queue = Queue()
    retry_counts = {}
    
    for acc in ACCOUNTS:
        retry_counts[acc["email"]] = 0
        account_queue.put(acc)

    # Start worker threads
    for _ in range(THREAD_COUNT):
        threading.Thread(target=worker, daemon=True).start()

    # Wait for all accounts to be processed
    account_queue.join()
    print("🎉 All accounts processed!")