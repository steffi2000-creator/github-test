
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


def fetch_pypi(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def check_dependencies(filename):
    dependencies_checked = 0
    packages_not_found = 0
    versions_not_found = 0
    oldest_release = None

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            dependencies_checked += 1

            if "==" not in line:
                continue

            name, version = line.split("==", 1)
            name = name.strip()
            version = version.strip()

            # Check whether the package exists
            package_url = f"https://pypi.org/pypi/{name}/json"
            package_data = fetch_pypi(package_url)

            if package_data is None:
                packages_not_found += 1
                continue

            # Check whether the pinned version exists
            version_url = f"https://pypi.org/pypi/{name}/{version}/json"
            version_data = fetch_pypi(version_url)

            if version_data is None:
                versions_not_found += 1
                continue

            # Find the first upload time of this release
            upload_times = []

            for item in version_data.get("urls", []):
                timestamp = item.get("upload_time_iso_8601")

                if timestamp:
                    upload_times.append(
                        datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    )

            if not upload_times:
                continue

            first_upload = min(upload_times)

            if oldest_release is None or first_upload < oldest_release[0]:
                oldest_release = (first_upload, name, version)

    print(f"Dependencies checked: {dependencies_checked}")
    print(f"Packages not on PyPI: {packages_not_found}")
    print(f"Versions not on PyPI: {versions_not_found}")

    if oldest_release:
        upload_time, name, version = oldest_release
        print(
            f"Oldest pinned release: "
            f"{name}=={version} ({upload_time.year})"
        )
    else:
        print("Oldest pinned release: None")


if __name__ == "__main__":
    check_dependencies("requirements.txt")
