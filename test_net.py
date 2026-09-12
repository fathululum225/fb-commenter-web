import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        page = await browser.new_page()
        
        print("🌐 Test buka facebook.com...")
        try:
            await page.goto("https://www.facebook.com/", 
                           wait_until="domcontentloaded", timeout=30000)
            print(f"✅ Berhasil! URL: {page.url}")
            print(f"📄 Title: {await page.title()}")
        except Exception as e:
            print(f"❌ Gagal: {e}")
        
        print("\n🌐 Test buka google.com...")
        try:
            await page.goto("https://www.google.com/", 
                           wait_until="domcontentloaded", timeout=30000)
            print(f"✅ Berhasil! URL: {page.url}")
        except Exception as e:
            print(f"❌ Gagal: {e}")
        
        input("\nTekan Enter untuk tutup...")
        await browser.close()

asyncio.run(main())