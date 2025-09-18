#!/usr/bin/env python3
"""
Comprehensive Kings Properties scraper - captures ALL property data
Gets the actual clickable URLs and all property information
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

def extract_comprehensive_property_data(property_element, driver):
    """Extract ALL data from a single property element"""
    try:
        print(f"     🔍 Analyzing property element...")
        
        # Get the outer HTML for debugging
        outer_html = property_element.get_attribute('outerHTML')[:500]
        print(f"     📋 Element HTML preview: {outer_html[:200]}...")
        
        # Extract actual clickable property URL from the structure you provided
        # <div class="col-md-6 col-12 mb-3"><a href="https://www.kingindustrial.com/home-5/properties/?propertyId=1417234-sale" target="_top">
        item_url = "https://example.com/item/unknown"  # fallback
        
        try:
            # Based on your HTML structure, the property element is the div.col-md-6
            # and it contains an <a> tag with the property URL
            link_element = property_element.find_element(By.TAG_NAME, "a")
            href = link_element.get_attribute("href")
            
            if href and href.startswith("http"):
                item_url = href
                print(f"     🔗 Found property URL: {item_url}")
            else:
                print(f"     ⚠️ Found link but invalid href: {href}")
                
        except Exception as e:
            print(f"     ❌ Could not find property URL in expected structure: {e}")
            # Fallback: try to find any link
            try:
                all_links = property_element.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "kingindustrial.com" in href and "propertyId" in href:
                        item_url = href
                        print(f"     🔗 Found property URL via fallback: {item_url}")
                        break
            except:
                pass
        
        # Extract property name/title from your HTML structure
        # <h5 class="mb-0 text-truncate">605 Athena Drive</h5>
        property_name = "Unknown Property"
        try:
            # Based on your structure, look for h5.mb-0 first
            title_elem = property_element.find_element(By.CSS_SELECTOR, "h5.mb-0")
            property_name = title_elem.text.strip()
            print(f"     📝 Property name (h5.mb-0): {property_name}")
        except:
            # Fallback to other selectors
            try:
                title_selectors = [
                    "h5", "h4", "h3", ".title", ".property-title", 
                    "[class*='title']", ".mb-0"
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = property_element.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        if title_text and len(title_text) > 2:
                            property_name = title_text
                            print(f"     📝 Property name ({selector}): {property_name}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Extract location/address from your HTML structure
        # <div class="text-truncate secondary-information">Athens, GA  30605</div>
        location = ""
        try:
            # Based on your structure, look for .secondary-information
            location_elems = property_element.find_elements(By.CSS_SELECTOR, ".secondary-information")
            for elem in location_elems:
                text = elem.text.strip()
                # Check if this looks like an address (contains state abbreviation or zip code)
                if text and any(pattern in text for pattern in [', GA', ', AL', ', FL', ', TN', ', SC', ', NC']) and any(c.isdigit() for c in text):
                    location = text
                    print(f"     📍 Location (.secondary-information): {location}")
                    break
        except Exception as e:
            print(f"     ⚠️ Could not extract location: {e}")
        
        # Extract listing type from your HTML structure
        # <div class="list-item-banner overlay for-sale">FOR SALE</div>
        for_lease = False
        for_sale = False
        listing_type = ""
        
        try:
            # Based on your structure, look for .list-item-banner
            banner_elem = property_element.find_element(By.CSS_SELECTOR, ".list-item-banner")
            banner_text = banner_elem.text.strip().upper()
            listing_type = banner_text
            
            if "LEASE" in banner_text:
                for_lease = True
            if "SALE" in banner_text:
                for_sale = True
                
            print(f"     🏷️ Listing type (.list-item-banner): {banner_text}")
            
        except Exception as e:
            print(f"     ⚠️ Could not extract listing type: {e}")
            # Default to lease if we can't determine
            for_lease = True
        
        # If no specific type found, default to lease
        if not for_lease and not for_sale:
            for_lease = True
        
        # Extract property details (size, price, etc.)
        property_details = {}
        try:
            # Look for property details in tables or structured data
            detail_selectors = [
                "table tr", ".property-detail", ".detail-item",
                "[class*='detail']", ".secondary-information"
            ]
            
            # Try to extract from table rows
            try:
                rows = property_element.find_elements(By.CSS_SELECTOR, "table tr")
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip().lower()
                            value = cells[1].text.strip()
                            if key and value:
                                property_details[key] = value
                                print(f"     📊 Detail: {key} = {value}")
                    except:
                        continue
            except:
                pass
            
            # Also extract from any text that looks like property details
            try:
                all_text = property_element.text
                lines = all_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for patterns like "10,000 SF", "Call Agent", etc.
                    if any(keyword in line.upper() for keyword in ['SF', 'ACRE', 'CALL', '$', 'SPACE']):
                        if 'SF' in line.upper() and 'available' not in property_details:
                            property_details['available_space'] = line
                        elif 'CALL' in line.upper() and 'price' not in property_details:
                            property_details['price'] = line
                        elif '$' in line and 'rate' not in property_details:
                            property_details['rate'] = line
            except:
                pass
                
        except:
            pass
        
        # Extract PDF/brochure URL
        pdf_url = ""
        try:
            pdf_selectors = [
                "a[href*='.pdf']", "a[href*='brochure']", "a[href*='flyer']",
                "a[title*='PDF']", "a[title*='Brochure']", "a[title*='Flyer']"
            ]
            
            for selector in pdf_selectors:
                try:
                    pdf_links = property_element.find_elements(By.CSS_SELECTOR, selector)
                    for pdf_link in pdf_links:
                        href = pdf_link.get_attribute("href")
                        if href and (".pdf" in href.lower() or "brochure" in href.lower()):
                            pdf_url = href
                            print(f"     📄 PDF URL: {pdf_url}")
                            break
                    if pdf_url:
                        break
                except:
                    continue
        except:
            pass
        
        # Extract image URL
        image_url = ""
        try:
            img_selectors = ["img", ".property-image img", ".listing-image img"]
            for selector in img_selectors:
                try:
                    img_elem = property_element.find_element(By.CSS_SELECTOR, selector)
                    src = img_elem.get_attribute("src")
                    if src and src.startswith("http"):
                        image_url = src
                        print(f"     🖼️ Image URL: {image_url}")
                        break
                except:
                    continue
        except:
            pass
        
        # Generate current date and time
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        
        # Create comprehensive property data
        property_data = {
            "name": property_name,
            "email": "contact@kingindustrial.com",
            "item_url": item_url,  # This is the actual clickable property URL
            "pdf_url": pdf_url,
            "for_lease": for_lease,
            "for_sale": for_sale,
            "date": current_date,
            "time": current_time,
            "property": property_name,
            # Additional comprehensive data
            "location": location,
            "listing_type": listing_type,
            "image_url": image_url,
            "property_details": property_details
        }
        
        return property_data
        
    except Exception as e:
        print(f"     ❌ Error extracting comprehensive property data: {e}")
        return None

def main():
    """Main comprehensive scraper function"""
    
    # Configuration
    URL = "https://www.kingindustrial.com/home-5/properties/"
    OUTPUT_FILE = "kings_data.json"
    
    # Set up Chrome options (visible browser for debugging)
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
        print("⏳ Waiting for 15 seconds for full page load...")
        time.sleep(15)
        print("✅ Wait completed")
        
        # Step 3: Scroll the page to trigger any lazy loading
        print("📜 Scrolling page to trigger content loading...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        print("✅ Page scrolled")
        
        # Step 4: Find and switch to iframe
        print("🔍 Looking for buildout iframe...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        buildout_iframe = None
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src")
            title = iframe.get_attribute("title")
            print(f"   Iframe {i+1}: {title} - {src[:100]}...")
            if src and "buildout.com" in src and "inventory" in src:
                buildout_iframe = iframe
                print(f"   ✅ Found buildout iframe!")
                break
        
        if not buildout_iframe:
            print("❌ Could not find buildout iframe")
            return 1
            
        print("🔄 Switching to iframe...")
        driver.switch_to.frame(buildout_iframe)
        time.sleep(5)  # Wait for iframe content to load
        print("✅ Successfully switched to iframe")
        
        # Step 5: Start comprehensive scraping of all pages
        current_page = 1
        max_pages = 20  # Increased safety limit
        
        while current_page <= max_pages:
            print(f"\n📄 COMPREHENSIVELY SCRAPING PAGE {current_page}")
            print("=" * 50)
            
            # Wait for page content to load
            time.sleep(8)
            
            # Scroll within iframe to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Find property items with multiple strategies
            property_selectors = [
                ".col-md-6",  # Most likely based on previous results
                ".grid-item",
                ".property-item", 
                ".listing-item",
                ".property-card",
                "div[class*='property']",
                "div[class*='listing']",
                "a[href*='property']"
            ]
            
            page_properties = []
            found_items = False
            
            for selector in property_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if items and len(items) > 0:
                        print(f"✅ Found {len(items)} items using selector: '{selector}'")
                        
                        for i, item in enumerate(items, 1):
                            print(f"\n   🏠 Processing property {i}/{len(items)}...")
                            
                            # Scroll to the item to ensure it's visible
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                                time.sleep(1)
                            except:
                                pass
                            
                            property_data = extract_comprehensive_property_data(item, driver)
                            if property_data:
                                page_properties.append(property_data)
                                print(f"   ✅ Extracted: {property_data['name']}")
                                print(f"   🔗 URL: {property_data['item_url']}")
                            else:
                                print(f"   ❌ Failed to extract property {i}")
                        
                        found_items = True
                        break
                except Exception as e:
                    print(f"   ❌ Error with selector '{selector}': {e}")
                    continue
            
            if not found_items:
                print("❌ No property items found on this page")
                break
            
            # Add page properties to total
            all_properties.extend(page_properties)
            print(f"\n✅ Page {current_page} complete: {len(page_properties)} properties")
            print(f"📊 Total properties collected so far: {len(all_properties)}")
            
            # Try to find next page button
            next_button = None
            try:
                # Look for pagination buttons
                pagination_selectors = [
                    ".js-paginate-btn", ".page-link", ".pagination a", 
                    ".pager a", "button[class*='page']", "a[class*='page']"
                ]
                
                for selector in pagination_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            button_text = button.text.strip()
                            if button_text.isdigit() and int(button_text) == current_page + 1:
                                next_button = button
                                break
                        if next_button:
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"❌ Error finding pagination: {e}")
            
            if next_button:
                print(f"🔄 Moving to page {current_page + 1}...")
                try:
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(8)  # Wait for next page to load
                    current_page += 1
                except Exception as e:
                    print(f"❌ Error clicking next page: {e}")
                    break
            else:
                print("🏁 No more pages found - comprehensive scraping complete!")
                break
        
        # Switch back to main content
        driver.switch_to.default_content()
        
        # Step 6: Save comprehensive data to JSON file
        if all_properties:
            print(f"\n💾 Saving {len(all_properties)} comprehensive properties to {OUTPUT_FILE}...")
            
            # Format data to match kings_items.json structure but keep additional data
            formatted_properties = []
            for prop in all_properties:
                # Keep the required format but add extra data as well
                formatted_prop = {
                    "name": prop.get("name", "Unknown Property"),
                    "email": prop.get("email", "contact@kingindustrial.com"),
                    "item_url": prop.get("item_url", ""),
                    "pdf_url": prop.get("pdf_url", ""),
                    "for_lease": prop.get("for_lease", False),
                    "for_sale": prop.get("for_sale", False),
                    "date": prop.get("date", ""),
                    "time": prop.get("time", ""),
                    "property": prop.get("property", prop.get("name", "Unknown Property")),
                    # Additional comprehensive data
                    "location": prop.get("location", ""),
                    "listing_type": prop.get("listing_type", ""),
                    "image_url": prop.get("image_url", ""),
                    "property_details": prop.get("property_details", {})
                }
                formatted_properties.append(formatted_prop)
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(formatted_properties, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Comprehensive data saved successfully to {OUTPUT_FILE}")
            
            # Show sample of saved data
            print(f"\n📋 SAMPLE COMPREHENSIVE PROPERTY:")
            if formatted_properties:
                sample = formatted_properties[0]
                for key, value in sample.items():
                    if key != "property_details":
                        print(f"   {key}: {value}")
                if sample.get("property_details"):
                    print(f"   property_details:")
                    for k, v in sample["property_details"].items():
                        print(f"      {k}: {v}")
                
        else:
            print("❌ No properties found to save")
        
        print(f"\n🎯 COMPREHENSIVE SCRAPING COMPLETED!")
        print(f"📊 Total properties collected: {len(all_properties)}")
        print(f"📁 Saved to: {OUTPUT_FILE}")
        print(f"🔗 All property URLs should now be actual clickable URLs!")
        
        # Keep browser open to see results
        print("⏸️ Keeping browser open for 15 seconds to review...")
        time.sleep(15)
        
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
