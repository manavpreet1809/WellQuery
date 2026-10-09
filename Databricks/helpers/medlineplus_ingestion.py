import requests
import io
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from typing import List, Dict, Optional

# scrape medlineplus and get the url of most recent 'MedlinePlus Compressed Health Topic XML' file
def get_latest_medlineplus_zip_url(timeout: int = 30) -> str:
    index_url = "https://medlineplus.gov/xml.html"
    resp = requests.get(index_url, timeout=timeout) # get the page that has the latest xml file
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser") # parse the page

    # find the compressed xml file
    for a in soup.find_all("a", href=True):
        if "MedlinePlus Compressed Health Topic XML" in a.get_text(strip=True):
            href = a["href"]
            # Make absolute if needed
            if href.startswith("http"):
                return href
            return f"https://medlineplus.gov/{href.lstrip('/')}"
    raise RuntimeError("Could not find MedlinePlus Compressed Health Topic XML link on xml.html")

def download_medlineplus_zip(zip_url: str, timeout: int = 60) -> bytes:
    response = requests.get(zip_url, timeout=timeout) # get the zip file
    response.raise_for_status()
    return response.content

def extract_first_xml_from_zip(zip_bytes: bytes) -> bytes:
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    xml_name = next(name for name in zip_file.namelist() if name.endswith(".xml"))
    return zip_file.read(xml_name)

def parse_medlineplus_xml_to_records(xml_bytes: bytes) -> List[Dict]:
    root = ET.fromstring(xml_bytes)
    records: List[Dict] = []

    for topic in root.findall(".//health-topic"):
        topic_id = topic.get("id")
        title = topic.attrib.get("title")
        url = topic.attrib.get("url")
        language = topic.attrib.get("language", "English")

        if (language or "").lower() != "english":
            continue

        also_called_elements = topic.findall("./also-called")
        synonyms_list = [
            element.text.strip()
            for element in also_called_elements
            if element is not None and element.text
        ]
        synonyms = "; ".join(synonyms_list) if synonyms_list else None

        full_text_tag = topic.find("./full-summary")
        raw_html = ET.tostring(full_text_tag, encoding="unicode") if full_text_tag is not None else None

        records.append({
            "doc_id": f"medline_{topic_id}",
            "category": "condition",
            "title": title,
            "synonyms": synonyms,
            "url": url,
            "raw_text": raw_html,
            "meta_json": None,
        })

    return records

def fetch_medlineplus_records(timeout_index: int = 30, timeout_zip: int = 60) -> List[Dict]:
    zip_url = get_latest_medlineplus_zip_url(timeout=timeout_index)
    zip_bytes = download_medlineplus_zip(zip_url, timeout=timeout_zip)
    xml_bytes = extract_first_xml_from_zip(zip_bytes)
    return parse_medlineplus_xml_to_records(xml_bytes)