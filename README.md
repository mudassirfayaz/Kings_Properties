# Kings Properties Web Scraper

A comprehensive Selenium-based web scraper for Kings Industrial real estate property listings with pagination handling and headless browser support.

## Features

- **Headless Browser Support**: Runs Chrome in headless mode for automated scraping
- **Pagination Handling**: Automatically navigates through all pages of listings
- **Comprehensive Data Extraction**: Extracts detailed property information including:
  - Property title and address
  - Location details
  - Listing type (FOR LEASE / FOR SALE)
  - Property images
  - Detailed specifications (size, price, spaces, etc.)
  - Property URLs and IDs
- **Robust Error Handling**: Graceful handling of missing elements and network issues
- **JSON Output**: Saves scraped data in structured JSON format
- **Logging**: Comprehensive logging to both file and console

## Prerequisites

- Python 3.7+
- Google Chrome browser installed
- ChromeDriver (automatically managed with webdriver-manager)

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with default settings:

```bash
python scraper.py
```

### Configuration Options

Edit the configuration section in `scraper.py`:

```python
# Configuration
URL = "file://" + "E:/Development/Kings/Kings_Properties/index.html"  # Local file
# For web URL, use: URL = "https://www.kingindustrial.com/properties"

HEADLESS = True  # Set to False to see browser
MAX_PAGES = None  # Set to number to limit pages, None for all pages
OUTPUT_FILE = "kings_items.json"
```

### Advanced Usage

You can also use the scraper programmatically:

```python
from scraper import KingsPropertiesScraper

# Initialize scraper
scraper = KingsPropertiesScraper(headless=True, timeout=30)

# Scrape all properties
properties = scraper.scrape_all_pages("your_url_here", max_pages=5)

# Save to JSON
scraper.save_to_json("output.json")
```

## Output Format

The scraper saves data in JSON format with the following structure:

```json
{
  "metadata": {
    "scraped_at": "2025-01-18T10:30:00",
    "total_properties": 25,
    "scraper_version": "1.0"
  },
  "properties": [
    {
      "property_id": "1417234-lease",
      "title": "605 Athena Drive",
      "location": "Athens, GA 30605",
      "listing_type": "FOR LEASE",
      "url": "https://www.kingindustrial.com/properties/?propertyId=1417234-lease",
      "image_url": "https://example.com/image.jpg",
      "details": {
        "available": "10,000 SF",
        "lease_rate": "Call Agent",
        "#_of_spaces": "3 Spaces",
        "building_size": "10,000 SF Bldg",
        "space_type": "Manufacturing"
      },
      "secondary_info": ["10,000 SF", "Call Agent", "3 Spaces", "10,000 SF Bldg", "Manufacturing"],
      "page_number": 1,
      "scraped_at": "2025-01-18T10:30:15"
    }
  ]
}
```

## Logging

The scraper creates detailed logs in:
- Console output (real-time)
- `scraper.log` file (persistent)

Log levels include:
- INFO: General progress information
- WARNING: Non-critical issues
- ERROR: Critical errors that stop execution
- DEBUG: Detailed debugging information

## Error Handling

The scraper handles various scenarios gracefully:
- Missing page elements
- Network timeouts
- WebDriver initialization issues
- Pagination navigation failures
- File I/O errors

## Customization

### Adding New Data Fields

To extract additional property information, modify the `extract_property_details()` method:

```python
# Add custom extraction logic
try:
    custom_element = property_element.find_element(By.CSS_SELECTOR, ".custom-class")
    property_data["custom_field"] = custom_element.text.strip()
except NoSuchElementException:
    property_data["custom_field"] = None
```

### Changing Browser Options

Modify Chrome options in the `__init__` method:

```python
# Add custom Chrome options
self.chrome_options.add_argument('--custom-option')
```

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   - Solution: Install webdriver-manager: `pip install webdriver-manager`

2. **Chrome browser not found**
   - Solution: Install Google Chrome browser

3. **Timeout errors**
   - Solution: Increase timeout value or check network connection

4. **Permission errors**
   - Solution: Run with appropriate permissions or change output directory

### Debug Mode

To run in debug mode with visible browser:

```python
scraper = KingsPropertiesScraper(headless=False)
```

## Performance

- Average scraping speed: 2-3 properties per second
- Memory usage: ~50-100MB depending on page size
- Network requirements: Stable internet connection for web scraping

## Legal Considerations

- Respect robots.txt files
- Implement rate limiting for production use
- Follow website terms of service
- Consider API alternatives when available

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scraper.
