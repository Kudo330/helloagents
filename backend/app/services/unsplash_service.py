"""Unsplash image service with fail-fast behavior."""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class UnsplashService:
    """Wrapper around the Unsplash search API."""

    def __init__(self, access_key: str):
        self.access_key = (access_key or "").strip()
        self.base_url = "https://api.unsplash.com"
        self.timeout = 3
        self.disabled = not bool(self.access_key)
        if self.disabled:
            logger.info("UnsplashService disabled because unsplash_access_key is missing")

    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        if self.disabled:
            return []
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key,
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            photos = []
            for result in results:
                photos.append(
                    {
                        "url": result.get("urls", {}).get("regular", ""),
                        "description": result.get("description", ""),
                        "photographer": result.get("user", {}).get("name", ""),
                    }
                )
            return photos
        except Exception as exc:
            logger.warning("Unsplash search exception, disabling service: %s", exc)
            self.disabled = True
            return []

    def get_photo_url(self, query: str) -> Optional[str]:
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None
