import os
import re
import logging
import asyncio
from typing import Dict, List, Any, Tuple, Optional # Added Optional

import httpx
from cachetools import TTLCache
from cachetools.keys import hashkey

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field, HttpUrl # Removed AnyHttpUrl as HttpUrl is generally preferred
from pydantic_settings import BaseSettings, SettingsConfigDict

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential, RetryError
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
#     with db_pool.connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT 1;")
#         conn.commit()
#     db_pool.putconn(test_conn)
# except OperationalError as e:
#     logger.critical(f"Failed to connect to Postgres: {e}")
# ─────────────────────────────────────────────────────────────
# --- Imports ---       


# Attempt to import lxml, falling back to ElementTree with a warning
try:
    from lxml import etree as ET # Use lxml for performance and robustness
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET # Fallback if lxml is not available
    LXML_AVAILABLE = False
    # Logging for this will be handled after logger is configured.

# --- Configuration via Pydantic ---
class Settings(BaseSettings):
    # Service Behavior
    GEO_DEFAULT: str = "US"
    LIMIT_DEFAULT: int = 20
    APP_PORT: int = 8000 # Port the app runs on internally, matches Dockerfile EXPOSE and docker-compose target
    ROOT_PATH: str = "" # For running behind a reverse proxy with a path prefix, if needed

    # Caching
    CACHE_TTL: int = 300
    CACHE_MAXSIZE: int = 500

    # HTTP Client
    HTTP_TIMEOUT: float = 15.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20

    # Rate Limiting
    RATE_LIMIT_SETTINGS: str = "60/minute"

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:5678"] # Example, adjust for n8n or other clients

    # Logging
    LOG_LEVEL: str = "INFO"

    # Optional: Sentry for error tracking in production
    # SENTRY_DSN: Optional[HttpUrl] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()

# --- Logging Setup ---
# Using python-json-logger for structured logging if available
try:
    from pythonjsonlogger.json import JsonFormatter
    PYTHON_JSON_LOGGER_AVAILABLE = True
except ImportError:
    PYTHON_JSON_LOGGER_AVAILABLE = False
    # This initial print is for immediate feedback if the logger isn't found.
    print("python-json-logger not found. Using basic logging formatter for trending_service.")

logging.getLogger().handlers.clear() # Clear root handlers to avoid duplicates
logger = logging.getLogger("trending_service")
logger.setLevel(settings.LOG_LEVEL.upper())

log_handler = logging.StreamHandler()

if PYTHON_JSON_LOGGER_AVAILABLE:
    formatter = JsonFormatter( # type: ignore
        fmt="%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"
    )
else:
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
    )
log_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(log_handler)

if not LXML_AVAILABLE and not os.getenv("SUPPRESS_LXML_WARNING_TRENDING_SERVICE"):
    logger.warning("lxml library not found for trending_service, using xml.etree.ElementTree. "
                   "It is highly recommended to install lxml ('pip install lxml') "
                   "for improved performance, security, and XML processing capabilities in production.")

# --- FastAPI app Initialization ---
app = FastAPI(
    title="Trending Keywords Service",
    version="1.2.0", # Updated version
    description="API to fetch trending keywords and hashtags from RSS feeds. (Production Optimized)",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.ROOT_PATH # If service is behind a proxy at a subpath e.g. /trending
)

# --- Middleware ---
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_SETTINGS])
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    response = _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(status_code=response.status_code, content=response.body)

# Prometheus Metrics
try:
    Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
    logger.info("Prometheus instrumentator configured for trending_service.")
except Exception as e:
    logger.error(f"Failed to configure Prometheus instrumentator for trending_service: {e}")

# --- Caching ---
# Note: For multi-instance scalability, consider a distributed cache (Redis, Memcached).
feed_cache: TTLCache[Any, List[str]] = TTLCache(maxsize=settings.CACHE_MAXSIZE, ttl=settings.CACHE_TTL)

# --- RSS Feed Configuration ---
RSS_FEEDS: Dict[str, str] = { # Using str for HttpUrl for now, as Pydantic handles it.
    "google_trends": "https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}",
    "techcrunch": "https://techcrunch.com/feed/",
    "the_verge": "https://www.theverge.com/rss/index.xml",
    "wired": "https://www.wired.com/feed/rss",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index/",
    "cnet_news": "https://www.cnet.com/rss/news/",
    "bbc_technology": "http://feeds.bbci.co.uk/news/technology/rss.xml"
}

# --- Pydantic Models ---
class KeywordsResponse(BaseModel):
    results: Dict[str, List[str]]
    errors: Dict[str, str] = Field(default_factory=dict)

class HashtagsResponse(BaseModel):
    results: Dict[str, List[str]]
    errors: Dict[str, str] = Field(default_factory=dict)

# --- HTTP Client Management ---
http_client: Optional[httpx.AsyncClient] = None # Global client

@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = httpx.AsyncClient(
        timeout=settings.HTTP_TIMEOUT,
        http2=True,
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=settings.HTTP_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE_CONNECTIONS
        )
    )
    logger.info(f"HTTPX client initialized for trending_service. Timeout: {settings.HTTP_TIMEOUT}s")
    # if settings.SENTRY_DSN:
    #     import sentry_sdk
    #     sentry_sdk.init(dsn=str(settings.SENTRY_DSN), traces_sample_rate=1.0, environment="production") # Add environment
    #     logger.info("Sentry initialized for trending_service.")

@app.on_event("shutdown")
async def shutdown_event():
    global http_client
    if http_client:
        await http_client.aclose()
        logger.info("HTTPX client closed for trending_service.")

# --- Helper Functions ---
def slugify_to_hashtag(text: str) -> str:
    if not text or not isinstance(text, str): return ""
    text = text.replace("'", "")
    clean = re.sub(r'[^\w-]+', '_', text, flags=re.UNICODE)
    clean = clean.strip('_')
    clean = re.sub(r'_+', '_', clean)
    return f"#{clean.lower()}" if clean else ""

def parse_xml_feed(content: bytes, source_name: str, url: str, limit: int) -> List[str]:
    titles: List[str] = []
    try:
        if LXML_AVAILABLE:
            parser = ET.XMLParser(recover=True, resolve_entities=False) # type: ignore
            root = ET.fromstring(content, parser=parser) # type: ignore
        else:
            parser = ET.XMLParser()
            root = ET.fromstring(content, parser=parser)

        potential_items = []
        if LXML_AVAILABLE:
            potential_items = root.xpath("//item | //*[local-name()='entry']") # type: ignore
        else: # xml.etree.ElementTree
            atom_ns_prefix = "{http://www.w3.org/2005/Atom}"
            potential_items.extend(root.findall(".//item"))
            potential_items.extend(root.findall(f".//{atom_ns_prefix}entry"))


        for item_element in potential_items:
            if len(titles) >= limit: break
            title_element = None
            # Common title tags - lxml specific find might be better if namespaces are known
            if LXML_AVAILABLE:
                 title_element = item_element.find("title") # RSS
                 if title_element is None: title_element = item_element.find("{http://www.w3.org/2005/Atom}title") # Atom
                 if title_element is None: title_element = item_element.find("{http://purl.org/dc/elements/1.1/}title") # DC
            else: # ElementTree
                title_element = item_element.find("title")
                if title_element is None: title_element = item_element.find(f"{atom_ns_prefix}title")

            if title_element is not None and title_element.text:
                title_text = title_element.text.strip()
                if title_text: titles.append(title_text)

        if not titles:
            logger.warning({"event": "no_titles_extracted", "source": source_name, "url": url, "content_snippet_bytes": content[:250].decode('utf-8', errors='ignore')})
        return titles
    except (ET.ParseError if not LXML_AVAILABLE else ET.XMLSyntaxError) as e: # type: ignore
        logger.error({"event": "xml_parse_failed", "source": source_name, "url": url, "error": str(e), "content_snippet_bytes": content[:250].decode('utf-8', errors='ignore')})
        raise ValueError(f"XML parsing failed for {source_name}") from e
    except Exception as e:
        logger.error({"event": "unexpected_parsing_error", "source": source_name, "url": url, "error": str(e), "type": type(e).__name__})
        raise ValueError(f"Unexpected error parsing XML for {source_name}") from e

async def fetch_rss_titles(source_name: str, url_template: str, geo_code: str, limit: int) -> List[str]:
    global http_client
    if not http_client:
        logger.error({"event": "http_client_not_initialized_in_fetch", "source": source_name})
        raise RuntimeError("HTTPX client not initialized. Trending service may not have started correctly.")

    url = url_template.format(geo=geo_code) if "{geo}" in url_template else url_template
    cache_key = hashkey(source_name, url, limit)
    cached_titles = feed_cache.get(cache_key)
    if cached_titles is not None:
        logger.debug({"event": "cache_hit", "source": source_name, "url": url})
        return cached_titles

    logger.debug({"event": "cache_miss", "source": source_name, "url": url})
    try:
        async for attempt in AsyncRetrying(
            reraise=True, stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, ValueError))
        ):
            with attempt:
                log_ctx = {"source": source_name, "url": url, "attempt": attempt.retry_state.attempt_number}
                logger.info({**log_ctx, "event": "fetch_attempt"})
                try:
                    response = await http_client.get(url)
                    response.raise_for_status()
                    loop = asyncio.get_event_loop()
                    titles = await loop.run_in_executor(None, parse_xml_feed, response.content, source_name, url, limit)
                    feed_cache[cache_key] = titles
                    logger.info({**log_ctx, "event": "fetched_successfully", "count": len(titles)})
                    return titles
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [401, 403, 404]: raise # Don't retry these
                    logger.warning({**log_ctx, "event": "fetch_http_status_error", "status": e.response.status_code, "error": str(e)})
                    raise
                except (httpx.RequestError, ValueError) as e: # Network, Timeout, or Parsing errors
                    logger.warning({**log_ctx, "event": "fetch_request_or_parse_error", "error": str(e), "type": type(e).__name__})
                    raise
                except Exception as e:
                    logger.error({**log_ctx, "event": "fetch_unexpected_attempt_error", "error": str(e), "type": type(e).__name__})
                    raise
    except RetryError as e:
        err_msg = f"All attempts to fetch {source_name} failed. Last error: {e.last_attempt.exception()}"
        logger.error({"event": "fetch_failed_all_retries", "source": source_name, "url": url, "error": err_msg})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Source {source_name} unavailable.")
    except Exception as e: # Should be rare if RetryError catches all
        logger.critical({"event": "fetch_rss_uncaught_critical", "source": source_name, "url": url, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error.")
    return []  # Return empty list as fallback, though this line should never be reached due to exceptions


# --- API Endpoints ---
@app.get("/health", summary="Service Health Check", tags=["Health"], response_model=Dict[str, Any])
async def health_check(request: Request):
    logger.info({"event": "health_check_requested", "client_ip": request.client.host if request.client else "N/A"})
    global http_client
    is_http_client_ok = http_client is not None and not http_client.is_closed
    health_status = {
        "status": "ok" if is_http_client_ok else "error",
        "message": "Service is operational." if is_http_client_ok else "HTTP client issue.",
        "timestamp": asyncio.to_thread(lambda: __import__('datetime').datetime.now( # type: ignore
            __import__('datetime').timezone.utc).isoformat()
        ), # type: ignore
        "version": app.version,
        "services": {
            "http_client": "ok" if is_http_client_ok else "error: not initialized or closed",
            "cache": {"status": "ok", "size": len(feed_cache), "max_size": feed_cache.maxsize},
            "xml_parser": "lxml" if LXML_AVAILABLE else "xml.etree.ElementTree (fallback)"
        }
    }
    status_code = status.HTTP_200_OK if is_http_client_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/keywords", response_model=KeywordsResponse, summary="Get Trending Headlines", tags=["Trending"])
@limiter.limit(settings.RATE_LIMIT_SETTINGS)
async def get_keywords_endpoint( # Renamed to avoid conflict with any potential 'get_keywords' helper
    request: Request,
    geo: str = Query(settings.GEO_DEFAULT, min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
    limit: int = Query(settings.LIMIT_DEFAULT, ge=1, le=50),
    sources_query: Optional[str] = Query(None, alias="sources", description="Comma-separated sources")
):
    geo_upper = geo.upper()
    log_ctx = {"geo": geo_upper, "limit": limit, "client_ip": request.client.host if request.client else "N/A"}
    logger.info({**log_ctx, "event": "get_keywords_request", "req_sources": sources_query or "all"})

    active_feeds = RSS_FEEDS
    if sources_query:
        selected_s_names = {s.strip().lower() for s in sources_query.split(',')}
        active_feeds = {name: url for name, url in RSS_FEEDS.items() if name.lower() in selected_s_names}
        if not active_feeds:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid sources selected.")

    tasks = {name: fetch_rss_titles(name, url, geo_upper, limit) for name, url in active_feeds.items()}
    task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    final_results: Dict[str, List[str]] = {}
    errors_map: Dict[str, str] = {}
    for (s_name, _), res_or_exc in zip(tasks.items(), task_results):
        if isinstance(res_or_exc, Exception):
            err_detail = str(res_or_exc.detail if isinstance(res_or_exc, HTTPException) else res_or_exc)
            errors_map[s_name] = err_detail
            logger.warning({**log_ctx, "event": "source_fetch_error", "source": s_name, "error": err_detail})
        elif isinstance(res_or_exc, list):
            final_results[s_name] = res_or_exc
    return KeywordsResponse(results=final_results, errors=errors_map)

@app.get("/hashtags", response_model=HashtagsResponse, summary="Get Trending Hashtags", tags=["Trending"])
@limiter.limit(settings.RATE_LIMIT_SETTINGS)
async def get_hashtags_endpoint( # Renamed
    request: Request,
    geo: str = Query(settings.GEO_DEFAULT, min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
    limit: int = Query(settings.LIMIT_DEFAULT, ge=1, le=50),
    sources_query: Optional[str] = Query(None, alias="sources")
):
    geo_upper = geo.upper()
    log_ctx = {"geo": geo_upper, "limit": limit, "client_ip": request.client.host if request.client else "N/A"}
    logger.info({**log_ctx, "event": "get_hashtags_request", "req_sources": sources_query or "all"})
    try:
        # Call the keywords endpoint logic directly
        keywords_data = await get_keywords_endpoint(request, geo_upper, limit, sources_query)
    except HTTPException as e: # If get_keywords_endpoint itself raises (e.g. bad sources query)
        logger.error({**log_ctx, "event": "internal_keywords_fetch_http_error", "error": e.detail})
        return HashtagsResponse(results={}, errors={"keywords_fetch": f"Failed: {e.detail}"})

    hashtag_map: Dict[str, List[str]] = {}
    if keywords_data.results:
        for source, titles in keywords_data.results.items():
            valid_titles = [t for t in titles if t and t.strip()]
            hts = [slugify_to_hashtag(t) for t in valid_titles]
            hashtag_map[source] = [ht for ht in hts if ht and ht != "#"]
    return HashtagsResponse(results=hashtag_map, errors=keywords_data.errors)

# --- Uvicorn Runner (for local development without docker-compose run) ---
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Trending Service locally on port {settings.APP_PORT} with Uvicorn.")
    uvicorn.run(
        "main:app", # Assuming filename is main.py
        host="0.0.0.0",
        port=settings.APP_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=True # Enable reload for local development
    )
