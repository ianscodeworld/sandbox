import os
import requests
from playwright.async_api import async_playwright
import bleach
from datetime import datetime
from typing import List
import re

class WebTestGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.test_steps: List[str] = []
        self.target_url = ""

    async def setup_target_page(self, url: str):
        """get html code from target page"""
        self.target_url = url
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            return await page.content()

    def sanitize_html(self, html: str) -> str:
        """sanitize HTML context"""
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS | {
            'button', 'form', 'img', 'input', 'select', 'textarea'
        }
        return bleach.clean(
            html,
            tags=allowed_tags,
            attributes=bleach.ALLOWED_ATTRIBUTES,
            protocols=['http', 'https', 'data']
        )

    async def call_deepseek_api(self, prompt: str) -> str:
        """Call DeepSeek API"""
        headers = {
            "Authorization": "Bearer sk-inevtcmwcxadaomrgzchgzemxcyqoczcoolypbiyzdiujblz",
            "Content-Type": "application/json"
        }
        url = "https://api.siliconflow.cn/v1/chat/completions"
        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-R1",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.3
        }
        try:
            response = requests.request("POST", url, json=payload, headers=headers)
            response.raise_for_status()
            print("==================prompt===========================")
            print(prompt)
            print("=================response=========================")
            print(response.json())
            print("===============response.json()=====================")
            print(response.json()['choices'][0]['message']['content'])
            print("=================end===============================")
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise RuntimeError(f"API Call Failed: {str(e)}")

    async def generate_test_code(self, scenario: str) -> str:
        """Main Workflow"""
        # 1. get target page html code 
        raw_html = await self.setup_target_page(self.target_url)
        
        # 2. sanitize HTML context
        sanitized_html = self.sanitize_html(raw_html)
        
        # 3. creating prompt with html content
        prompt = f"""
        [AVAILABLE TOOLS]
        - async click(selector) -> None
        - async fill(selector, text) -> None
        - async select(selector, option) -> None
        - async check(selector) -> None
        - async screenshot(path) -> None
        - async wait_for_selector(selector) -> None

        [CURRENT PAGE CONTENT]
        {sanitized_html[:8192]}  <!-- Max_Token limitation -->

        [TASK]
        Playwright NL-requirements：
        {scenario}

        [REQUIREMENT]
        - use Python async/await syntax
        - implement proper asynchronous waiting mechanisms
        - add code comments if necessary
        - handle potential exceptions with try/except blocks
        - only give python code without markdown format
        - always print the result of Test 
        """
        
        # 4. use deepseek to create response
        generated_code = await self.call_deepseek_api(prompt)
        
        # 5. modify the response to acutal playwright scripts
        return self._post_process_code(generated_code)

    def _post_process_code(self, code: str) -> str:
        """modify the response to acutal playwright scripts """
        pattern = r'^\s*```python\s*|\s*```\s*$'
        code = re.sub(pattern, '', code, flags=re.MULTILINE)

        return code

##Smaple run
async def main():
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    generator = WebTestGenerator(api_key=API_KEY)
    
    await generator.setup_target_page("https://www.baidu.com")

    test_scenario = """
    Requirements for testing Baidu search:

    1.Access the Baidu homepage
    2.Input "AI-generated code" in the search box (typically displaying "Baidu Search" as placeholder text)
    3.Click the "Baidu Search" button
    4.Verify the result page URL contains the search parameter (typically including wd=AI-generated code)
    """
    
    generated_code = await generator.generate_test_code(
        test_scenario
    )

    if isinstance(generated_code, list):
        generated_code = "\n".join(generated_code)

    with open("Baidu_UI_Testing_Script.py", "w", encoding="utf-8-sig", errors='xmlcharrefreplace') as f:
        f.write(generated_code)
        
    print("code has been generated to baidu_search_test.py")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
