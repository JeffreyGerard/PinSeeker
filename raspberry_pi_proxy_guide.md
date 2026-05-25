# 🍓 Raspberry Pi 3 Residential Proxy Setup Guide

This guide describes how to transform your home Raspberry Pi 3 into a secure HTTP or SOCKS5 residential proxy. Routing your Cloud Run automation traffic through this proxy allows the booking engine to bypass bot-detection algorithms that block Google Cloud Platform (GCP) IP ranges.

---

## 🔒 Security Architectures: Choose Your Route

There are two primary ways to connect Cloud Run to your Raspberry Pi proxy:

| Feature | Option A: Secure Dynamic Tunnel (Recommended) | Option B: Standard Port Forwarding |
| :--- | :--- | :--- |
| **Complexity** | 🟢 Low (Zero router configuration) | 🟡 Medium (Requires router access) |
| **Security** | 🛡️ Extremely High (No exposed public ports) | ⚠️ Standard (Exposes a port to the web) |
| **IP Stability** | 🔄 Works behind CGNAT & dynamic home IPs | ❌ Breaks if home IP changes (needs DDNS) |
| **Technology** | **Tailscale** or **Cloudflare Tunnel** | **DDNS** (e.g. DuckDNS) + Router Port Forwarding |

---

### Option A: The Secure Tunnel Route (Recommended)

Using **Tailscale** is the easiest, most secure, and robust way to connect your Cloud Run service to your home Raspberry Pi. It creates a secure, encrypted virtual private network (mesh network) between GCP and your home Pi.

1. **Install Tailscale on the Raspberry Pi**:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. **Authorize the Cloud Run service**:
   We will configure Cloud Run to connect to the Tailscale network during deployment, allowing it to address your Raspberry Pi using its stable Tailscale IP (e.g., `100.x.y.z`) safely without any router configuration!

---

### Option B: The Port Forwarding Route

If you prefer direct connection, you must forward a port on your home router.

1. **Static IP**: Assign a static LAN IP to your Raspberry Pi in your home router settings (e.g., `192.168.1.150`).
2. **Port Forward**: Forward a custom external port (e.g., `8888`) to the Raspberry Pi's proxy port (`8888` for HTTP or `1080` for SOCKS5) on your router.
3. **Dynamic DNS (DDNS)**: If your home ISP changes your public IP frequently, set up [DuckDNS](https://www.duckdns.org/) or [No-IP](https://www.noip.com/) on the Pi to maintain a stable address (e.g., `myhome.duckdns.org`).

---

## 🛠️ Step-by-Step Proxy Server Installation

Log into your Raspberry Pi via SSH and follow the instructions below to install either an **HTTP Proxy (Squid)** or a **SOCKS5 Proxy (Dante)**.

### Path 1: Install Squid (HTTP/HTTPS Proxy)

Squid is a robust, widely-supported HTTP proxy.

1. **Update packages and install Squid**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y squid apache2-utils
   ```

2. **Generate your proxy credentials**:
   Replace `myusername` and `mypassword` with your desired proxy authentication credentials:
   ```bash
   sudo htpasswd -cb /etc/squid/passwd myusername mypassword
   ```

3. **Configure Squid**:
   Backup and overwrite the configuration file `/etc/squid/squid.conf`:
   ```bash
   sudo mv /etc/squid/squid.conf /etc/squid/squid.conf.bak
   sudo nano /etc/squid/squid.conf
   ```
   Paste the following config:
   ```text
   # Define proxy port
   http_port 8888

   # Configure Basic Authentication using the passwd file
   auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwd
   auth_param basic children 5
   auth_param basic realm PinSeeker Secure Residential Proxy
   auth_param basic credentialsttl 2 hours

   # Create ACLs
   acl authenticated proxy_auth REQUIRED
   acl SSL_ports port 443
   acl Safe_ports port 80          # http
   acl Safe_ports port 443         # https

   # Deny requests to unsafe ports
   http_access deny !Safe_ports
   
   # Require authentication
   http_access allow authenticated
   
   # Deny everything else
   http_access deny all
   ```

4. **Restart Squid**:
   ```bash
   sudo systemctl restart squid
   sudo systemctl enable squid
   ```

---

### Path 2: Install Dante (SOCKS5 Proxy)

SOCKS5 is faster and operates at a lower network layer, making it extremely efficient for scraping.

1. **Install Dante Server**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y dante-server
   ```

2. **Create a Proxy User**:
   Dante uses standard Linux users for authentication. Create a dedicated user for your proxy:
   ```bash
   sudo useradd -r -s /bin/false proxyuser
   echo "proxyuser:proxypassword" | sudo chpasswd
   ```

3. **Configure Dante**:
   Backup and overwrite `/etc/dftpd.conf` (or `/etc/dante.conf`):
   ```bash
   sudo mv /etc/dftpd.conf /etc/dftpd.conf.bak
   sudo nano /etc/dftpd.conf
   ```
   Paste the following config (replace `eth0` or `wlan0` with your active Pi interface):
   ```text
   logoutput: stderr

   # Port Dante listens on
   internal: 0.0.0.0 port = 1080

   # Interface used for outgoing requests (e.g. eth0 or wlan0)
   external: eth0

   # Authentication method (username/password)
   socksmethod: username
   clientmethod: none

   # Allow all clients to connect to the internal port
   client pass {
       from: 0.0.0.0/0 to: 0.0.0.0/0
       log: connect disconnect error
   }

   # Pass traffic when authenticated
   socks pass {
       from: 0.0.0.0/0 to: 0.0.0.0/0
       command: connect
       log: connect disconnect error
   }
   ```

4. **Restart Dante**:
   ```bash
   sudo systemctl restart danted
   sudo systemctl enable danted
   ```

---

## 🧪 Testing Your Residential Proxy

From your personal computer or any separate terminal, test the proxy server to verify that it correctly intercepts traffic and reports your home IP address:

```bash
# Test HTTP Proxy (Squid)
curl --proxy http://myusername:mypassword@<PI_IP>:8888 https://ifconfig.me

# Test SOCKS5 Proxy (Dante)
curl --socks5-hostname proxyuser:proxypassword@<PI_IP>:1080 https://ifconfig.me
```

This should return your **home residential public IP** instead of your local/office network IP!
Once confirmed, you are ready to configure these credentials inside your PinSeeker Cloud Run deployment environment.
