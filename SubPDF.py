#!/usr/bin/env python3
############################################################################
# .oooooo..o              .o8       ooooooooo.   oooooooooo.   oooooooooooo#
#d8P'    `Y8             "888       `888   `Y88. `888'   `Y8b  `888'     `8#
#Y88bo.      oooo  oooo   888oooo.   888   .d88'  888      888  888        #
# `"Y8888o.  `888  `888   d88' `88b  888ooo88P'   888      888  888oooo8   #
#     `"Y88b  888   888   888   888  888          888      888  888    "   #
#oo     .d8P  888   888   888   888  888          888     d88'  888        #
#8""88888P'   `V88V"V8P'  `Y8bod8P' o888o        o888bood8P'   o888o       #
############################################################################

import os
import re
import time
import json
import logging
import argparse
import requests
import shutil
import tempfile
import tldextract
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfReader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

# -----------------------------------------------------------------------------
# Import tqdm for Progress Bars
# -----------------------------------------------------------------------------
try:
    from tqdm import tqdm
except ImportError:
    print("tqdm library not found. Install it using 'pip install tqdm'")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
# Initial logging setup; the level will be adjusted based on --debug flag
logging.basicConfig(
    level=logging.DEBUG,  # Temporary; will be overridden
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -----------------------------------------------------------------------------
# Default "Browser-like" Headers
# -----------------------------------------------------------------------------
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.google.com",
}

# Initialize a single session for all requests
session = requests.Session()

# -----------------------------------------------------------------------------
# Functions for Downloading, PDF Extraction, Domain Parsing
# -----------------------------------------------------------------------------

def get_all_pdf_links_from_website(base_url):
    """
    Crawl a single webpage (base_url) for any <a> tags whose href ends with .pdf.
    Returns a set of absolute PDF URLs.
    """
    logging.debug(f"Fetching PDF links from URL: {base_url}")
    pdf_links = set()

    try:
        resp = session.get(base_url, timeout=15)
        logging.debug(f"Response code for {base_url}: {resp.status_code}")
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)
                if full_url.lower().endswith(".pdf"):
                    pdf_links.add(full_url)
            logging.info(f"Found {len(pdf_links)} PDF link(s) on {base_url}")
        else:
            logging.warning(f"Non-200 status code {resp.status_code} for {base_url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {base_url}: {e}")
    return pdf_links

def download_pdf(pdf_url, download_folder):
    """
    Download a single PDF into the specified folder.
    Returns the local file path if successful, or None if failed.
    """
    logging.debug(f"Attempting to download PDF: {pdf_url}")
    os.makedirs(download_folder, exist_ok=True)

    filename = os.path.basename(urlparse(pdf_url).path) or "temp.pdf"
    filepath = os.path.join(download_folder, filename)

    if os.path.exists(filepath):
        logging.debug(f"PDF already exists. Skipping download: {filepath}")
        return filepath

    try:
        resp = session.get(pdf_url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            logging.info(f"PDF downloaded -> {filepath}")
            return filepath
        else:
            logging.warning(f"Failed to download {pdf_url}, status code {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error downloading {pdf_url}: {e}")

    return None

def extract_links_from_pdf(filepath):
    """
    Extracts ANY links from a PDF (annotations + text-based).
    Handles mailto:, ftp://, file://, http(s)://, etc.
    Returns a set of all URL strings found.
    """
    logging.debug(f"Extracting links from PDF: {filepath}")
    urls_found = set()

    # Check if file is non-empty
    if os.path.getsize(filepath) == 0:
        logging.error(f"Cannot read an empty file: {filepath}")
        return urls_found

    # 1) Annotation-based (clickable) links
    try:
        with open(filepath, "rb") as f:
            reader = PdfReader(f)
            for page_index, page in enumerate(reader.pages):
                if "/Annots" in page:
                    for annot in page["/Annots"]:
                        obj = annot.get_object()
                        if "/A" in obj and "/URI" in obj["/A"]:
                            uri = obj["/A"]["/URI"]
                            urls_found.add(uri)
                            logging.debug(f"Annotation link (page {page_index + 1}): {uri}")
    except Exception as e:
        logging.warning(f"Annotation-based extraction failed for {filepath}: {e}")

    # 2) Text-based (regex approach)
    try:
        with open(filepath, "rb") as f:
            reader = PdfReader(f)
            full_text = ""
            for page_index, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += text

        # mailto:, ftp://, file://, http(s):
        url_pattern = re.compile(
            r'(mailto:[^\s)]+|ftp://[^\s)]+|file://[^\s)]+|https?://[^\s)]+)'
        )
        matches = re.findall(url_pattern, full_text)
        for link in matches:
            urls_found.add(link.strip())
            logging.debug(f"Text-based link found: {link.strip()}")
    except Exception as e:
        logging.error(f"Text-based extraction failed on {filepath}: {e}")

    logging.info(f"Total unique links in '{os.path.basename(filepath)}': {len(urls_found)}")
    return urls_found

def parse_domains_from_links(link_set):
    """
    From a set of raw links, derive the final domains.
    Handles mailto: links by extracting domains from email addresses.
    """
    domains = set()
    for link in link_set:
        if link.lower().startswith("mailto:") and "@" in link:
            # Extract domain from email
            email_part = link.split("mailto:", 1)[1]
            if "@" in email_part:
                domain_part = email_part.split("@", 1)[1]
                domains.add(domain_part.lower())
            continue

        parsed = urlparse(link)
        if parsed.netloc:
            domains.add(parsed.netloc.lower())
    return domains

def handle_pdf_link(pdf_url, download_folder, ephemeral_mode):
    """
    Handles the entire process for a single PDF link:
    1. Download the PDF
    2. Extract links from the PDF
    3. Parse domains from the extracted links
    4. Delete the PDF if in ephemeral mode
    Returns a tuple: (pdf_filename, set_of_domains)
    """
    filepath = download_pdf(pdf_url, download_folder)
    if not filepath:
        logging.warning(f"Skipping extraction; download failed for {pdf_url}")
        return (os.path.basename(urlparse(pdf_url).path) or "temp.pdf", set())

    link_set = extract_links_from_pdf(filepath)
    domain_set = parse_domains_from_links(link_set)

    pdf_filename = os.path.basename(filepath)

    if ephemeral_mode:
        try:
            os.remove(filepath)
            logging.info(f"Deleted '{filepath}' -> {pdf_filename}")
        except OSError as e:
            logging.warning(f"Error removing {filepath}: {e}")

    return (pdf_filename, domain_set)

# -----------------------------------------------------------------------------
# Output Format Functions
# -----------------------------------------------------------------------------

def format_default(result_dict):
    """
    Verbose text-based output.
    """
    lines = []
    lines.append("\n========== Default Output ==========")
    for pdf_file, domains in result_dict.items():
        lines.append(f"PDF File: {pdf_file}")
        if not domains:
            lines.append("  -> (No domains/subdomains found)")
        else:
            for d in domains:
                lines.append(f"  -> {d}")
    lines.append("")
    return "\n".join(lines)

def format_simple(result_dict):
    """
    "Simple" => all extracted domains line-by-line (no extra labeling).
    """
    lines = []
    for pdf_file, domains in result_dict.items():
        for d in domains:
            lines.append(d)
    return "\n".join(lines) + "\n"

def format_json(result_dict):
    """
    JSON format
    """
    # Convert sets to lists for JSON serialization
    json_ready = {pdf: sorted(list(domains)) for pdf, domains in result_dict.items()}
    return json.dumps(json_ready, indent=2)

def format_list(result_dict):
    """
    List format with bullets
    """
    lines = []
    lines.append("\n========== List Format ==========")
    for pdf_file, domains in result_dict.items():
        lines.append(f"* {pdf_file}")
        if not domains:
            lines.append("  - (No domains found)")
        else:
            for d in domains:
                lines.append(f"  - {d}")
    lines.append("")
    return "\n".join(lines)

def format_domains(result_dict):
    """
    'domains' => uses tldextract to output only top-level or registered domains
    """
    all_domains = set()
    for pdf_file, domain_list in result_dict.items():
        for raw_domain in domain_list:
            extracted = tldextract.extract(raw_domain)
            if extracted.domain and extracted.suffix:
                reg = extracted.domain + "." + extracted.suffix
                all_domains.add(reg)
    lines = []
    lines.append("\n========== Domains Only ==========")
    for d in sorted(all_domains):
        lines.append(d)
    lines.append("")
    return "\n".join(lines)

# -----------------------------------------------------------------------------
# Main Function
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "CLI tool that processes URLs/PDFs in a multi-threaded fashion. "
            "If no --debug is given, displays a progress bar for status updates. "
            "If --debug is given, shows detailed logs."
        )
    )
    # Input sources
    parser.add_argument("-u", "--url", help="Webpage URL to crawl for PDF links.")
    parser.add_argument("-pu", "--pdf-url", help="Direct PDF link to parse.")
    parser.add_argument("-il", "--input-list", help="A text file with one URL per line.")
    parser.add_argument("-ij", "--input-json", help="A JSON file containing a list of URLs or 'urls' array.")

    # Storage
    parser.add_argument("-f", "--download-folder",
                        help="Store PDFs permanently here. Otherwise, PDFs are deleted after extraction.")

    # Headers
    parser.add_argument("-H", "--header", action="append",
                        help="Custom HTTP headers (like curl). Format: 'HeaderName: Value'. Can use multiple times.")

    # Output format
    parser.add_argument("--format", choices=["default", "simple", "json", "list", "domains"],
                        default="default",
                        help="Output style. Options: default | simple | json | list | domains.")

    # Output file
    parser.add_argument("--output-file",
                        help="Write final output to file (e.g., /home/user/output.txt). If omitted, prints to stdout.")

    # Thread count
    parser.add_argument("-t", "--threads", type=int, default=100,
                        help="Number of threads to use for PDF processing. Default = 100.")

    # Debug flag
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logs. Otherwise, shows progress bar with minimal info.")

    args = parser.parse_args()

    # 1) Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Debug mode enabled. Detailed logs will be shown.")
    else:
        logging.getLogger().setLevel(logging.WARNING)
        # Minimal output in normal mode

    # 2) Build final headers
    final_headers = dict(DEFAULT_HEADERS)
    if args.header:
        for header_line in args.header:
            if ':' in header_line:
                parts = header_line.split(':', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                final_headers[key] = val
                if args.debug:
                    logging.debug(f"Custom header set: '{key}' = '{val}'")
            else:
                logging.warning(f"Skipping malformed header: {header_line}")

    session.headers.update(final_headers)

    # 3) Decide ephemeral vs permanent
    if args.download_folder:
        ephemeral_mode = False
        download_folder = args.download_folder
        if args.debug:
            logging.info(f"Using permanent folder: {download_folder}")
        else:
            print(f"Using permanent folder: {download_folder}")
    else:
        ephemeral_mode = True
        download_folder = tempfile.mkdtemp(prefix="pdf_temp_")
        if args.debug:
            logging.info(f"Using temporary folder '{download_folder}', PDFs will be deleted after extraction.")
        else:
            print(f"Using temporary folder '{download_folder}', PDFs will be deleted after extraction.")

    # 4) Prepare results dict
    result = {}

    # 5) Collect all URLs to process
    all_urls = set()

    if args.url:
        all_urls.add(args.url)
    if args.pdf_url:
        all_urls.add(args.pdf_url)
    if args.input_list:
        if os.path.isfile(args.input_list):
            with open(args.input_list, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url:
                        all_urls.add(url)
        else:
            print(f"Input list file '{args.input_list}' not found.", file=sys.stderr)
            if args.debug:
                logging.error(f"Input list file '{args.input_list}' not found.")
    if args.input_json:
        if os.path.isfile(args.input_json):
            try:
                with open(args.input_json, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                if isinstance(data, list):
                    for url in data:
                        if isinstance(url, str) and url.strip():
                            all_urls.add(url.strip())
                elif isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], list):
                    for url in data['urls']:
                        if isinstance(url, str) and url.strip():
                            all_urls.add(url.strip())
                else:
                    print(f"JSON file '{args.input_json}' has an unexpected format.", file=sys.stderr)
                    if args.debug:
                        logging.error(f"JSON file '{args.input_json}' has an unexpected format.")
            except Exception as e:
                print(f"Error reading JSON file '{args.input_json}': {e}", file=sys.stderr)
                if args.debug:
                    logging.error(f"Error reading JSON file '{args.input_json}': {e}")
        else:
            print(f"JSON file '{args.input_json}' not found.", file=sys.stderr)
            if args.debug:
                logging.error(f"JSON file '{args.input_json}' not found.")

    # Remove any PDFs from URLs to prevent double-processing
    all_pdf_urls = set(url for url in all_urls if url.lower().endswith(".pdf"))
    all_webpage_urls = set(url for url in all_urls if not url.lower().endswith(".pdf"))

    # 6) Setup ThreadPoolExecutor with increased connection pool size
    max_workers = args.threads
    if args.debug:
        logging.info(f"Using up to {max_workers} threads for PDF processing.")
    else:
        print(f"Processing with up to {max_workers} threads...")

    # Configure the session's connection pool size
    retries = Retry(
        total=5,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )

    adapter = HTTPAdapter(
        pool_connections=max_workers,
        pool_maxsize=max_workers,
        max_retries=retries
    )

    session.mount('http://', adapter)
    session.mount('https://', adapter)

    with ThreadPoolExecutor(max_workers=max_workers) as threadpool:
        # Collect all PDF links first
        all_pdf_links = set()

        if args.url:
            # If processing a webpage, collect PDF links
            logging.debug(f"Collecting PDFs from webpage: {args.url}")
            webpage_pdf_links = get_all_pdf_links_from_website(args.url)
            all_pdf_links.update(webpage_pdf_links)
            if not args.debug:
                print(f"Found {len(webpage_pdf_links)} PDF link(s) on {args.url}")

        # Add all_pdf_urls
        all_pdf_links.update(all_pdf_urls)

        # Add PDFs from other webpages (if any)
        for webpage_url in all_webpage_urls:
            pdf_links = get_all_pdf_links_from_website(webpage_url)
            all_pdf_links.update(pdf_links)
            if not args.debug:
                print(f"Found {len(pdf_links)} PDF link(s) on {webpage_url}")

        total_pdfs = len(all_pdf_links)
        if total_pdfs == 0:
            if not args.debug:
                print("No PDF links found to process.")
            else:
                logging.warning("No PDF links found to process.")
            # Exit early
            pass

        # Initialize tqdm progress bar if not in debug mode
        if not args.debug and total_pdfs > 0:
            progress_bar = tqdm(total=total_pdfs, desc="Processing PDFs", unit="pdf")
        else:
            progress_bar = None

        # Submit all PDF links to threadpool
        futures = []
        for pdf_link in all_pdf_links:
            future = threadpool.submit(handle_pdf_link, pdf_link, download_folder, ephemeral_mode)
            futures.append(future)

        # Iterate through completed futures with progress bar
        if not args.debug and progress_bar:
            for fut in as_completed(futures):
                try:
                    pdf_filename, domain_set = fut.result()
                    if pdf_filename not in result:
                        result[pdf_filename] = set()
                    result[pdf_filename].update(domain_set)
                except Exception as e:
                    logging.error(f"Exception occurred while processing PDF: {e}")
                progress_bar.update(1)
            progress_bar.close()
        else:
            for fut in as_completed(futures):
                try:
                    pdf_filename, domain_set = fut.result()
                    if pdf_filename not in result:
                        result[pdf_filename] = set()
                    result[pdf_filename].update(domain_set)
                except Exception as e:
                    logging.error(f"Exception occurred while processing PDF: {e}")

    # 7) Remove temporary folder if ephemeral
    if ephemeral_mode:
        if args.debug:
            logging.info(f"Removing temporary folder: {download_folder}")
        else:
            print(f"Removing temporary folder: {download_folder}")
        try:
            shutil.rmtree(download_folder, ignore_errors=True)
            if not args.debug:
                print("Temporary folder removed.")
        except Exception as e:
            logging.warning(f"Error removing temporary folder '{download_folder}': {e}")
            if not args.debug:
                print(f"Error removing temporary folder '{download_folder}': {e}")

    # 8) Format the output
    format_choice = args.format
    if format_choice == "default":
        output_str = format_default(result)
    elif format_choice == "simple":
        output_str = format_simple(result)
    elif format_choice == "json":
        output_str = format_json(result)
    elif format_choice == "list":
        output_str = format_list(result)
    elif format_choice == "domains":
        output_str = format_domains(result)
    else:
        logging.warning(f"Unexpected format '{format_choice}', falling back to default.")
        output_str = format_default(result)

    # 9) Write or print output
    if args.output_file:
        if args.debug:
            logging.info(f"Writing output to: {args.output_file}")
        else:
            print(f"Writing output to: {args.output_file}")
        try:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output_str)
            if not args.debug:
                print("Output successfully written.")
        except Exception as e:
            logging.error(f"Error writing to output file '{args.output_file}': {e}")
            if not args.debug:
                print(f"Error writing to output file '{args.output_file}': {e}")
    else:
        print(output_str)

if __name__ == "__main__":
    LOGO = r"""
    ############################################################################
    # .oooooo..o              .o8       ooooooooo.   oooooooooo.   oooooooooooo#
    #d8P'    `Y8             "888       `888   `Y88. `888'   `Y8b  `888'     `8#
    #Y88bo.      oooo  oooo   888oooo.   888   .d88'  888      888  888        #
    # `"Y8888o.  `888  `888   d88' `88b  888ooo88P'   888      888  888oooo8   #
    #     `"Y88b  888   888   888   888  888          888      888  888    "   #
    #oo     .d8P  888   888   888   888  888          888     d88'  888        #
    #8""88888P'   `V88V"V8P'  `Y8bod8P' o888o        o888bood8P'   o888o       #
    #                                                       Made by Suman@ZERON#
    ############################################################################
    """
    print(LOGO)
    main()
