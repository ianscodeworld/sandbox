

from playwright.async_api import async_playwright
import asyncio

async def test_baidu_search():
    try:
        async with async_playwright() as p:
            # Launch browser and create page
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 1. Access Baidu homepage
            await page.goto('https://www.baidu.com')
            await page.wait_for_selector('input#kw', state='attached')
            
            # 2. Fill search keyword
            search_input = 'input#kw'
            await page.fill(search_input, 'AI-generated code')
            
            # 3. Click search button
            search_btn = 'input#su'
            await page.click(search_btn)
            
            # 4. Verify result page
            await page.wait_for_selector('#content_left', timeout=5000)
            current_url = page.url
            
            if 'wd=AI-generated%20code' in current_url:
                print("Test Result: Success - URL contains search parameter")
            else:
                print(f"Test Result: Failed - Unexpected URL: {current_url}")
            
            await browser.close()
            
    except Exception as e:
        print(f"Test Result: Failed - {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_baidu_search())