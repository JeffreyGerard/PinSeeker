# 🍓 Raspberry Pi 3 Residential Proxy Setup Guide (Modern Edition)

This guide provides a bulletproof, single-command setup to transform a Raspberry Pi 3 into a secure SOCKS5 residential proxy. This "Modern Edition" is optimized for **Debian 13 (Trixie)**, uses **Docker** to bypass missing native packages, and is designed to run within the **1GB RAM** constraints of the Pi 3.

Routing your Cloud Run automation traffic through this proxy allows your booking engine to bypass bot-detection algorithms that block Google Cloud Platform (GCP) IP ranges.

---

## 🔒 Security Architecture: Tailscale Tunnel

To ensure maximum security with zero configuration of your home router, we use **Tailscale**. This creates a secure, encrypted virtual private network (mesh network) between GCP and your home Pi.

*   **No Exposed Ports**: Your Pi remains invisible to the public internet.
*   **CGNAT Compatible**: Works even if your ISP uses Carrier-Grade NAT.
*   **Stable Identity**: Your Pi gets a stable internal IP (e.g., `100.x.y.z`) that doesn't change.

### 1. Install Tailscale
Run this on your Raspberry Pi:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Follow the login link provided in the terminal to authenticate your Pi.

---

## 🛠️ Step-by-Step Proxy Installation

We use a lightweight Docker container for the proxy. This ensures compatibility with Debian Trixie and keeps memory usage extremely low.

### 2. Install Docker
If Docker isn't installed, run the official convenience script:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect
```

### 3. Deploy the SOCKS5 Proxy
Replace `YOUR_USERNAME` and `YOUR_PASSWORD` with secure credentials. This command pulls an ultra-lightweight `go-socks5-proxy` image and runs it as a background service that auto-restarts on reboot.

```bash
docker run -d \
  --name pinseeker-proxy \
  --restart always \
  -p 1080:1080 \
  -e PROXY_USER=YOUR_USERNAME \
  -e PROXY_PASSWORD=YOUR_PASSWORD \
  serjs/go-socks5-proxy
```

---

## 🧪 Testing Your Residential Proxy

From your personal computer (or any device also on your Tailscale network), test the proxy server to verify that it correctly intercepts traffic and reports your home IP address. 

**Note**: Use the **Tailscale IP** of your Pi (found by running `tailscale ip -4` on the Pi).

```bash
# Test SOCKS5 Proxy
curl --socks5-hostname YOUR_USERNAME:YOUR_PASSWORD@<TAILSCALE_IP>:1080 https://ifconfig.me
```

### Expected Result
The command should return your **home residential public IP** (check it at [whatismyip.com](https://www.whatismyip.com) first to verify).

---

## 🚀 Cloud Run Integration

When deploying your PinSeeker service to Cloud Run:
1.  Ensure the Cloud Run service is connected to your Tailscale network (via Tailscale's [Cloud Run integration](https://tailscale.com/kb/1278/cloud-run/)).
2.  Set the `PROXY_URL` environment variable in Cloud Run:
    `socks5://YOUR_USERNAME:YOUR_PASSWORD@<TAILSCALE_IP>:1080`

> **💡 Pro-Tip for Playwright Users:**
> SOCKS5 credentials in a URL string can sometimes fail if your password contains special characters (like `#`, `@`, or `?`). For maximum reliability in your automation scripts, pass credentials explicitly during browser launch:
>
> ```python
> browser = playwright.chromium.launch(
>     proxy={
>         "server": "socks5://<TAILSCALE_IP>:1080",
>         "username": "YOUR_USERNAME",
>         "password": "YOUR_PASSWORD"
>     }
> )
> ```

Your automation traffic will now appear to originate from your living room!

