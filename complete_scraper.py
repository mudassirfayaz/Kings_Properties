#!/usr/bin/env python3
"""
Complete Kings Properties scraper - collects all items from all pages
Saves data in exact format of kings_items.json to kings_data.json
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

def extract_property_data(property_element):
    """Extract data from a single property element"""
    try:
        # Extract actual property URL from the browser
        item_url = "https://example.com/item/unknown"  # fallback
        try:
            # Try to find the property link
            link_element = property_element.find_element(By.TAG_NAME, "a")
            actual_url = link_element.get_attribute("href")
            if actual_url and actual_url.startswith("http"):
                item_url = actual_url
                print(f"     🔗 Found property URL: {actual_url}")
            else:
                # If the element itself is a link
                if property_element.tag_name == "a":
                    actual_url = property_element.get_attribute("href")
                    if actual_url and actual_url.startswith("http"):
                        item_url = actual_url
                        print(f"     🔗 Found property URL: {actual_url}")
        except Exception as e:
            print(f"     ⚠️ Could not extract property URL: {e}")
            # Try alternative selectors for links
            try:
                link_selectors = [
                    "a[href*='property']",
                    "a[href*='listing']", 
                    "a[href*='detail']",
                    "a"
                ]
                for selector in link_selectors:
                    try:
                        link = property_element.find_element(By.CSS_SELECTOR, selector)
                        actual_url = link.get_attribute("href")
                        if actual_url and actual_url.startswith("http"):
                            item_url = actual_url
                            print(f"     🔗 Found property URL with selector '{selector}': {actual_url}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Extract property title/name
        property_name = "Unknown Property"
        try:
            # Try different selectors for title
            title_selectors = ["h5", "h4", "h3", ".title", "[class*='title']"]
            for selector in title_selectors:
                try:
                    title_elem = property_element.find_element(By.CSS_SELECTOR, selector)
                    property_name = title_elem.text.strip()
                    if property_name:
                        break
                except:
                    continue
        except:
            pass
        
        # Extract listing type and set for_lease/for_sale
        for_lease = False
        for_sale = False
        try:
            # Look for listing type banner
            banner_selectors = [".list-item-banner", "[class*='banner']", "[class*='type']"]
            for selector in banner_selectors:
                try:
                    banner = property_element.find_element(By.CSS_SELECTOR, selector)
                    banner_text = banner.text.strip().upper()
                    if "LEASE" in banner_text:
                        for_lease = True
                    if "SALE" in banner_text:
                        for_sale = True
                    break
                except:
                    continue
        except:
            # Default if we can't determine
            for_lease = True
        
        # Extract PDF URL if available
        pdf_url = ""  # Default empty as shown in your example
        try:
            # Look for PDF or brochure links
            pdf_selectors = [
                "a[href*='.pdf']",
                "a[href*='brochure']",
                "a[href*='flyer']",
                "a[title*='PDF']",
                "a[title*='Brochure']"
            ]
            for selector in pdf_selectors:
                try:
                    pdf_link = property_element.find_element(By.CSS_SELECTOR, selector)
                    pdf_href = pdf_link.get_attribute("href")
                    if pdf_href and (".pdf" in pdf_href.lower() or "brochure" in pdf_href.lower()):
                        pdf_url = pdf_href
                        print(f"     📄 Found PDF URL: {pdf_url}")
                        break
                except:
                    continue
        except:
            pass
        
        # Generate current date and time
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        # Create property data in exact format
        property_data = {
            "name": property_name,
            "email": "contact@kingindustrial.com",  # Default email
            "item_url": item_url,  # This is now the actual property URL from browser
            "pdf_url": pdf_url,  # This will be actual PDF URL if found, empty string otherwise
            "for_lease": for_lease,
            "for_sale": for_sale,
            "date": current_date,
            "time": current_time,
            "property": property_name
        }
        
        return property_data
        
    except Exception as e:
        print(f"   ❌ Error extracting property data: {e}")
        return None

def find_pagination_buttons(driver):
    """Find pagination buttons"""
    try:
        # Try different pagination selectors
        pagination_selectors = [
            ".js-paginate-btn",
            ".page-link",
            ".pagination a",
            ".pager a", 
            "[class*='page']",
            "button[class*='page']"
        ]
        
        for selector in pagination_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    return buttons
            except:
                continue
        return []
    except:
        return []

def get_next_page_button(driver, current_page):
    """Find the next page button"""
    try:
        buttons = find_pagination_buttons(driver)
        
        for button in buttons:
            try:
                button_text = button.text.strip()
                if button_text.isdigit():
                    page_num = int(button_text)
                    if page_num == current_page + 1:
                        return button
            except:
                continue
        return None
    except:
        return None

def main():
    """Main scraper function"""
    
    # Configuration
    URL = "https://www.kingindustrial.com/home-5/properties/"
    OUTPUT_FILE = "kings_data.json"
    
    # Set up Chrome options (visible browser)
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    driver = None
    all_properties = []
    
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ WebDriver initialized successfully")
        
        # Step 1: Visit the URL
        print(f"🌐 Visiting URL: {URL}")
        driver.get(URL)
        print("✅ URL loaded")
        
        # Step 2: Wait for page to load
        print("⏳ Waiting for 10 seconds...")
        time.sleep(10)
        print("✅ Wait completed")
        
        # Step 3: Scroll the page
        print("📜 Scrolling page...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        print("✅ Page scrolled")
        
        # Step 4: Find and switch to iframe
        print("🔍 Looking for iframe...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        buildout_iframe = None
        
        for iframe in iframes:
            src = iframe.get_attribute("src")
            if src and "buildout.com" in src and "inventory" in src:
                buildout_iframe = iframe
                break
        
        if not buildout_iframe:
            print("❌ Could not find buildout iframe")
            return 1
            
        print("🔄 Switching to iframe...")
        driver.switch_to.frame(buildout_iframe)
        time.sleep(3)
        print("✅ Successfully switched to iframe")
        
        # Step 5: Start scraping all pages
        current_page = 1
        max_pages = 10  # Safety limit
        
        while current_page <= max_pages:
            print(f"\n📄 SCRAPING PAGE {current_page}")
            print("=" * 40)
            
            # Wait for page content to load
            time.sleep(5)
            
            # Find property items on current page
            property_selectors = [
                ".grid-item",
                ".col-md-6",
                ".property-item", 
                ".listing-item",
                "div[class*='property']",
                "div[class*='listing']"
            ]
            
            page_properties = []
            found_items = False
            
            for selector in property_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        print(f"✅ Found {len(items)} items using selector: '{selector}'")
                        
                        for i, item in enumerate(items, 1):
                            print(f"   Extracting property {i}/{len(items)}...")
                            property_data = extract_property_data(item)
                            if property_data:
                                page_properties.append(property_data)
                                print(f"   ✅ Extracted: {property_data['name']}")
                        
                        found_items = True
                        break
                except:
                    continue
            
            if not found_items:
                print("❌ No property items found on this page")
                break
            
            # Add page properties to total
            all_properties.extend(page_properties)
            print(f"✅ Page {current_page} complete: {len(page_properties)} properties")
            print(f"📊 Total properties so far: {len(all_properties)}")
            
            # Try to find next page button
            next_button = get_next_page_button(driver, current_page)
            
            if next_button:
                print(f"🔄 Moving to page {current_page + 1}...")
                try:
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(5)  # Wait for page to load
                    current_page += 1
                except Exception as e:
                    print(f"❌ Error clicking next page: {e}")
                    break
            else:
                print("🏁 No more pages found - scraping complete!")
                break
        
        # Switch back to main content
        driver.switch_to.default_content()
        
        # Step 6: Save data to JSON file
        if all_properties:
            print(f"\n💾 Saving {len(all_properties)} properties to {OUTPUT_FILE}...")
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_properties, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Data saved successfully to {OUTPUT_FILE}")
            
            # Show sample of saved data
            print(f"\n📋 SAMPLE PROPERTY:")
            sample = all_properties[0]
            for key, value in sample.items():
                print(f"   {key}: {value}")
                
        else:
            print("❌ No properties found to save")
        
        print(f"\n🎯 SCRAPING COMPLETED!")
        print(f"📊 Total properties collected: {len(all_properties)}")
        print(f"📁 Saved to: {OUTPUT_FILE}")
        
        # Keep browser open to see results
        print("⏸️ Keeping browser open for 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Browser closed")
    
    return 0

if __name__ == "__main__":
    exit(main())
