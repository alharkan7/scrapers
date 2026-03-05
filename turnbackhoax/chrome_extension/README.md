# TurnBackHoax Chrome Extension

A Chrome extension to manually save headlines from TurnBackHoax article pages.

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select the `turnbackhoax-extension` folder

## Usage

1. Navigate to a TurnBackHoax articles page (e.g., `https://turnbackhoax.id/articles?dateRange=August+2025&page=44`)
2. Click the extension icon in Chrome toolbar
3. Click **"💾 Save This Page"** to save all headlines from the current page
4. Navigate to the next page manually and repeat
5. When done, click **"📥 Download CSV"** to save all collected headlines

## Features

- ✅ Saves headlines with full metadata (title, URL, preview, image, date, category)
- ✅ Tracks page number and date range automatically from URL
- ✅ Deduplicates by URL - won't save the same article twice
- ✅ Stores data locally in Chrome - persists between browser sessions
- ✅ Downloads as CSV compatible with the main Python scraper

## Notes

- The extension stores data in Chrome's local storage
- Data persists until you click "Clear All Data" or uninstall the extension
- The CSV format matches the Python scraper output for easy merging

## Troubleshooting

**If the extension doesn't work after installation or updates:**
1. Go to `chrome://extensions/`
2. Find "TurnBackHoax Headline Scraper"
3. Click the refresh/reload icon (⟳) on the extension card
4. Try again

**If you see errors:**
- Make sure you're on a valid TurnBackHoax articles page (e.g., `https://turnbackhoax.id/articles`)
- Check that Developer mode is enabled in `chrome://extensions/`
- Try reloading the extension
