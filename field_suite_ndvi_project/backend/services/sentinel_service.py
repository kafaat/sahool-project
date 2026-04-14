import os
import requests
import glob
import zipfile

SCI_HUB = "https://scihub.copernicus.eu/dhus"

SENTINEL_USER = os.getenv("SENTINEL_USER", "")
SENTINEL_PASS = os.getenv("SENTINEL_PASS", "")


class SentinelService:

    @staticmethod
    def search_product(aoi_wkt: str, date: str) -> str:
        query = (
            f"platformname:Sentinel-2 AND "
            f"producttype:S2MSI2A AND "
            f"beginposition:[{date}T00:00:00.000Z TO {date}T23:59:59.999Z] AND "
            f"footprint:\"Intersects({aoi_wkt})\""
        )
        params = {"q": query, "format": "json"}
        r = requests.get(
            f"{SCI_HUB}/search",
            params=params,
            auth=(SENTINEL_USER, SENTINEL_PASS),
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            raise RuntimeError("No Sentinel-2 products found")
        return entries[0]["id"]

    @staticmethod
    def download_product(product_id: str, out_path: str):
        r = requests.get(
            f"{SCI_HUB}/odata/v1/Products('{product_id}')/\$value",
            auth=(SENTINEL_USER, SENTINEL_PASS),
            stream=True,
            timeout=600,
        )
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    @staticmethod
    def get_bands_paths_from_zip(zip_path: str, workdir: str):
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(workdir)

        b04 = glob.glob(os.path.join(workdir, "**/*B04*.jp2"), recursive=True)
        b08 = glob.glob(os.path.join(workdir, "**/*B08*.jp2"), recursive=True)

        if not b04 or not b08:
            raise RuntimeError("Could not find B04/B08 bands")

        return b04[0], b08[0]
