from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class MobileTester:
    
    MOBILE_DEVICES = {
        "basic_phone": {"width": 240, "height": 320},
        "feature_phone": {"width": 320, "height": 480},
        "smartphone": {"width": 375, "height": 667},
        "tablet": {"width": 768, "height": 1024}
    }
    
    def test_responsiveness(self, url="http://localhost:5000"):
        """Test on different screen sizes"""
        driver = webdriver.Chrome()
        
        results = {}
        
        for device_name, dimensions in self.MOBILE_DEVICES.items():
            print(f"\nTesting: {device_name}")
            
            # Set window size
            driver.set_window_size(dimensions['width'], dimensions['height'])
            driver.get(url)
            time.sleep(2)
            
            # Take screenshot
            screenshot_name = f"screenshots/{device_name}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_name)
            
            # Check key elements
            checks = {
                "login_visible": self.is_element_visible(driver, "#loginSection"),
                "nav_tabs_visible": self.is_element_visible(driver, ".nav-tabs"),
                "prices_displayed": self.is_element_visible(driver, ".price-value"),
                "responsive_menu": self.check_menu_collapse(driver)
            }
            
            results[device_name] = {
                "dimensions": dimensions,
                "screenshot": screenshot_name,
                "checks": checks,
                "passed": all(checks.values())
            }
            
            print(f"  - Checks: {checks}")
        
        driver.quit()
        return results
    
    def is_element_visible(self, driver, css_selector):
        try:
            element = driver.find_element(By.CSS_SELECTOR, css_selector)
            return element.is_displayed()
        except:
            return False
    
    def check_menu_collapse(self, driver):
        # Check if navigation collapses on small screens
        width = driver.get_window_size()['width']
        if width < 768:
            # Should show hamburger menu
            return self.is_element_visible(driver, ".mobile-menu")
        return True