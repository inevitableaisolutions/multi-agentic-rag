# Connectivity Issues

## Overview

If you are experiencing connection problems with CloudSync Pro, this guide covers common causes and troubleshooting steps. CloudSync Pro requires a stable internet connection with at least 1 Mbps bandwidth.

## Quick Diagnostic Steps

1. **Check our status page**: Visit status.cloudsyncpro.com to verify CloudSync Pro services are operational
2. **Test your internet**: Try loading other websites. If nothing loads, the issue is your network.
3. **Try a different browser**: Open CloudSync Pro in an incognito/private window to rule out extension conflicts
4. **Clear browser cache**: Cached assets can sometimes cause connection failures (see Browser Compatibility guide)

## Firewall and Proxy Configuration

CloudSync Pro requires access to the following domains. Ensure your firewall or proxy allows traffic to:

- `*.cloudsyncpro.com` (TCP ports 80 and 443)
- `api.cloudsyncpro.com` (TCP port 443)
- `ws.cloudsyncpro.com` (WebSocket, TCP port 443) -- required for real-time collaboration
- `cdn.cloudsyncpro.com` (TCP port 443) -- static assets
- `uploads.cloudsyncpro.com` (TCP port 443) -- file uploads and downloads

If your organization uses a web proxy, configure it to allow WebSocket connections to `ws.cloudsyncpro.com`. Without WebSocket support, real-time features (live cursors, instant task updates, chat) will not function.

## VPN Compatibility

CloudSync Pro is compatible with most VPN configurations. Known issues:

- **Split-tunnel VPNs**: Ensure CloudSync Pro domains are routed through the tunnel if your VPN blocks external traffic by default
- **VPNs with SSL inspection**: Add `*.cloudsyncpro.com` to the SSL inspection bypass list. SSL inspection can cause certificate errors (`ERR_CERT_AUTHORITY_INVALID`)
- **High-latency VPNs**: Connections with latency above 500ms may cause WebSocket disconnections. The app will display a yellow "Reconnecting..." banner.

## Error Messages

- **"Unable to connect to CloudSync Pro"**: Check internet and firewall settings above.
- **"Real-time sync disconnected"**: WebSocket connection lost. Usually reconnects automatically within 10 seconds. If persistent, check WebSocket/proxy settings.
- **"Request timed out (ERR_TIMEOUT)"**: Server did not respond within 30 seconds. Check status page and retry.

## Corporate Network Troubleshooting

If you are on a corporate network with strict security policies, contact your IT administrator and provide them with the domain allowlist above. We also offer a network diagnostic tool at app.cloudsyncpro.com/diagnostics that tests connectivity to all required endpoints and generates a report you can share with your IT team.
