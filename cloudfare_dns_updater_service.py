import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil
import configparser
import os
import requests
import time
from cloudflare import Cloudflare

# --- Configuration ---
# Create a file named 'config.ini' in the same directory as this script.
# Add the following content to 'config.ini' and fill in your details:
#
# [Cloudflare]
# api_token = YOUR_CLOUDFLARE_API_TOKEN
# zone_name = your_domain.com
# record_name = your_subdomain.your_domain.com
#
# [Service]
# update_interval_seconds = 300

class CloudflareDNSUpdaterService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CloudflareDNSUpdater"
    _svc_display_name_ = "Cloudflare DNS Updater Service"
    _svc_description_ = "Updates a Cloudflare DNS record with the current public IP address."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True
        self.config = configparser.ConfigParser()
        # Get the directory where the executable is running
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.config.read(os.path.join(self.app_dir, 'config.ini'))
        self.log_file = os.path.join(self.app_dir, 'service.log')
        self.last_synced_ip_file = os.path.join(self.app_dir, 'last_synced_ip.txt')
        self.last_synced_ip = self._load_last_synced_ip()

    def log(self, message):
        """Appends a log message to the service log file."""
        with open(self.log_file, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def _load_last_synced_ip(self):
        """Loads the last successfully synced public IP from a file."""
        try:
            if os.path.exists(self.last_synced_ip_file):
                with open(self.last_synced_ip_file, 'r') as f:
                    ip = f.read().strip()
                    if ip: # Ensure IP is not empty string
                        self.log(f"Loaded last synced IP: {ip}")
                        return ip
                    else:
                        self.log("Last synced IP file was empty. Will perform full check.")
                        return None
            else:
                self.log("Last synced IP file not found. Will perform full check.")
                return None
        except Exception as e:
            self.log(f"Error loading last synced IP: {e}")
            return None

    def _save_last_synced_ip(self, ip_address):
        """Saves the last successfully synced public IP to a file."""
        try:
            with open(self.last_synced_ip_file, 'w') as f:
                f.write(ip_address)
            self.log(f"Saved last synced IP: {ip_address}")
            self.last_synced_ip = ip_address # Update in-memory cache
        except Exception as e:
            self.log(f"Error saving last synced IP: {e}")

    def get_public_ip(self):
        """Fetches the current public IP address."""
        try:
            response = requests.get('https://api.ipify.org')
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            self.log(f"Error getting public IP: {e}")
            return None

    def update_dns(self):
        """The main logic for checking and updating the DNS record."""
        self.log("Service is running. Starting IP check.") # Changed log message

        current_public_ip = self.get_public_ip()
        if not current_public_ip:
            self.log("Could not determine public IP. Skipping check.")
            return

        self.log(f"Current public IP is: {current_public_ip}")

        if self.last_synced_ip == current_public_ip:
            self.log(f"Public IP ({current_public_ip}) matches last synced IP. No Cloudflare check needed.")
            return

        self.log(f"Public IP ({current_public_ip}) differs from last synced IP ({self.last_synced_ip}). Checking Cloudflare.")

        try:
            api_token = self.config.get('Cloudflare', 'api_token')
            zone_name = self.config.get('Cloudflare', 'zone_name')
            record_name = self.config.get('Cloudflare', 'record_name')
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            self.log(f"Configuration error: {e}. Please check your config.ini file.")
            return

        try:
            client = Cloudflare(api_token=api_token)

            # Get Zone ID
            zones_page = client.zones.list(name=zone_name)
            zones_list = list(zones_page)
            if not zones_list:
                self.log(f"Error: Zone '{zone_name}' not found.")
                return
            zone_id = zones_list[0].id
            self.log(f"Found Zone ID for '{zone_name}': {zone_id}")

            # Get DNS Record ID
            dns_records_page = client.dns.records.list(zone_id=zone_id, name=record_name, type='A')
            dns_records_list = list(dns_records_page)
            if not dns_records_list:
                self.log(f"Error: DNS record '{record_name}' not found.")
                return
            dns_record = dns_records_list[0]
            record_id = dns_record.id
            cloudflare_ip = dns_record.content
            self.log(f"Found DNS record for '{dns_record.name}' with IP: {cloudflare_ip}")

            # Compare and Update
            if current_public_ip == cloudflare_ip:
                self.log(f"IP addresses match (Cloudflare IP is {cloudflare_ip}). Updating local last synced IP to {current_public_ip}.")
                self._save_last_synced_ip(current_public_ip)
            else:
                self.log(f"IP has changed for {dns_record.name}. Current Public IP: {current_public_ip}, Cloudflare IP: {cloudflare_ip}. Updating Cloudflare DNS record to {current_public_ip}...")
                client.dns.records.update(
                    dns_record_id=record_id,
                    zone_id=zone_id,
                    type=dns_record.type,
                    name=dns_record.name,
                    content=current_public_ip,
                    ttl=int(dns_record.ttl),
                    proxied=dns_record.proxied
                )
                self.log("DNS record updated successfully on Cloudflare.")
                self._save_last_synced_ip(current_public_ip)

        except Exception as e:
            self.log(f"An error occurred during Cloudflare operations: {e}")
            # Do not update last_synced_ip if Cloudflare operations fail

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        self.log("Service is stopping.")

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        update_interval = int(self.config.get('Service', 'update_interval_seconds', fallback=300))
        while self.is_alive:
            self.update_dns()
            # Wait for the specified interval or until a stop signal is received
            win32event.WaitForSingleObject(self.hWaitStop, update_interval * 1000)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CloudflareDNSUpdaterService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CloudflareDNSUpdaterService)