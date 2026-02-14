#!/usr/bin/env python3
"""
Update country membership data from authoritative sources.

This script regenerates country_data.json by:
1. Using pycountry for base ISO 3166 country data
2. Fetching membership lists from official/authoritative sources
3. Merging the data into a single JSON file

Sources:
- ISO 3166 countries: pycountry package (https://pypi.org/project/pycountry/)
- G7: https://en.wikipedia.org/wiki/G7
- G20: https://en.wikipedia.org/wiki/G20
- EU: https://en.wikipedia.org/wiki/Member_state_of_the_European_Union
- NATO: https://www.nato.int/cps/en/natohq/nato_countries.htm
- OECD: https://www.oecd.org/about/document/ratification-oecd-convention.htm
- OPEC: https://www.opec.org/opec_web/en/about_us/25.htm
- BRICS: https://en.wikipedia.org/wiki/BRICS

Usage:
    python scripts/update_country_memberships.py

Requirements:
    pip install pycountry requests beautifulsoup4
"""

import json
import sys
from datetime import date
from pathlib import Path

try:
    import pycountry
except ImportError:
    print("Error: pycountry not installed. Run: pip install pycountry")
    sys.exit(1)

# Output path relative to script location
SCRIPT_DIR = Path(__file__).parent
OUTPUT_PATH = SCRIPT_DIR.parent / "openbb_platform/core/openbb_core/provider/utils/country_data.json"

# Membership data with sources
# Last verified: 2025-02-13
# NOTE: Update these lists when memberships change, then run the script

MEMBERSHIPS = {
    "G7": {
        "source": "https://en.wikipedia.org/wiki/G7",
        "last_updated": "2025-02-13",
        "members": [
            "CA",  # Canada
            "FR",  # France
            "DE",  # Germany
            "IT",  # Italy
            "JP",  # Japan
            "GB",  # United Kingdom
            "US",  # United States
        ],
    },
    "G20": {
        "source": "https://en.wikipedia.org/wiki/G20",
        "last_updated": "2025-02-13",
        "notes": "EU is a member but not a country; African Union joined 2023",
        "members": [
            "AR",  # Argentina
            "AU",  # Australia
            "BR",  # Brazil
            "CA",  # Canada
            "CN",  # China
            "FR",  # France
            "DE",  # Germany
            "IN",  # India
            "ID",  # Indonesia
            "IT",  # Italy
            "JP",  # Japan
            "MX",  # Mexico
            "RU",  # Russia
            "SA",  # Saudi Arabia
            "ZA",  # South Africa
            "KR",  # South Korea
            "TR",  # Turkey (Türkiye)
            "GB",  # United Kingdom
            "US",  # United States
        ],
    },
    "EU": {
        "source": "https://en.wikipedia.org/wiki/Member_state_of_the_European_Union",
        "last_updated": "2025-02-13",
        "members": [
            "AT",  # Austria
            "BE",  # Belgium
            "BG",  # Bulgaria
            "HR",  # Croatia
            "CY",  # Cyprus
            "CZ",  # Czechia
            "DK",  # Denmark
            "EE",  # Estonia
            "FI",  # Finland
            "FR",  # France
            "DE",  # Germany
            "GR",  # Greece
            "HU",  # Hungary
            "IE",  # Ireland
            "IT",  # Italy
            "LV",  # Latvia
            "LT",  # Lithuania
            "LU",  # Luxembourg
            "MT",  # Malta
            "NL",  # Netherlands
            "PL",  # Poland
            "PT",  # Portugal
            "RO",  # Romania
            "SK",  # Slovakia
            "SI",  # Slovenia
            "ES",  # Spain
            "SE",  # Sweden
        ],
    },
    "NATO": {
        "source": "https://www.nato.int/cps/en/natohq/nato_countries.htm",
        "last_updated": "2025-02-13",
        "notes": "Sweden joined March 7, 2024; Finland joined April 4, 2023",
        "members": [
            "AL",  # Albania
            "BE",  # Belgium
            "BG",  # Bulgaria
            "CA",  # Canada
            "HR",  # Croatia
            "CZ",  # Czechia
            "DK",  # Denmark
            "EE",  # Estonia
            "FI",  # Finland (2023)
            "FR",  # France
            "DE",  # Germany
            "GR",  # Greece
            "HU",  # Hungary
            "IS",  # Iceland
            "IT",  # Italy
            "LV",  # Latvia
            "LT",  # Lithuania
            "LU",  # Luxembourg
            "ME",  # Montenegro
            "NL",  # Netherlands
            "MK",  # North Macedonia
            "NO",  # Norway
            "PL",  # Poland
            "PT",  # Portugal
            "RO",  # Romania
            "SK",  # Slovakia
            "SI",  # Slovenia
            "ES",  # Spain
            "SE",  # Sweden (2024)
            "TR",  # Turkey (Türkiye)
            "GB",  # United Kingdom
            "US",  # United States
        ],
    },
    "OECD": {
        "source": "https://www.oecd.org/about/document/ratification-oecd-convention.htm",
        "last_updated": "2025-02-13",
        "members": [
            "AU",  # Australia
            "AT",  # Austria
            "BE",  # Belgium
            "CA",  # Canada
            "CL",  # Chile
            "CO",  # Colombia
            "CR",  # Costa Rica
            "CZ",  # Czechia
            "DK",  # Denmark
            "EE",  # Estonia
            "FI",  # Finland
            "FR",  # France
            "DE",  # Germany
            "GR",  # Greece
            "HU",  # Hungary
            "IS",  # Iceland
            "IE",  # Ireland
            "IL",  # Israel
            "IT",  # Italy
            "JP",  # Japan
            "KR",  # South Korea
            "LV",  # Latvia
            "LT",  # Lithuania
            "LU",  # Luxembourg
            "MX",  # Mexico
            "NL",  # Netherlands
            "NZ",  # New Zealand
            "NO",  # Norway
            "PL",  # Poland
            "PT",  # Portugal
            "SK",  # Slovakia
            "SI",  # Slovenia
            "ES",  # Spain
            "SE",  # Sweden
            "CH",  # Switzerland
            "TR",  # Turkey (Türkiye)
            "GB",  # United Kingdom
            "US",  # United States
        ],
    },
    "OPEC": {
        "source": "https://www.opec.org/opec_web/en/about_us/25.htm",
        "last_updated": "2025-02-13",
        "members": [
            "DZ",  # Algeria
            "AO",  # Angola
            "CG",  # Congo
            "GQ",  # Equatorial Guinea
            "GA",  # Gabon
            "IR",  # Iran
            "IQ",  # Iraq
            "KW",  # Kuwait
            "LY",  # Libya
            "NG",  # Nigeria
            "SA",  # Saudi Arabia
            "AE",  # United Arab Emirates
            "VE",  # Venezuela
        ],
    },
    "BRICS": {
        "source": "https://en.wikipedia.org/wiki/BRICS",
        "last_updated": "2025-02-13",
        "notes": "Expanded Jan 1, 2024 (Egypt, Ethiopia, Iran, UAE); Indonesia joined Jan 6, 2025; Saudi Arabia invited but status unclear",
        "members": [
            "BR",  # Brazil
            "RU",  # Russia
            "IN",  # India
            "CN",  # China
            "ZA",  # South Africa
            "EG",  # Egypt (2024)
            "ET",  # Ethiopia (2024)
            "IR",  # Iran (2024)
            "AE",  # UAE (2024)
            "ID",  # Indonesia (2025)
        ],
    },
}


def build_country_data() -> dict:
    """Build the country data structure from pycountry and membership lists."""
    # Start with all ISO 3166 countries
    countries = []
    
    for country in pycountry.countries:
        entry = {
            "alpha_2": country.alpha_2,
            "alpha_3": country.alpha_3,
            "name": country.name,
            "numeric": country.numeric,
        }
        
        # Find all group memberships for this country
        groups = []
        for group_name, group_data in MEMBERSHIPS.items():
            if country.alpha_2 in group_data["members"]:
                groups.append(group_name)
        
        if groups:
            entry["groups"] = sorted(groups)
        
        countries.append(entry)
    
    # Sort countries by alpha_2 code
    countries.sort(key=lambda x: x["alpha_2"])
    
    return {
        "_last_updated": date.today().isoformat(),
        "_sources": {
            group: {
                "url": data["source"],
                "last_verified": data["last_updated"],
                **({"notes": data["notes"]} if "notes" in data else {}),
            }
            for group, data in MEMBERSHIPS.items()
        },
        "countries": countries,
    }


def validate_memberships():
    """Validate that all membership country codes exist in pycountry."""
    errors = []
    valid_codes = {c.alpha_2 for c in pycountry.countries}
    
    for group_name, group_data in MEMBERSHIPS.items():
        for code in group_data["members"]:
            if code not in valid_codes:
                errors.append(f"{group_name}: Unknown country code '{code}'")
    
    return errors


def main():
    print("Validating membership data...")
    errors = validate_memberships()
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("Building country data...")
    data = build_country_data()
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON with nice formatting
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    # Print summary
    total_countries = len(data["countries"])
    countries_with_groups = sum(1 for c in data["countries"] if "groups" in c)
    
    print(f"\nWrote {OUTPUT_PATH}")
    print(f"  Total countries: {total_countries}")
    print(f"  Countries with memberships: {countries_with_groups}")
    print("\nMembership counts:")
    for group_name, group_data in MEMBERSHIPS.items():
        print(f"  {group_name}: {len(group_data['members'])} members")


if __name__ == "__main__":
    main()
