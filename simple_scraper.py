#!/usr/bin/env python3
"""
Simple Kings Properties scraper - does exactly what's requested
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

def main():
    """Simple scraper following exact steps"""
    
    # Configuration
    URL = "https://www.kingindustrial.com/home-5/properties/"
    
    # Set up Chrome options (visible browser)
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    driver = None
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
        
        # Step 2: Wait for 10 seconds
        print("⏳ Waiting for 10 seconds...")
        time.sleep(10)
        print("✅ Wait completed")
        
        # Step 3: Scroll the page only one time
        print("📜 Scrolling page one time...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("✅ Page scrolled")
        
        # Step 4: Find the iframe first (property listings are inside iframe)
        print("🔍 Step 4a: Looking for iframe...")
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"✅ Found {len(iframes)} iframe(s)")
                
                # Look for the buildout iframe specifically
                buildout_iframe = None
                for i, iframe in enumerate(iframes, 1):
                    src = iframe.get_attribute("src")
                    title = iframe.get_attribute("title")
                    print(f"   Iframe {i}: title='{title}', src='{src[:100]}...'")
                    
                    if "buildout.com" in src and "inventory" in src:
                        buildout_iframe = iframe
                        print(f"   ✅ Found buildout property iframe!")
                        break
                
                if buildout_iframe:
                    print("🔄 Step 4b: Switching to iframe...")
                    driver.switch_to.frame(buildout_iframe)
                    print("✅ Successfully switched to iframe")
                    
                    # Now look for container-fluid inside the iframe
                    print("🔍 Step 4c: Looking for 'container-fluid' inside iframe...")
                    containers = driver.find_elements(By.CLASS_NAME, "container-fluid")
                    if containers:
                        print(f"✅ YES I FOUND IT! Found {len(containers)} 'container-fluid' elements")
                        
                        # Show some details about what we found
                        for i, container in enumerate(containers, 1):
                            try:
                                # Get some basic info about the container
                                tag_name = container.tag_name
                                class_attr = container.get_attribute("class")
                                print(f"   Container {i}: <{tag_name}> with classes: {class_attr}")
                            except:
                                print(f"   Container {i}: Found but couldn't get details")
                                
                        # Step 5: Now look for the property items we will be scraping
                        print("\n🏠 Step 5: Looking for property items to scrape...")
                        try:
                            # Try different selectors for property items
                            property_selectors = [
                                ".grid-item",
                                ".property-item", 
                                ".listing-item",
                                ".col-md-6",  # Bootstrap columns
                                ".property-card",
                                "div[class*='property']",
                                "div[class*='listing']",
                                "a[href*='property']"
                            ]
                            
                            found_items = False
                            for selector in property_selectors:
                                try:
                                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                                    if items:
                                        print(f"✅ FOUND PROPERTY ITEMS! Found {len(items)} items using selector: '{selector}'")
                                        
                                        # Show details of first few items
                                        for i, item in enumerate(items[:3], 1):  # Show first 3 items
                                            try:
                                                tag_name = item.tag_name
                                                class_attr = item.get_attribute("class")
                                                text_preview = item.text[:100] if item.text else "No text"
                                                print(f"   Item {i}: <{tag_name}> classes='{class_attr}'")
                                                print(f"           Text preview: '{text_preview}...'")
                                            except:
                                                print(f"   Item {i}: Found but couldn't get details")
                                        
                                        if len(items) > 3:
                                            print(f"   ... and {len(items) - 3} more items")
                                        
                                        found_items = True
                                        break
                                except:
                                    continue
                            
                            if not found_items:
                                print("❌ NO property items found with any selector")
                                
                                # Debug: show what elements are actually available
                                print("\n🔍 DEBUG: Let me show you what's available in the iframe...")
                                all_divs = driver.find_elements(By.TAG_NAME, "div")
                                print(f"   Total div elements: {len(all_divs)}")
                                
                                # Show first few divs with classes
                                for i, div in enumerate(all_divs[:10], 1):
                                    try:
                                        class_attr = div.get_attribute("class")
                                        if class_attr:
                                            print(f"   Div {i}: classes='{class_attr}'")
                                    except:
                                        continue
                                        
                        except Exception as e:
                            print(f"❌ Error looking for property items: {e}")
                    else:
                        print("❌ NO, I did not find any 'container-fluid' elements inside iframe")
                        
                    # Switch back to main content
                    driver.switch_to.default_content()
                    print("🔄 Switched back to main content")
                else:
                    print("❌ Could not find buildout iframe")
            else:
                print("❌ NO iframes found")
                
        except Exception as e:
            print(f"❌ Error looking for iframe/container-fluid: {e}")
        
        print("\n🎯 Task completed successfully!")
        
        # Keep browser open for a moment so you can see the result
        print("⏸️ Keeping browser open for 10 seconds so you can see...")
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
