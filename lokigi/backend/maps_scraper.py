from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from loguru import logger
import time

class MapsScraper:
    def __init__(self, urls, headless=True, timeout=20000):
        self.urls = urls
        self.headless = headless
        self.timeout = timeout

    def scrape_reviews_and_posts(self):
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            for url in self.urls:
                try:
                    logger.info(f"Navegando a {url}")
                    page.goto(url, timeout=self.timeout)
                    time.sleep(2)
                    self._scroll_reviews(page)
                    reviews = self._extract_reviews(page)
                    posts = self._extract_posts(page)
                    results.append({"url": url, "reviews": reviews, "posts": posts})
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout navegando a {url}")
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
            browser.close()
        return results

    def _scroll_reviews(self, page, max_scrolls=10):
        for _ in range(max_scrolls):
            try:
                page.mouse.wheel(0, 1000)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Error al hacer scroll: {e}")
                break

    def _extract_reviews(self, page):
        try:
            review_elements = page.query_selector_all('[aria-label*="reseña"]')
            reviews = [el.inner_text() for el in review_elements]
            return reviews
        except Exception as e:
            logger.warning(f"No se pudieron extraer reseñas: {e}")
            return []

    def _extract_posts(self, page):
        try:
            post_elements = page.query_selector_all('[aria-label*="Publicación"]')
            posts = [el.inner_text() for el in post_elements]
            return posts
        except Exception as e:
            logger.warning(f"No se pudieron extraer posts: {e}")
            return []

# Ejemplo de uso:
# urls = ["https://maps.google.com/...?cid=...", ...]
# scraper = MapsScraper(urls)
# data = scraper.scrape_reviews_and_posts()
# print(data)
