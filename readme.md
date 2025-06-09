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
   - Edit `config.ini` and fill in your Cloudflare API token, zone name, record name, and update interval.

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
