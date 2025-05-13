import asyncio, aio_pika, logging, argparse
from datetime import datetime
from playwright.async_api import async_playwright
from content_utils import clean_html, hash_content, calculate_similarity

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_URL = "https://example.com"
CHECK_INTERVAL = 10
HASH_CACHE = {}
CONTENT_CACHE = {}
SIMILARITY_THRESHOLD = 0.98

async def get_page_content(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await (await browser.new_context()).new_page()
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        logging.error(f"Error getting content for {url}: {e}")
        return None

async def send_url_to_archive(url, connection):
    try:
        channel = await connection.channel()
        await channel.declare_queue("url_queue", durable=True)
        message = aio_pika.Message(body=url.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await channel.default_exchange.publish(message=message, routing_key="url_queue")
        logging.info(f"Sent URL to archive: {url}")
    except Exception as e:
        logging.error(f"Error sending URL to archive {url}: {e}")

async def check_url(url, connection):
    try:
        content = await get_page_content(url)
        if not content:
            return
        cleaned = clean_html(content)
        current_hash = hash_content(cleaned)
        prev_hash = HASH_CACHE.get(url)
        prev_content = CONTENT_CACHE.get(url)
        if not prev_hash:
            HASH_CACHE[url] = current_hash
            CONTENT_CACHE[url] = cleaned
            logging.info(f"Initial hash for {url}: {current_hash[:8]}...")
            return
        if current_hash != prev_hash:
            similarity = calculate_similarity(cleaned, prev_content)
            logging.info(f"Content similarity: {similarity:.4f}")
            if similarity < SIMILARITY_THRESHOLD:
                logging.info(f"Significant change detected for {url}")
                HASH_CACHE[url] = current_hash
                CONTENT_CACHE[url] = cleaned
                await send_url_to_archive(url, connection)
            else:
                HASH_CACHE[url] = current_hash
                CONTENT_CACHE[url] = cleaned
        else:
            logging.info(f"No changes detected for {url}")
    except Exception as e:
        logging.error(f"Error checking URL {url}: {e}")

async def main(url):
    connection = None
    try:
        connection = await aio_pika.connect_robust(host="localhost", port=5672, login="guest", password="guest", timeout=10)
        logging.info("Connected to RabbitMQ")
        content = await get_page_content(url)
        if content:
            cleaned = clean_html(content)
            HASH_CACHE[url] = hash_content(cleaned)
            CONTENT_CACHE[url] = cleaned
            #initially send the URL to archive
            await send_url_to_archive(url, connection)
        while True:
            await check_url(url, connection)
            await asyncio.sleep(CHECK_INTERVAL)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if connection and not connection.is_closed:
            await connection.close()
            logging.info("Connection closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL Change Monitor")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="URL to monitor for changes")
    args = parser.parse_args()
    logging.info(f"Starting to monitor URL: {args.url}")
    try:
        asyncio.run(main(args.url))
    except KeyboardInterrupt:
        logging.info("URL monitor interrupted by user")