#!/usr/bin/env python3
"""
Kings Properties Web Scraper
Scrapes property listings from Kings Industrial real estate website with pagination handling
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KingsPropertiesScraper:
    """Scraper for Kings Properties real estate listings"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for element waits
        """
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.scraped_properties = []
        
        # Set up Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        
        # Additional Chrome options for better scraping
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
    def setup_driver(self):
        """Initialize the Chrome WebDriver"""
        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                # Use webdriver-manager to automatically download and manage ChromeDriver
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            else:
                # Fallback to system ChromeDriver
                self.driver = webdriver.Chrome(options=self.chrome_options)
                
            self.driver.set_page_load_timeout(self.timeout)
            self.wait = WebDriverWait(self.driver, self.timeout)
            logger.info("WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error("Make sure Chrome browser is installed and ChromeDriver is available")
            logger.error("Install dependencies: pip install selenium webdriver-manager")
            raise
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def wait_for_page_load(self):
        """Wait for the page to fully load"""
        try:
            # Wait for the page body to be present
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Initial wait for page to fully load
            logger.info("Waiting for page to fully load...")
            time.sleep(10)  # Longer initial wait for dynamic content and JavaScript
            
            # Wait for any loading indicators to disappear
            self.wait_for_loading_to_complete()
            
            # Perform scrolling to trigger any lazy loading
            self.scroll_page()
            
            # Wait for any additional loading after scrolling
            self.wait_for_loading_to_complete()
            
            # Additional wait after scrolling
            time.sleep(3)
            
            # Try multiple possible selectors for property listings
            possible_selectors = [
                ".js-listing-container",
                ".property-listing",
                ".listing-item",
                ".property-item",
                ".property-card",
                "[class*='property']",
                "[class*='listing']"
            ]
            
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found elements with selector: {selector} ({len(elements)} elements)")
                        return
                except:
                    continue
                    
            logger.warning("No property containers found with standard selectors")
            
        except TimeoutException:
            logger.warning("Page load timeout - continuing anyway")
    
    def debug_page_structure(self):
        """Debug method to inspect page structure"""
        try:
            logger.info("=== DEBUGGING PAGE STRUCTURE ===")
            
            # Get page title
            title = self.driver.title
            logger.info(f"Page title: {title}")
            
            # Get current URL
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check for common property-related elements
            debug_selectors = [
                "div[class*='property']",
                "div[class*='listing']", 
                "div[class*='item']",
                "div[class*='card']",
                "a[href*='property']",
                ".grid-item",
                ".property",
                ".listing",
                "[data-property]"
            ]
            
            for selector in debug_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        # Log first element's HTML for inspection
                        if elements:
                            first_element_html = elements[0].get_attribute('outerHTML')[:500]
                            logger.info(f"First element HTML preview: {first_element_html}...")
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
            
            # Check for pagination elements
            pagination_selectors = [
                ".pagination",
                ".pager", 
                "[class*='page']",
                "button[class*='page']",
                "a[class*='page']"
            ]
            
            for selector in pagination_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} pagination elements with selector: {selector}")
                except Exception as e:
                    logger.debug(f"Error checking pagination selector {selector}: {e}")
                    
            logger.info("=== END DEBUG ===")
            
        except Exception as e:
            logger.error(f"Error in debug_page_structure: {e}")
    
    def scroll_page(self):
        """Scroll through the page to trigger lazy loading and load all content"""
        try:
            logger.info("Starting page scroll to load all content...")
            
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"Initial page height: {last_height}px")
            
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll to bottom of page
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logger.info(f"Scrolled to bottom (attempt {scroll_attempts + 1})")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Calculate new scroll height and compare to last height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                logger.info(f"New page height: {new_height}px")
                
                if new_height == last_height:
                    # No new content loaded, break
                    logger.info("No new content loaded, scrolling complete")
                    break
                    
                last_height = new_height
                scroll_attempts += 1
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Additional scrolling pattern - scroll in steps to ensure everything loads
            logger.info("Performing step-by-step scroll...")
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_steps = 5
            step_size = page_height // scroll_steps
            
            for i in range(scroll_steps):
                scroll_position = step_size * (i + 1)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1)
                logger.debug(f"Scrolled to position: {scroll_position}px")
            
            # Scroll back to top for extraction
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info("Page scrolling completed")
            
        except Exception as e:
            logger.error(f"Error during page scrolling: {e}")
            # Continue anyway, scrolling is not critical
    
    def wait_for_loading_to_complete(self):
        """Wait for any loading spinners or overlays to disappear"""
        try:
            # Common loading indicator selectors
            loading_selectors = [
                ".loading",
                ".spinner",
                ".loader",
                "[class*='loading']",
                "[class*='spinner']",
                "[class*='loader']",
                ".overlay",
                ".modal-backdrop"
            ]
            
            for selector in loading_selectors:
                try:
                    # Wait for loading elements to disappear
                    loading_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if loading_elements:
                        logger.info(f"Waiting for loading elements to disappear: {selector}")
                        # Wait up to 30 seconds for loading to complete
                        WebDriverWait(self.driver, 30).until_not(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info("Loading completed")
                except TimeoutException:
                    logger.warning(f"Timeout waiting for loading element to disappear: {selector}")
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error waiting for loading to complete: {e}")
    
    def extract_property_details(self, property_element) -> Dict:
        """
        Extract detailed information from a single property listing
        
        Args:
            property_element: Selenium WebElement for the property
            
        Returns:
            Dictionary containing property details
        """
        property_data = {}
        
        try:
            # Extract property link and ID
            property_url = None
            try:
                link_element = property_element.find_element(By.TAG_NAME, "a")
                property_url = link_element.get_attribute("href")
                property_data["url"] = property_url
            except NoSuchElementException:
                # If the element itself is a link
                if property_element.tag_name == "a":
                    property_url = property_element.get_attribute("href")
                    property_data["url"] = property_url
                else:
                    property_data["url"] = None
            
            # Extract property ID from URL
            if property_url and "propertyId=" in property_url:
                property_id = property_url.split("propertyId=")[1]
                property_data["property_id"] = property_id
            else:
                property_data["property_id"] = None
            
            # Extract property image
            image_selectors = [
                "img.image-cover",
                "img",
                ".property-image img",
                ".listing-image img"
            ]
            
            image_found = False
            for selector in image_selectors:
                try:
                    img_element = property_element.find_element(By.CSS_SELECTOR, selector)
                    property_data["image_url"] = img_element.get_attribute("src")
                    property_data["image_alt"] = img_element.get_attribute("alt")
                    image_found = True
                    break
                except NoSuchElementException:
                    continue
            
            if not image_found:
                property_data["image_url"] = None
                property_data["image_alt"] = None
            
            # Extract listing type (FOR LEASE / FOR SALE) and set boolean flags
            listing_type = "Unknown"
            try:
                banner_element = property_element.find_element(By.CSS_SELECTOR, ".list-item-banner")
                listing_type = banner_element.text.strip().upper()
                property_data["listing_type"] = listing_type
            except NoSuchElementException:
                property_data["listing_type"] = "Unknown"
            
            # Set boolean flags based on listing type
            property_data["for_lease"] = "LEASE" in listing_type
            property_data["for_sale"] = "SALE" in listing_type
            
            # Check if it's both (some properties might have both options)
            if "BOTH" in listing_type or ("LEASE" in listing_type and "SALE" in listing_type):
                property_data["for_lease"] = True
                property_data["for_sale"] = True
            
            # Extract property title/address
            title_selectors = [
                "h5.mb-0",
                "h5", 
                "h4",
                "h3",
                ".title",
                ".property-title",
                ".listing-title",
                "[class*='title']"
            ]
            
            title_found = False
            for selector in title_selectors:
                try:
                    title_element = property_element.find_element(By.CSS_SELECTOR, selector)
                    property_data["title"] = title_element.text.strip()
                    title_found = True
                    break
                except NoSuchElementException:
                    continue
            
            if not title_found:
                property_data["title"] = "Unknown"
            
            # Extract location
            try:
                location_elements = property_element.find_elements(By.CSS_SELECTOR, ".secondary-information")
                if location_elements:
                    # First secondary-information element usually contains location
                    location_text = location_elements[0].text.strip()
                    if location_text and not location_text.startswith(("$", "Call", "Available")):
                        property_data["location"] = location_text
                    else:
                        property_data["location"] = "Unknown"
                else:
                    property_data["location"] = "Unknown"
            except NoSuchElementException:
                property_data["location"] = "Unknown"
            
            # Extract detailed information from table (in hover overlay)
            property_details = {}
            try:
                table_element = property_element.find_element(By.CSS_SELECTOR, "table.mt-2")
                rows = table_element.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip().lower().replace(" ", "_")
                            value = cells[1].text.strip()
                            property_details[key] = value
                    except Exception as e:
                        logger.debug(f"Error extracting table row: {e}")
                        continue
                        
            except NoSuchElementException:
                logger.debug("No detailed table found for property")
            
            # Also extract from secondary information divs (visible text)
            try:
                secondary_info_elements = property_element.find_elements(By.CSS_SELECTOR, ".secondary-information")
                secondary_info_text = []
                
                for element in secondary_info_elements:
                    text = element.text.strip()
                    if text and text not in ["-", ""]:
                        secondary_info_text.append(text)
                
                property_data["secondary_info"] = secondary_info_text
                
                # Parse specific information from secondary info
                for info in secondary_info_text:
                    info_lower = info.lower()
                    if "sf" in info_lower and "available" not in property_details:
                        property_details["available_space"] = info
                    elif "call agent" in info_lower and "price" not in property_details:
                        property_details["price"] = info
                    elif "spaces" in info_lower and "#_of_spaces" not in property_details:
                        property_details["number_of_spaces"] = info
                    elif "bldg" in info_lower and "building_size" not in property_details:
                        property_details["building_size"] = info
                    elif info_lower in ["manufacturing", "office", "warehouse", "retail", "industrial"]:
                        property_details["property_type"] = info
                        
            except Exception as e:
                logger.debug(f"Error extracting secondary information: {e}")
            
            property_data["details"] = property_details
            
        except Exception as e:
            logger.error(f"Error extracting property details: {e}")
            property_data["error"] = str(e)
        
        return property_data
    
    def get_current_page_properties(self) -> List[Dict]:
        """Extract all properties from the current page"""
        properties = []
        
        try:
            # Wait for properties to load
            self.wait_for_page_load()
            
            # Debug page structure
            self.debug_page_structure()
            
            # Try multiple selectors to find property elements
            property_selectors = [
                ".grid-item",
                ".property-item",
                ".listing-item", 
                ".property-card",
                "div[class*='property']",
                "div[class*='listing']",
                "a[href*='property']",
                ".col-md-6",  # Bootstrap columns that might contain properties
                ".property",
                ".listing"
            ]
            
            property_elements = []
            used_selector = None
            
            for selector in property_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        property_elements = elements
                        used_selector = selector
                        logger.info(f"Using selector '{selector}' - found {len(elements)} elements")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not property_elements:
                logger.warning("No property elements found with any selector")
                return properties
            
            logger.info(f"Found {len(property_elements)} properties on current page using selector: {used_selector}")
            
            for i, property_element in enumerate(property_elements, 1):
                logger.info(f"Extracting property {i}/{len(property_elements)}")
                
                # Scroll to the property element to ensure it's visible and loaded
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", property_element)
                    time.sleep(0.5)  # Brief pause after scrolling to element
                except Exception as e:
                    logger.debug(f"Could not scroll to property element: {e}")
                
                property_data = self.extract_property_details(property_element)
                property_data["page_number"] = self.get_current_page_number()
                property_data["scraped_at"] = datetime.now().isoformat()
                properties.append(property_data)
                
        except Exception as e:
            logger.error(f"Error getting properties from current page: {e}")
        
        return properties
    
    def get_current_page_number(self) -> int:
        """Get the current page number"""
        try:
            active_page_element = self.driver.find_element(By.CSS_SELECTOR, ".js-paginate-btn.active")
            return int(active_page_element.text.strip())
        except (NoSuchElementException, ValueError):
            return 1
    
    def get_total_results_info(self) -> Dict:
        """Extract pagination and results information"""
        info = {
            "total_listings": 0,
            "current_range": "",
            "total_pages": 1
        }
        
        try:
            # Try multiple selectors for pagination info
            pagination_selectors = [
                ".js-pagination-container",
                ".pagination-info",
                ".results-info",
                "[class*='pagination']",
                "[class*='results']"
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    current_range = pagination_container.text.strip()
                    info["current_range"] = current_range
                    logger.info(f"Found pagination info with selector {selector}: {current_range}")
                    break
                except NoSuchElementException:
                    continue
            
            # Try multiple selectors for total results
            total_selectors = [
                ".js-total-container",
                ".total-results",
                ".results-total",
                "[class*='total']"
            ]
            
            for selector in total_selectors:
                try:
                    total_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    total_text = total_container.text.strip()
                    
                    # Extract total number from text like "out of X listings"
                    if "out of" in total_text:
                        total_str = total_text.split("out of")[1].replace("listings", "").strip()
                        try:
                            info["total_listings"] = int(total_str)
                        except ValueError:
                            pass
                    break
                except NoSuchElementException:
                    continue
            
            # Try multiple selectors for pagination buttons
            button_selectors = [
                ".js-paginate-btn",
                ".page-link",
                ".pagination a",
                ".pager a",
                "[class*='page']"
            ]
            
            for selector in button_selectors:
                try:
                    pagination_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if pagination_buttons:
                        page_numbers = []
                        for button in pagination_buttons:
                            try:
                                page_num = int(button.text.strip())
                                page_numbers.append(page_num)
                            except ValueError:
                                continue
                        if page_numbers:
                            info["total_pages"] = max(page_numbers)
                            logger.info(f"Found {len(pagination_buttons)} pagination buttons, max page: {max(page_numbers)}")
                            break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not extract pagination info: {e}")
        
        return info
    
    def navigate_to_next_page(self) -> bool:
        """
        Navigate to the next page if available
        
        Returns:
            True if successfully navigated to next page, False otherwise
        """
        try:
            current_page = self.get_current_page_number()
            
            # Look for pagination buttons
            pagination_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".js-paginate-btn")
            
            # Find the next page button
            next_page_button = None
            for button in pagination_buttons:
                try:
                    page_num = int(button.text.strip())
                    if page_num == current_page + 1:
                        next_page_button = button
                        break
                except ValueError:
                    continue
            
            if next_page_button:
                logger.info(f"Navigating from page {current_page} to page {current_page + 1}")
                self.driver.execute_script("arguments[0].click();", next_page_button)
                
                # Wait for page to load
                time.sleep(3)
                self.wait_for_page_load()
                
                # Verify we're on the new page
                new_page = self.get_current_page_number()
                if new_page > current_page:
                    logger.info(f"Successfully navigated to page {new_page}")
                    return True
                else:
                    logger.warning("Page number didn't change after clicking next")
                    return False
            else:
                logger.info("No next page button found - reached end")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def scrape_all_pages(self, url: str, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Scrape all properties from all pages
        
        Args:
            url: Starting URL to scrape
            max_pages: Maximum number of pages to scrape (None for all)
            
        Returns:
            List of all scraped properties
        """
        all_properties = []
        
        try:
            self.setup_driver()
            
            logger.info(f"Starting scrape from: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Initial wait for the browser and page to fully initialize
            logger.info("Allowing browser and page to fully initialize...")
            time.sleep(5)
            
            # Wait for page content to load
            self.wait_for_page_load()
            
            # Get initial pagination info
            pagination_info = self.get_total_results_info()
            logger.info(f"Found {pagination_info['total_listings']} total listings across {pagination_info['total_pages']} pages")
            
            page_count = 0
            max_pages_to_scrape = max_pages or pagination_info['total_pages']
            
            while page_count < max_pages_to_scrape:
                page_count += 1
                current_page = self.get_current_page_number()
                
                logger.info(f"Scraping page {current_page} (iteration {page_count})")
                
                # Get properties from current page
                page_properties = self.get_current_page_properties()
                all_properties.extend(page_properties)
                
                logger.info(f"Extracted {len(page_properties)} properties from page {current_page}")
                logger.info(f"Total properties scraped so far: {len(all_properties)}")
                
                # Try to navigate to next page
                if not self.navigate_to_next_page():
                    logger.info("No more pages available or navigation failed")
                    break
                
                # Small delay between pages to be respectful
                time.sleep(2)
            
            logger.info(f"Scraping completed. Total properties extracted: {len(all_properties)}")
            self.scraped_properties = all_properties
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
        finally:
            self.close_driver()
        
        return all_properties
    
    def save_to_json(self, filename: str = "kings_items.json"):
        """Save scraped properties to JSON file"""
        if not self.scraped_properties:
            logger.warning("No properties to save")
            return
        
        # Create metadata
        metadata = {
            "scraped_at": datetime.now().isoformat(),
            "total_properties": len(self.scraped_properties),
            "scraper_version": "1.0"
        }
        
        # Combine metadata and properties
        output_data = {
            "metadata": metadata,
            "properties": self.scraped_properties
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.scraped_properties)} properties to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            raise


def main():
    """Main function to run the scraper"""
    
    # Configuration
    URL = "https://www.kingindustrial.com/home-5/properties/"  # Local file path
    # For web URL, use: URL = "https://www.kingindustrial.com/properties"
    
    HEADLESS = False  # Set to False to see browser
    MAX_PAGES = None  # Set to number to limit pages, None for all pages
    OUTPUT_FILE = "kings_data.json"
    
    # Initialize scraper
    scraper = KingsPropertiesScraper(headless=HEADLESS)
    
    try:
        # Scrape all properties
        properties = scraper.scrape_all_pages(URL, max_pages=MAX_PAGES)
        
        # Save results
        scraper.save_to_json(OUTPUT_FILE)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"SCRAPING COMPLETED SUCCESSFULLY")
        print(f"{'='*50}")
        print(f"Total properties scraped: {len(properties)}")
        print(f"Output file: {OUTPUT_FILE}")
        
        # Print sample of first property
        if properties:
            print(f"\nSample property data:")
            print(f"Title: {properties[0].get('title', 'N/A')}")
            print(f"Location: {properties[0].get('location', 'N/A')}")
            print(f"Type: {properties[0].get('listing_type', 'N/A')}")
            print(f"URL: {properties[0].get('url', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"Scraping failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
