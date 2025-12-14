# 🛡️ ProtonVPN WireGuard Config Auto-Fetcher

This project provides an automated solution using Python/Selenium and GitHub Actions to regularly fetch and update the latest **WireGuard** configuration files from a ProtonVPN account.

The downloaded configuration files are automatically updated in this repository and are pushed to the corresponding Telegram channel for notifications.

---

## ⚡️ Quick Access & Download

Find the freshest WireGuard config package, neatly sorted into country-specific folders.

### 📥 Direct Download Link (ZIP File)

Use the link below to download the ZIP file containing all the latest configuration files:

[**Download Full WireGuard Config Package**](https://raw.githubusercontent.com/[YOUR_USERNAME]/[YOUR_REPOSITORY_NAME]/main/ProtonVPN_WireGuard_Configs.zip)

> **Note:** Please replace `[YOUR_USERNAME]` and `[YOUR_REPOSITORY_NAME]` with your actual GitHub username and repository name.

### 📢 Telegram Notification Channel

To receive the latest updates and notifications whenever the configurations are refreshed, join the Telegram channel:

[**ProtonConfigBot - VPN Configs**](https://t.me/ProtonConfigBot)

---

## 💻 Usage Guide (Windows Focus)

These WireGuard configuration files (`.conf`) are optimized for seamless use in a Windows environment.

### 📌 Recommended Tool for Optimal Performance (Windows)

For the best performance, stability, and compatibility on Windows, it is **highly recommended** to use the following client instead of the official WireGuard application:

* **Wiresock VPN Client (Recommended)**
    * **Link:** [https://www.wiresock.net](https://www.wiresock.net)

Wiresock is a robust client that supports the WireGuard protocol, offering superior performance in connection management and traffic handling on Windows systems.

### How to Use the Config Files:

1.  Download the **ProtonVPN_WireGuard_Configs.zip** file.
2.  Extract the ZIP file. (Files are organized into folders by two-letter country codes, such as `US`, `DE`, `NL`.)
3.  Install and launch the Wiresock software.
4.  Import your desired `.conf` files from the country folders into Wiresock and connect.

---

## ⚙️ Project Technical Structure

* **Primary Language:** Python 3
* **Web Automation:** Selenium + Chrome Headless
* **Scheduler:** GitHub Actions (Runs every 4 hours)
* **Output:** A single zipped file (folder-structured) and a Telegram notification message.
