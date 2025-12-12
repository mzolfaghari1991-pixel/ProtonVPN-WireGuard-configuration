import os
import time
import random 
import glob 
import json 
import zipfile 
import requests 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# Define the selector for the modal backdrop which causes the click interception error
MODAL_BACKDROP_SELECTOR = (By.CLASS_NAME, "modal-two-backdrop")
CONFIRM_BUTTON_SELECTOR = (By.CSS_SELECTOR, ".button-solid-norm:nth-child(2)")

# Constants
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloaded_configs")
SERVER_ID_LOG_FILE = os.path.join(os.getcwd(), "downloaded_server_ids.json") 
TARGET_COUNTRY_NAME = None # Process all countries
MAX_DOWNLOADS_PER_SESSION = 20 
MAX_OPENVPN_DOWNLOADS_PER_SESSION = 20
RELOGIN_DELAY = 60

# Environment variables will be read once at runtime
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Create the download directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"Created download directory: {DOWNLOAD_DIR}")


class ProtonVPN:
    def __init__(self):
        # ... (Initialization code remains the same)
        self.options = webdriver.ChromeOptions()
        
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        
        prefs = {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True 
        }
        self.options.add_experimental_option("prefs", prefs)

        self.driver = None

    # --- Setup/Teardown/Log Management (Unchanged) ---
    def setup(self):
        """Initializes the WebDriver (Chrome) with Headless options.)"""
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_window_size(1936, 1048)
        self.driver.implicitly_wait(10)
        print("WebDriver initialized successfully in Headless mode (Chrome).")

    def teardown(self):
        """Closes the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed.")

    def load_downloaded_ids(self):
        """Loads the set of previously downloaded server IDs for both types."""
        if os.path.exists(SERVER_ID_LOG_FILE):
            try:
                with open(SERVER_ID_LOG_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('wireguard', [])), set(data.get('openvpn', []))
            except json.JSONDecodeError:
                print("Warning: Log file corrupted. Starting with empty lists.")
                return set(), set()
        return set(), set()

    def save_downloaded_ids(self, wireguard_ids, openvpn_ids):
        """Saves the set of downloaded server IDs for both types."""
        data = {
            'wireguard': list(wireguard_ids),
            'openvpn': list(openvpn_ids)
        }
        with open(SERVER_ID_LOG_FILE, 'w') as f:
            json.dump(data, f)
            
    # --- Login/Navigation/Logout (Unchanged) ---
    def login(self, username, password):
        try:
            self.driver.get("https://protonvpn.com/")
            time.sleep(1) 
            self.driver.find_element(By.XPATH, "//a[contains(@href, 'https://account.protonvpn.com/login')]").click()
            time.sleep(1) 
            user_field = self.driver.find_element(By.ID, "username")
            user_field.clear()
            user_field.send_keys(username)
            time.sleep(1) 
            self.driver.find_element(By.CSS_SELECTOR, ".button-large").click()
            time.sleep(1) 
            pass_field = self.driver.find_element(By.ID, "password")
            pass_field.clear()
            pass_field.send_keys(password)
            time.sleep(1) 
            self.driver.find_element(By.CSS_SELECTOR, ".button-large").click()
            time.sleep(3) 
            print("Login Successful.")
            return True
        except Exception as e:
            print(f"Error Login: {e}")
            return False

    def navigate_to_downloads(self):
        try:
            downloads_link_selector = (By.CSS_SELECTOR, ".navigation-item:nth-child(7) .text-ellipsis")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(downloads_link_selector)
            ).click()
            time.sleep(2) 
            print("Navigated to Downloads section.")
            return True
        except Exception as e:
            print(f"Error Navigating to Downloads: {e}")
            return False

    def logout(self):
        try:
            self.driver.get("https://account.protonvpn.com/logout") 
            time.sleep(1) 
            print("Logout Successful.")
            return True
        except Exception as e:
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".p-1").click()
                time.sleep(1)
                self.driver.find_element(By.CSS_SELECTOR, ".mb-4 > .button").click()
                time.sleep(1) 
                print("Logout Successful via UI.")
                return True
            except Exception as e:
                print(f"Error Logout: {e}")
                return False

    # --- WireGuard/IKEv2 Download (CRITICALLY MODIFIED) ---
    def process_wireguard_downloads(self, downloaded_ids):
        """
        Processes WireGuard/IKEv2 downloads for ALL countries, limited by MAX_DOWNLOADS_PER_SESSION.
        """
        print("\n--- Starting WireGuard/IKEv2 Download Session ---")
        try:
            self.driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1) 

            # CRITICAL: Click WireGuard/IKEv2 tab (first tab)
            wireguard_tab_selector = (By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(1) > .relative")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(wireguard_tab_selector)
            ).click()
            time.sleep(2) 

            # CRITICAL: Select Platform (based on user's successful finding)
            platform_select_selector = (By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(3) .radio-fakeradio")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(platform_select_selector)
            ).click()
            time.sleep(2)
            print("Platform set for WireGuard/IKEv2.")
            
            # ... (Rest of the WireGuard download logic remains the same)
            
            print(f"Found {len(downloaded_ids)} WireGuard server IDs already logged as downloaded.")

            countries = self.driver.find_elements(By.CSS_SELECTOR, ".mb-6 details")
            print(f"Found {len(countries)} total countries to check.")
            
            download_counter = 0
            all_downloads_finished = True 

            for country in countries:
                try:
                    country_name_element = country.find_element(By.CSS_SELECTOR, "summary")
                    country_name = country_name_element.text.split('\n')[0].strip()
                    
                    if download_counter >= MAX_DOWNLOADS_PER_SESSION:
                        print(f"Session limit reached ({MAX_DOWNLOADS_PER_SESSION}). Stopping for relogin...")
                        all_downloads_finished = False 
                        return all_downloads_finished, downloaded_ids
                    
                    print(f"--- Processing country (WireGuard): {country_name} ---")

                    self.driver.execute_script("arguments[0].open = true;", country)
                    time.sleep(0.5)

                    rows = country.find_elements(By.CSS_SELECTOR, "tr")
                    
                    all_configs_in_country_downloaded = True 

                    for index, row in enumerate(rows[1:]): 
                        
                        try:
                            file_cell = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
                            server_id = file_cell.text.strip()
                            
                            if server_id in downloaded_ids:
                                continue
                            
                            all_configs_in_country_downloaded = False
                            
                            if download_counter >= MAX_DOWNLOADS_PER_SESSION:
                                print(f"Session limit reached ({MAX_DOWNLOADS_PER_SESSION}). Stopping for relogin...")
                                all_downloads_finished = False 
                                return all_downloads_finished, downloaded_ids
                            
                            btn = row.find_element(By.CSS_SELECTOR, ".button")

                        except Exception as e:
                            # print(f"Could not determine Server ID/Button for row {index} in {country_name}. Error: {e}")
                            continue 

                        random_delay = random.randint(10, 20) 
                        
                        # --- Execute Download ---
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)

                            ActionChains(self.driver).move_to_element(btn).click().perform()

                            # Confirmation modal click
                            confirm_btn = WebDriverWait(self.driver, 30).until(
                                EC.element_to_be_clickable(CONFIRM_BUTTON_SELECTOR)
                            )
                            confirm_btn.click()

                            WebDriverWait(self.driver, 30).until(
                                EC.invisibility_of_element_located(MODAL_BACKDROP_SELECTOR)
                            )
                            
                            download_counter += 1
                            print(f"Successfully downloaded WG/IKEv2 config (Server ID: {server_id}). Total in session: {download_counter}. Waiting {random_delay}s...")
                            time.sleep(random_delay) 

                            downloaded_ids.add(server_id)
                            
                        except (TimeoutException, ElementClickInterceptedException) as e:
                            print(f"CRITICAL ERROR: Failed to download WG/IKEv2 config {server_id} in {country_name}. Rate limit or session issue detected. Shutting down session.")
                            all_downloads_finished = False
                            return all_downloads_finished, downloaded_ids
                        
                        except Exception as e:
                            print(f"General error during WG/IKEv2 download {server_id} in {country_name}: {e}. Shutting down session.")
                            all_downloads_finished = False
                            return all_downloads_finished, downloaded_ids
                            
                    if all_configs_in_country_downloaded:
                        print(f"All WG/IKEv2 configs for {country_name} were already downloaded. Moving to next country.")
                        
                except Exception as e:
                    print(f"Error processing country block for {country_name}: {e}. Continuing to next country.")
                    
            all_downloads_finished = True 

        except Exception as e:
            print(f"Error in main WireGuard download loop: {e}")
            all_downloads_finished = False
            
        return all_downloads_finished, downloaded_ids


    # --- OpenVPN Download Function (MODIFIED: Removed platform selection) ---
    def process_openvpn_downloads(self, downloaded_ids):
        """
        Processes OpenVPN downloads for ALL countries (relying on default/auto-selected platform).
        """
        print("\n--- Starting OpenVPN Download Session (Platform assumed to be set) ---")
        try:
            self.driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1) 

            # CRITICAL: Click OpenVPN tab (second tab)
            openvpn_tab_selector = (By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(2) > .relative")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(openvpn_tab_selector)
            ).click()
            time.sleep(2) 
            
            # --- REMOVED: Platform selection logic (as per user request, relying on auto-set) ---
            print("Relying on auto-set Platform (Android/Linux) for OpenVPN.")

            # 2. Iterate through countries and click 'Create'
            
            countries = self.driver.find_elements(By.CSS_SELECTOR, ".mb-6 details")
            download_counter = 0
            all_downloads_finished = True 

            for country in countries:
                try:
                    country_name_element = country.find_element(By.CSS_SELECTOR, "summary")
                    country_name = country_name_element.text.split('\n')[0].strip()
                    
                    if download_counter >= MAX_OPENVPN_DOWNLOADS_PER_SESSION:
                        print(f"Session limit reached ({MAX_OPENVPN_DOWNLOADS_PER_SESSION}). Stopping for relogin...")
                        all_downloads_finished = False 
                        return all_downloads_finished, downloaded_ids
                    
                    self.driver.execute_script("arguments[0].open = true;", country)
                    time.sleep(0.5)

                    rows = country.find_elements(By.CSS_SELECTOR, "tr")
                    
                    try:
                        udp_row = rows[-2] # UDP is typically the second to last row
                        tcp_row = rows[-1] # TCP is typically the last row
                    except IndexError:
                        print(f"Could not find UDP/TCP rows for {country_name}. Skipping.")
                        continue
                        
                    protocols = [
                        {'row': udp_row, 'protocol': 'UDP'},
                        {'row': tcp_row, 'protocol': 'TCP'}
                    ]
                    
                    country_finished = True

                    for item in protocols:
                        proto_row = item['row']
                        protocol = item['protocol']
                        
                        openvpn_server_id = f"{country_name.split()[0].upper()}-OpenVPN-{protocol}"
                        
                        if openvpn_server_id in downloaded_ids:
                            continue
                        
                        country_finished = False

                        if download_counter >= MAX_OPENVPN_DOWNLOADS_PER_SESSION:
                            print(f"Session limit reached ({MAX_OPENVPN_DOWNLOADS_PER_SESSION}). Stopping for relogin...")
                            all_downloads_finished = False 
                            return all_downloads_finished, downloaded_ids
                        
                        # Select the 'Create' button within the row
                        create_btn_selector = (By.CSS_SELECTOR, ".button")
                        create_btn = proto_row.find_element(*create_btn_selector)

                        random_delay = random.randint(60, 90) 
                        
                        print(f"--- Processing country (OpenVPN {protocol}): {country_name} ---")

                        # --- Execute Download ---
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", create_btn)
                            time.sleep(0.5)

                            ActionChains(self.driver).move_to_element(create_btn).click().perform()

                            # OpenVPN downloads immediately after clicking Create
                            
                            download_counter += 1
                            print(f"Successfully downloaded OpenVPN config (ID: {openvpn_server_id}). Total in session: {download_counter}. Waiting {random_delay}s...")
                            time.sleep(random_delay) 

                            downloaded_ids.add(openvpn_server_id)
                            
                        except Exception as e:
                            print(f"General error during OpenVPN download {openvpn_server_id} in {country_name}: {e}. Shutting down session.")
                            all_downloads_finished = False
                            return all_downloads_finished, downloaded_ids

                    if country_finished:
                        print(f"All OpenVPN configs for {country_name} were already downloaded. Moving to next country.")
                        
                except Exception as e:
                    print(f"Error processing country block for {country_name} (OpenVPN): {e}. Continuing to next country.")
                    
            all_downloads_finished = True 

        except Exception as e:
            print(f"Error in main OpenVPN download loop: {e}")
            all_downloads_finished = False
            
        return all_downloads_finished, downloaded_ids

    # --- File Organization and Run Loop (Unchanged) ---

    def organize_and_send_files(self):
        """
        Organizes downloaded files by country and sends a zip file for each country via Telegram.
        """
        print("\n###################### Organizing and Sending Files ######################")
        
        country_files = {}
        
        for filename in os.listdir(DOWNLOAD_DIR):
            if filename.endswith(".ovpn") or filename.endswith(".conf"):
                try:
                    
                    if "udp.ovpn" in filename or "tcp.ovpn" in filename:
                        # --- OpenVPN files ---
                        name_without_ext = filename.split('.')[0]
                        country_code = name_without_ext.split('_')[0].upper()
                        
                    else:
                        # --- WireGuard/IKEv2 files (using previous successful logic) ---
                        name_without_ext = filename.split('.')[0]
                        base_name = name_without_ext.split('(')[0].strip() 
                        
                        if base_name.startswith("wg-"):
                            name_without_prefix = base_name[3:]
                        else:
                            name_without_prefix = base_name
                            
                        country_code = name_without_prefix.split('-')[0].split('#')[0].upper()

                    if len(country_code) > 3 or not country_code.isalpha():
                        country_code = country_code[:3] if len(country_code) > 3 else country_code
                    
                    if country_code not in country_files:
                        country_files[country_code] = []
                    
                    country_files[country_code].append(os.path.join(DOWNLOAD_DIR, filename))
                    
                except Exception as e:
                    print(f"Error processing filename {filename}: {e}")

        if not country_files:
            print("No new configuration files found to organize/send.")
            return

        print(f"Found files for {len(country_files)} unique countries/groups: {', '.join(country_files.keys())}")

        # 2. Zip and Send each country's files
        for country_code, files in country_files.items():
            zip_filename = f"{country_code}_ProtonVPN_Configs.zip"
            zip_path = os.path.join(os.getcwd(), zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    zipf.write(file_path, os.path.basename(file_path))

            print(f"Created {zip_filename} with {len(files)} configurations.")

            # 3. Send to Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                caption = f"✅ کانفیگ‌های جدید WireGuard/OpenVPN برای کشور {country_code} ({len(files)} فایل)."
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

                try:
                    with open(zip_path, 'rb') as doc:
                        response = requests.post(url, 
                            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}, 
                            files={'document': doc}
                        )
                    if response.status_code == 200:
                        print(f"Successfully sent {zip_filename} to Telegram.")
                    else:
                        print(f"Failed to send {zip_filename} to Telegram. Status code: {response.status_code}, Response: {response.text}")
                except Exception as e:
                    print(f"Telegram API Error for {zip_filename}: {e}")
            else:
                print("Skipping Telegram send: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
            
            # 4. Clean up the created zip file
            os.remove(zip_path)
        
        print("File organization and sending process completed.")
        
        # 5. Clean up downloaded files and clear the log file
        print("Cleaning up individual configuration files...")
        for file in glob.glob(os.path.join(DOWNLOAD_DIR, '*')):
            os.remove(file)
        self.save_downloaded_ids(set(), set())


    def run(self, username, password):
        """Executes the full automation workflow with relogin cycle."""
        
        all_wg_finished = False
        all_ovpn_finished = False
        session_count = 0
        
        wg_ids, ovpn_ids = self.load_downloaded_ids()
        
        try:
            # Phase 1: Download WireGuard/IKEv2 until all are done
            while not all_wg_finished and session_count < 20: 
                session_count += 1
                print(f"\n###################### Starting Session {session_count} (Phase 1: WireGuard) ######################")
                
                self.setup()
                if not self.login(username, password):
                    print("Failed to log in. Aborting run.")
                    break
                
                if self.navigate_to_downloads():
                    all_wg_finished, wg_ids = self.process_wireguard_downloads(wg_ids)
                    self.save_downloaded_ids(wg_ids, ovpn_ids)
                
                self.logout()
                self.teardown() 
                
                if not all_wg_finished:
                    print(f"Session {session_count} completed. Waiting {RELOGIN_DELAY} seconds before relogging in...")
                    time.sleep(RELOGIN_DELAY) 
                
            
            # Phase 2: Download OpenVPN until all are done
            session_count = 0
            while all_wg_finished and not all_ovpn_finished and session_count < 20:
                session_count += 1
                print(f"\n###################### Starting Session {session_count} (Phase 2: OpenVPN) ######################")
                
                self.setup()
                if not self.login(username, password):
                    print("Failed to log in. Aborting run.")
                    break
                
                if self.navigate_to_downloads():
                    all_ovpn_finished, ovpn_ids = self.process_openvpn_downloads(ovpn_ids)
                    self.save_downloaded_ids(wg_ids, ovpn_ids)
                
                self.logout()
                self.teardown() 
                
                if not all_ovpn_finished:
                    print(f"Session {session_count} completed. Waiting {RELOGIN_DELAY} seconds before relogging in...")
                    time.sleep(RELOGIN_DELAY) 


            # Final step: Organize and send files if ALL phases are complete
            if all_wg_finished and all_ovpn_finished:
                print("\n###################### All configurations (WG & OVPN) downloaded successfully! ######################")
                self.organize_and_send_files()
            elif not all_wg_finished:
                print("Aborting: Could not finish WireGuard/IKEv2 downloads.")
            elif not all_ovpn_finished:
                print("Aborting: Could not finish OpenVPN downloads.")

        except Exception as e:
            print(f"Runtime Error in main loop: {e}")
        finally:
            self.teardown()


if __name__ == "__main__":
    USERNAME = os.environ.get("VPN_USERNAME")
    PASSWORD = os.environ.get("VPN_PASSWORD")
    
    if not USERNAME or not PASSWORD:
        print("---")
        print("ERROR: VPN_USERNAME or VPN_PASSWORD not loaded from environment variables.")
        print("Please configure them as Secrets in your GitHub repository.")
        print("---")
    else:
        print("Account info loaded from environment variables. Starting workflow...")
        proton = ProtonVPN()
        proton.run(USERNAME, PASSWORD)
