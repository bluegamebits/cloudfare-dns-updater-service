# Cloudflare DNS Updater Service

This service automatically updates a Cloudflare DNS A record with your current public IP address. It is designed to run as a Windows service.

## Prerequisites

- Python 3.x installed
- Required Python packages:
  - `requests`
  - `cloudflare-python` (or the correct Cloudflare API library)
  - `pywin32`
- A valid Cloudflare API token with DNS edit permissions

## Setup

1. **Clone or copy the files to a folder** (e.g., `C:\cloudfare_dns_updater_service`).
2. **Install dependencies** (in an Administrator Command Prompt or PowerShell):

   ```bash
   pip install requests cloudflare-python pywin32
   ```

3. **Configure the service**:

- Create a file named 'config.ini' in the same directory as this script.
- Add the following content to 'config.ini' and fill in your details:
  
    ```bash
    # [Cloudflare]
    # api_token = YOUR_CLOUDFLARE_API_TOKEN
    # zone_name = your_domain.com
    # record_name = your_subdomain.your_domain.com
    #
    # [Service]
    # update_interval_seconds = 300
    ```

4. **Install and start the service**:

    ```bash
    python cloudfare_dns_updater_service.py install
    python cloudfare_dns_updater_service.py start
    ```

## Service Commands

Run these commands in the folder containing `cloudfare_dns_updater_service.py`.  
**You must run these commands as Administrator.**

### Install the Service

```bash
python cloudfare_dns_updater_service.py install
```

### Start the Service

```bash
python cloudfare_dns_updater_service.py start
```

### Stop the Service

```bash
python cloudfare_dns_updater_service.py stop
```

### Restart the Service

```bash
python cloudfare_dns_updater_service.py restart
```

### Uninstall the Service

```bash
python cloudfare_dns_updater_service.py remove
```

## Logs

- Service logs are written to `service.log` in the same directory.

## Notes

- The service only updates the DNS record if your public IP address changes.
- Ensure your API token has permission to edit DNS records for your zone.
- To check the service status, use Windows Services Manager or:

  ```bash
  python cloudfare_dns_updater_service.py status
  ```
