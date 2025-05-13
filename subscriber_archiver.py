import asyncio, aio_pika, os, re, logging
from playwright.async_api import async_playwright
from datetime import datetime

ARCHIVE_BASE_PATH = "./archives"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def sanitize_folder_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

async def save_with_playwright(url, folder_name):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await (await browser.new_context()).new_page()
            await page.goto(url, wait_until="networkidle")
            full_path = os.path.join(ARCHIVE_BASE_PATH, folder_name)
            os.makedirs(full_path, exist_ok=True)
            html = await page.content()
            with open(os.path.join(full_path, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            await page.screenshot(path=os.path.join(full_path, "screenshot.png"), full_page=True)
            await browser.close()
    except Exception as e:
        logging.error(f"Error saving {url}: {e}")

async def process_message(message):
    url = message.body.decode()
    logging.info(f"URL received: {url}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = sanitize_folder_name(f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}__{timestamp}")
    await save_with_playwright(url, folder_name)
    logging.info(f"Archived {url} at {folder_name}")

async def main():
    connection = None
    try:
        connection = await aio_pika.connect_robust(host="localhost", port=5672, login="guest", password="guest", timeout=10)
        logging.info("Connected to RabbitMQ")
        channel = await connection.channel()
        queue = await channel.declare_queue("url_queue", durable=True)
        await channel.set_qos(prefetch_count=1)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await process_message(message)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if connection and not connection.is_closed:
            await connection.close()
            logging.info("Connection closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")