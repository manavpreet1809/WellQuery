from typing import List, Dict, Optional
import requests
import json
from helpers.raw_storage import write_text

openFDA_URL = "https://api.fda.gov/drug/label.json"
default_fields = [
    "indications_and_usage",
    "dosage_and_administration",
    "warnings",
    "adverse_reactions",
    "contraindications",
]

def fetch_openfda_records(max_pages: int = 20, limit: int = 100, search: str = "openfda.brand_name:*", fields: Optional[List[str]] = None, timeout: int = 60, raw_base_path: Optional[str] = None) -> List[Dict]:
    fields = fields or default_fields

    records: List[Dict] = []
    skip = 0

    
    for page in range(max_pages):
        params = {"search": search, "limit": limit, "skip": skip}
        resp = requests.get(openFDA_URL, params=params, timeout=timeout)

        if resp.status_code == 404:
            break

        resp.raise_for_status()

        # save the raw page JSON if a base path is provided
        if raw_base_path is not None:
            raw_page_path = f"{raw_base_path}/page={page:04d}.json"
            write_text(raw_page_path, resp.text)

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for result in results:
            product = result.get("openfda", {})
            brand_name = ", ".join(product.get("brand_name", []))
            generic_name = ", ".join(product.get("generic_name", []))
            title = brand_name or generic_name or "Unknown"

            synonyms_list = []
            if brand_name:
                synonyms_list.append(brand_name)
            if generic_name:
                synonyms_list.append(generic_name)
            synonyms = "; ".join(sorted(set(synonyms_list))) if synonyms_list else None

            section_text: List[str] = []
            for key in fields:
                values = result.get(key)
                if isinstance(values, list):
                    section_text.extend(values)
                elif isinstance(values, str):
                    section_text.append(values)

            raw_text = "\n\n".join(section_text) if section_text else None

            records.append({
                "doc_id": f"openfda_{result.get('id')}",
                "category": "drug",
                "title": title,
                "synonyms": synonyms,
                "url": None,
                "raw_text": raw_text,
                "meta_json": json.dumps(result),
            })

        skip += limit

    return records