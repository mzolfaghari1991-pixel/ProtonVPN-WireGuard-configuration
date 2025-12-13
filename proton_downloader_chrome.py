import os
import time
import random 
import glob 
import json 
import zipfile 
import requests 
import re 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# --- Constants ---
MODAL_BACKDROP_SELECTOR = (By.CLASS_NAME, "modal-two-backdrop")
CONFIRM_BUTTON_SELECTOR = (By.CSS_SELECTOR, ".button-solid-norm:nth-child(2)")
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloaded_configs")
SERVER_ID_LOG_FILE = os.path.join(os.getcwd(), "downloaded_server_ids.json") 
MAX_DOWNLOADS_PER_SESSION = 20 
MAX_OPENVPN_DOWNLOADS_PER_SESSION = 5 
RELOGIN_DELAY = 120 

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class ProtonVPN:
    def __init__(self):
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

    def setup(self):
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_window_size(1936, 1048)
        self.driver.implicitly_wait(10)
        print("WebDriver initialized.")

    def teardown(self):
        if self.driver:
            self.driver.quit()
            print("WebDriver closed.")

    def load_downloaded_ids(self):
        if os.path.exists(SERVER_ID_LOG_FILE):
            try:
                with open(SERVER_ID_LOG_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('wireguard', [])), set(data.get('openvpn', []))
            except json.JSONDecodeError:
                return set(), set()
        return set(), set()

    def save_downloaded_ids(self, wireguard_ids, openvpn_ids):
        data = {'wireguard': list(wireguard_ids), 'openvpn': list(openvpn_ids)}
        with open(SERVER_ID_LOG_FILE, 'w') as f:
            json.dump(data, f)
            
    def login(self, username, password):
        try:
            self.driver.get("https://protonvpn.com/")
            time.sleep(1) 
            self.driver.find_element(By.XPATH, "//a[contains(@href, 'https://account.protonvpn.com/login')]").click()
            time.sleep(1) 
            self.driver.find_element(By.ID, "username").send_keys(username)
            time.sleep(1) 
            self.driver.find_element(By.CSS_SELECTOR, ".button-large").click()
            time.sleep(1) 
            self.driver.find_element(By.ID, "password").send_keys(password)
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
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".navigation-item:nth-child(7) .text-ellipsis"))
            ).click()
            time.sleep(2) 
            return True
        except Exception as e:
            print(f"Error Navigating to Downloads: {e}")
            return False

    def logout(self):
        try:
            self.driver.get("https://account.protonvpn.com/logout") 
            time.sleep(1) 
            return True
        except Exception:
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".p-1").click()
                time.sleep(1)
                self.driver.find_element(By.CSS_SELECTOR, ".mb-4 > .button").click()
                time.sleep(1) 
                return True
            except:
                return False

    # --- WireGuard Logic (Unchanged) ---
    def process_wireguard_downloads(self, downloaded_ids):
        print("\n--- Starting WireGuard/IKEv2 Download Session ---")
        try:
            self.driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1) 
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(1) > .relative"))).click()
            time.sleep(2) 
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(3) .radio-fakeradio"))).click()
            time.sleep(2)
            
            countries = self.driver.find_elements(By.CSS_SELECTOR, ".mb-6 details")
            download_counter = 0
            all_downloads_finished = True 

            for country in countries:
                try:
                    country_name = country.find_element(By.CSS_SELECTOR, "summary").text.split('\n')[0].strip()
                    if download_counter >= MAX_DOWNLOADS_PER_SESSION:
                        print(f"Session limit ({MAX_DOWNLOADS_PER_SESSION}) reached.")
                        return False, downloaded_ids
                    
                    self.driver.execute_script("arguments[0].open = true;", country)
                    time.sleep(0.5)
                    rows = country.find_elements(By.CSS_SELECTOR, "tr")
                    all_configs_in_country_downloaded = True 

                    for row in rows[1:]: 
                        try:
                            server_id = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                            if server_id in downloaded_ids: continue
                            
                            all_configs_in_country_downloaded = False
                            if download_counter >= MAX_DOWNLOADS_PER_SESSION: return False, downloaded_ids
                            
                            btn = row.find_element(By.CSS_SELECTOR, ".button")
                            
                            # Random delay 60-90s
                            random_delay = random.randint(60, 90)
                            
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)
                            ActionChains(self.driver).move_to_element(btn).click().perform()
                            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable(CONFIRM_BUTTON_SELECTOR)).click()
                            WebDriverWait(self.driver, 30).until(EC.invisibility_of_element_located(MODAL_BACKDROP_SELECTOR))
                            
                            download_counter += 1
                            print(f"[WG] Downloaded {server_id}. Waiting {random_delay}s...")
                            time.sleep(random_delay) 
                            downloaded_ids.add(server_id)
                        except Exception: continue 
                            
                    if all_configs_in_country_downloaded:
                        print(f"[WG] All configs for {country_name} done.")
                except Exception: continue
        except Exception as e: print(f"WG Loop Error: {e}")
        return True, downloaded_ids

    # --- OpenVPN Logic (Random Delay Restored) ---
    def process_openvpn_downloads(self, downloaded_ids):
        print("\n--- Starting OpenVPN Download Session ---")
        try:
            self.driver.execute_script("window.scrollTo(0,0)")
            time.sleep(1) 
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".flex:nth-child(4) > .mr-8:nth-child(2) > .relative"))).click()
            time.sleep(2) 
            
            countries = self.driver.find_elements(By.CSS_SELECTOR, ".mb-6 details")
            download_counter = 0
            
            for country in countries:
                try:
                    country_name = country.find_element(By.CSS_SELECTOR, "summary").text.split('\n')[0].strip()
                    if download_counter >= MAX_OPENVPN_DOWNLOADS_PER_SESSION:
                        print(f"Session limit ({MAX_OPENVPN_DOWNLOADS_PER_SESSION}) reached.")
                        return False, downloaded_ids
                    
                    self.driver.execute_script("arguments[0].open = true;", country)
                    time.sleep(0.5)
                    rows = country.find_elements(By.CSS_SELECTOR, "tr")
                    
                    try: protocols = [{'row': rows[-2], 'proto': 'UDP'}, {'row': rows[-1], 'proto': 'TCP'}]
                    except: continue
                        
                    for item in protocols:
                        sid = f"{country_name.split()[0].upper()}-OpenVPN-{item['proto']}"
                        if sid in downloaded_ids: continue
                        
                        if download_counter >= MAX_OPENVPN_DOWNLOADS_PER_SESSION: return False, downloaded_ids
                        
                        btn = item['row'].find_element(By.CSS_SELECTOR, ".button")
                        
                        # Random delay 60-90s (Restored as requested)
                        random_delay = random.randint(60, 90)
                        
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        ActionChains(self.driver).move_to_element(btn).click().perform()
                        
                        download_counter += 1
                        print(f"[OVPN] Downloaded {sid}. Waiting {random_delay}s...")
                        time.sleep(random_delay)
                        downloaded_ids.add(sid)

                    print(f"[OVPN] {country_name} done.")
                except Exception: continue
        except Exception as e: print(f"OVPN Loop Error: {e}")
        return True, downloaded_ids

    # --- NEW: Improved Parsing & Grouped Zipping ---
    def organize_and_send_files(self):
        print("\n###################### Organizing and Sending Files (Grouped) ######################")
        
        # Mapping to force standard 2-letter codes
        COUNTRY_MAP = {
            'unitedstates': 'US', 'netherlands': 'NL', 'japan': 'JP', 'romania': 'RO',
            'poland': 'PL', 'switzerland': 'CH', 'mexico': 'MX', 'norway': 'NO',
            'canada': 'CA', 'singapore': 'SG', 'ireland': 'IE', 'iceland': 'IS',
            'france': 'FR', 'germany': 'DE', 'unitedkingdom': 'UK', 'italy': 'IT',
            'spain': 'ES', 'sweden': 'SE', 'australia': 'AU', 'brazil': 'BR'
        }

        wg_files = {} # {'US': [file1, file2], 'NL': [file3]}
        ovpn_files = {}

        # 1. Parse and Sort Files
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            # Clean filename
            name_no_ext = filename.rsplit('.', 1)[0]
            clean_name = re.sub(r'\s*\(\d+\)$', '', name_no_ext).strip().lower() # remove (1), (2)
            
            country_code = 'OTHER'

            if filename.endswith(".conf"):
                # WireGuard Logic
                prefix = clean_name.replace("wg-", "")
                code = prefix.split('-')[0].split('#')[0].upper()
                if len(code) == 2 and code.isalpha():
                    country_code = code
                
                if country_code not in wg_files: wg_files[country_code] = []
                wg_files[country_code].append(file_path)

            elif filename.endswith(".ovpn"):
                # OpenVPN Logic
                parts = clean_name.split('_')
                if len(parts) >= 1:
                    c_name = parts[0]
                    if c_name in COUNTRY_MAP:
                        country_code = COUNTRY_MAP[c_name]
                    else:
                        country_code = c_name[:2].upper()
                
                if country_code not in ovpn_files: ovpn_files[country_code] = []
                ovpn_files[country_code].append(file_path)

        # 2. Create and Send ZIPs (Only 2 Zip files total)
        self.create_and_send_zip("WireGuard", ".conf", wg_files)
        self.create_and_send_zip("OpenVPN", ".ovpn", ovpn_files)

        # 3. Cleanup
        print("Cleaning up...")
        for file in glob.glob(os.path.join(DOWNLOAD_DIR, '*')):
            os.remove(file)
        self.save_downloaded_ids(set(), set())

    def create_and_send_zip(self, proto_name, ext, grouped_data):
        if not grouped_data:
            print(f"No files found for {proto_name}.")
            return

        total_files = sum(len(v) for v in grouped_data.values())
        print(f"Preparing {proto_name} Zip: {total_files} files across {len(grouped_data)} countries.")
        
        zip_filename = f"ProtonVPN_All_{proto_name}_Configs.zip"
        zip_path = os.path.join(os.getcwd(), zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for country, files in grouped_data.items():
                for file_path in files:
                    # Create folder structure inside ZIP: e.g. US/file.conf
                    archive_name = os.path.join(country, os.path.basename(file_path))
                    zipf.write(file_path, arcname=archive_name)

        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            caption = (
                f"✅ **پکیج کامل کانفیگ‌های {proto_name}**\n\n"
                f"📂 **ساختار:** پوشه‌بندی شده بر اساس کشور\n"
                f"🌍 **تعداد کشورها:** {len(grouped_data)}\n"
                f"📄 **تعداد کل فایل‌ها:** {total_files}\n"
                f"ℹ️ **فرمت:** {ext}\n\n"
                f"🔹 فایل‌ها درون ZIP به تفکیک کشور مرتب شده‌اند."
            )
            
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
                with open(zip_path, 'rb') as doc:
                    requests.post(url, 
                        data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                        files={'document': doc}
                    )
                print(f"Sent {zip_filename} to Telegram.")
            except Exception as e:
                print(f"Telegram Error: {e}")
        
        os.remove(zip_path)

    def run(self, username, password):
        wg_done = False
        ovpn_done = False
        session = 0
        wg_ids, ovpn_ids = self.load_downloaded_ids()
        
        try:
            # Phase 1: WireGuard
            while not wg_done and session < 20: 
                session += 1
                self.setup()
                if self.login(username, password) and self.navigate_to_downloads():
                    wg_done, wg_ids = self.process_wireguard_downloads(wg_ids)
                    self.save_downloaded_ids(wg_ids, ovpn_ids)
                self.logout()
                self.teardown()
                if not wg_done: time.sleep(RELOGIN_DELAY)
            
            # Phase 2: OpenVPN
            session = 0
            while wg_done and not ovpn_done and session < 20:
                session += 1
                self.setup()
                if self.login(username, password) and self.navigate_to_downloads():
                    ovpn_done, ovpn_ids = self.process_openvpn_downloads(ovpn_ids)
                    self.save_downloaded_ids(wg_ids, ovpn_ids)
                self.logout()
                self.teardown()
                if not ovpn_done: time.sleep(RELOGIN_DELAY)

            if wg_done and ovpn_done:
                self.organize_and_send_files()

        except Exception as e: print(f"Fatal Error: {e}")
        finally: self.teardown()

if __name__ == "__main__":
    U = os.environ.get("VPN_USERNAME")
    P = os.environ.get("VPN_PASSWORD")
    if U and P: 
        ProtonVPN().run(U, P)
    else: 
        print("Missing Credentials.")
