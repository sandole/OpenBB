# Developer Scripts

Utility scripts for maintaining OpenBB Platform data and configurations.

## Scripts

### `update_country_memberships.py`

Regenerates `openbb_platform/core/openbb_core/provider/utils/country_data.json` from authoritative sources.

**Why this exists:**
- Country group memberships change over time (NATO added Sweden in 2024, BRICS expanded in 2024-2025)
- Manual JSON edits are error-prone
- This script provides reproducible, documented updates with source links

**Usage:**
```bash
# Install dependencies
pip install pycountry

# Run the script
python scripts/update_country_memberships.py
```

**Updating memberships:**
1. Edit the `MEMBERSHIPS` dict in the script with new member codes
2. Update the `last_updated` date and add notes if relevant
3. Run the script to regenerate the JSON
4. Commit both the script changes and the updated JSON

**Sources tracked:**
- G7: Wikipedia
- G20: Wikipedia  
- EU: Wikipedia
- NATO: Official NATO website
- OECD: Official OECD website
- OPEC: Official OPEC website
- BRICS: Wikipedia

## Contributing

When adding new scripts:
1. Include comprehensive docstrings with usage examples
2. Document data sources with URLs
3. Add validation/error handling
4. Update this README
