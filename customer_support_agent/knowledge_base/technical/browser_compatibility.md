# Browser Compatibility

## Supported Browsers

CloudSync Pro is tested and fully supported on the following browsers:

| Browser | Minimum Version | Recommended |
|---|---|---|
| Google Chrome | 90+ | Latest |
| Mozilla Firefox | 88+ | Latest |
| Apple Safari | 15+ | Latest |
| Microsoft Edge | 90+ | Latest |

**Not supported**: Internet Explorer (any version), Opera Mini, Samsung Internet versions below 16.

## Known Browser-Specific Issues

### Chrome
- **Extensions conflict**: Ad blockers (uBlock Origin, AdBlock Plus) may block CloudSync Pro's analytics endpoints, causing false "connection error" warnings. Add `*.cloudsyncpro.com` to your ad blocker's allowlist.
- **Memory usage**: Workspaces with 500+ tasks in a single view may consume over 2 GB of memory. Use filters to reduce visible items.

### Safari
- **File uploads**: Safari may not support drag-and-drop uploads for files larger than 100 MB. Use the file picker dialog instead.
- **Notifications**: Safari requires explicit permission for desktop notifications. Go to Safari > Settings > Websites > Notifications and allow `app.cloudsyncpro.com`.
- **Private browsing**: Local storage is limited in Safari Private Browsing mode, which may cause login sessions to expire frequently.

### Firefox
- **Enhanced Tracking Protection**: Firefox's strict tracking protection may block some third-party integration widgets (e.g., embedded Slack preview). Set tracking protection to "Standard" or add an exception for `app.cloudsyncpro.com`.

## Clearing Cache and Cookies

If you experience display issues, stale data, or unexpected errors:

1. **Chrome**: Settings > Privacy and Security > Clear Browsing Data > select "Cached images and files" and "Cookies and other site data" > Clear Data
2. **Firefox**: Settings > Privacy & Security > Cookies and Site Data > Clear Data
3. **Safari**: Safari > Settings > Privacy > Manage Website Data > search "cloudsyncpro" > Remove
4. **Edge**: Settings > Privacy, search, and services > Clear Browsing Data

After clearing cache, reload CloudSync Pro and log in again.

## Enabling JavaScript and Cookies

CloudSync Pro requires JavaScript and cookies to be enabled. If you see a blank white screen after login, verify:

1. JavaScript is enabled in your browser settings
2. Third-party cookies are allowed for `*.cloudsyncpro.com`
3. No browser extension is blocking scripts on the page
