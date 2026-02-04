#!/usr/bin/env python
"""
Sample Queries Demo - Interactive demonstration of the Moniker Service.

Run with: python demo/sample_queries.py
Requires the service to be running: python start.py
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE_URL = "http://localhost:8050"


def fetch(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    """Fetch from the API and return JSON response."""
    url = f"{BASE_URL}{endpoint}"
    try:
        req = Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if data:
            req.data = json.dumps(data).encode()
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        try:
            error_body = json.loads(e.read().decode())
            print(f"  Detail: {error_body.get('detail', 'No detail')}")
        except Exception:
            pass
        return None
    except URLError as e:
        print(f"  Connection Error: {e.reason}")
        print("  Is the service running? Start with: python start.py")
        return None


def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


def header(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# =============================================================================
# Menu Options
# =============================================================================

def option_1_health():
    """Health Check"""
    header("1. Health Check")
    print("\nChecking service health...")
    result = fetch("/health")
    if result:
        print(f"\n  Status: {result['status']}")
        print(f"  Cache size: {result['cache']['size']}")
        print(f"  Telemetry emitted: {result['telemetry']['emitted']}")
        print("\n  Full response:")
        print_json(result)


def option_2_resolve_equity():
    """Resolve - Equity Price (Snowflake)"""
    header("2. Resolve Moniker - Equity Price")
    print("\nResolving: moniker://prices.equity/AAPL")
    print("This returns connection info for Snowflake - client connects directly.\n")
    result = fetch("/resolve/prices.equity/AAPL")
    if result:
        print(f"  Source Type: {result['source_type']}")
        print(f"  Binding Path: {result['binding_path']}")
        print(f"  Connection: {result['connection']}")
        print(f"\n  Query to execute:")
        print(f"  {result['query'][:200]}..." if len(result.get('query', '')) > 200 else f"  {result.get('query')}")


def option_3_resolve_rest():
    """Resolve - Risk VaR (REST API)"""
    header("3. Resolve Moniker - Risk VaR (REST)")
    print("\nResolving: moniker://analytics.risk/var/portfolio-123")
    print("This returns REST API connection info.\n")
    result = fetch("/resolve/analytics.risk/var/portfolio-123")
    if result:
        print(f"  Source Type: {result['source_type']}")
        print(f"  Base URL: {result['connection'].get('base_url')}")
        print(f"  Auth Type: {result['connection'].get('auth_type')}")
        print(f"  Path: {result['query']}")


def option_4_resolve_oracle():
    """Resolve - Security Master (Oracle)"""
    header("4. Resolve Moniker - Security Master (Oracle)")
    print("\nResolving: moniker://reference.security/ISIN/US0378331005")
    print("This returns Oracle connection info.\n")
    result = fetch("/resolve/reference.security/ISIN/US0378331005")
    if result:
        print(f"  Source Type: {result['source_type']}")
        print(f"  DSN: {result['connection'].get('dsn')}")
        print(f"\n  Query:")
        print(f"  {result.get('query', 'N/A')}")


def option_5_fetch_equity():
    """Fetch - Equity Price (Server-side execution)"""
    header("5. Fetch Data - Equity Price")
    print("\nFetching: moniker://prices.equity/AAPL")
    print("Server executes the query and returns data directly.\n")
    result = fetch("/fetch/prices.equity/AAPL?limit=5")
    if result:
        print(f"  Rows returned: {result['row_count']}")
        print(f"  Columns: {result['columns']}")
        print(f"  Execution time: {result['execution_time_ms']}ms")
        print(f"\n  Data sample:")
        for row in result['data'][:3]:
            print(f"    {row}")


def option_6_fetch_crypto():
    """Fetch - Crypto (REST pass-through)"""
    header("6. Fetch Data - Digital Assets")
    print("\nFetching: moniker://commodities.derivatives/crypto/ETH")
    print("Server calls REST API and returns data.\n")
    result = fetch("/fetch/commodities.derivatives/crypto/ETH?limit=5")
    if result:
        print(f"  Source Type: {result['source_type']}")
        print(f"  Rows: {result['row_count']}")
        if result['data']:
            print(f"\n  Data sample:")
            for row in result['data'][:3]:
                print(f"    {row}")


def option_7_describe():
    """Describe - Get metadata about a path"""
    header("7. Describe Moniker")
    print("\nDescribing: moniker://analytics")
    print("Returns metadata, ownership, classification.\n")
    result = fetch("/describe/analytics")
    if result:
        print(f"  Path: {result['path']}")
        print(f"  Display Name: {result['display_name']}")
        print(f"  Classification: {result['classification']}")
        print(f"  Has Source: {result['has_source_binding']}")
        print(f"\n  Ownership:")
        for key, val in result['ownership'].items():
            if val and not key.endswith('_source'):
                print(f"    {key}: {val}")


def option_8_lineage():
    """Lineage - Ownership provenance"""
    header("8. Ownership Lineage")
    print("\nLineage for: moniker://analytics.risk/var")
    print("Shows where each ownership field is inherited from.\n")
    result = fetch("/lineage/analytics.risk/var")
    if result:
        print(f"  Path: {result['path']}")
        print(f"\n  Ownership inheritance:")
        for key, val in result['ownership'].items():
            if not key.endswith('_at') and val:
                source = result['ownership'].get(f"{key}_defined_at", "unknown")
                print(f"    {key}: {val} (from: {source})")


def option_9_list_children():
    """List - Children of a path"""
    header("9. List Children")
    print("\nListing children of: moniker://reference")
    result = fetch("/list/reference")
    if result:
        print(f"  Path: {result['path']}")
        print(f"  Children: {result['children']}")


def option_10_sample():
    """Sample - Quick data preview"""
    header("10. Sample Data")
    print("\nSampling: moniker://indices.sovereign/developed")
    print("Quick preview of data structure.\n")
    result = fetch("/sample/indices.sovereign/developed/EU.GovBondAgg/EUR/ALL?limit=3")
    if result:
        print(f"  Columns: {result['columns']}")
        print(f"  Row count: {result['row_count']}")
        if result['data']:
            print(f"\n  Sample rows:")
            for row in result['data']:
                print(f"    {row}")


def option_11_metadata():
    """Metadata - AI/Agent discoverability"""
    header("11. Rich Metadata (for AI agents)")
    print("\nMetadata for: moniker://holdings/positions")
    print("Returns comprehensive info for AI discoverability.\n")
    result = fetch("/metadata/holdings/positions")
    if result:
        print(f"  Path: {result['path']}")
        print(f"  Display Name: {result['display_name']}")
        if result.get('schema'):
            print(f"  Granularity: {result['schema'].get('granularity')}")
        if result.get('ownership'):
            print(f"  Owner: {result['ownership'].get('accountable_owner')}")


def option_12_tree():
    """Tree - Hierarchical view"""
    header("12. Catalog Tree")
    print("\nTree view of: analytics\n")
    result = fetch("/tree/analytics")
    if result:
        def print_tree(node, indent=0):
            prefix = "  " * indent
            source = f" [{node.get('source_type')}]" if node.get('source_type') else ""
            print(f"{prefix}- {node['name']}/{source}")
            for child in node.get('children', []):
                print_tree(child, indent + 1)
        print_tree(result)


def option_13_batch_validate():
    """Batch Validate - Multiple monikers"""
    header("13. Batch Moniker Validation")
    monikers = [
        "prices.equity/AAPL",
        "prices.equity/MSFT",
        "analytics.risk/var/portfolio-1",
        "reference.security/ISIN/US0378331005",
        "invalid/path/does/not/exist",
    ]
    print(f"\nValidating {len(monikers)} monikers...\n")

    for moniker in monikers:
        result = fetch(f"/describe/{moniker}")
        if result:
            status = "HAS SOURCE" if result.get('has_source_binding') else "NO SOURCE"
            print(f"  {moniker}")
            print(f"    -> {status}, classification: {result.get('classification', 'N/A')}")
        else:
            print(f"  {moniker}")
            print(f"    -> NOT FOUND")


def option_14_list_domains():
    """List Data Domains - Top-level catalog paths"""
    header("14. List Data Domains")
    print("\nTop-level data domains in the catalog:\n")
    result = fetch("/catalog")
    if result:
        # Extract unique top-level domains
        domains = set()
        for path in result.get('paths', []):
            top = path.split('/')[0].split('.')[0]
            domains.add(top)

        domains = sorted(domains)
        print(f"  Found {len(domains)} top-level domains:\n")
        for i, domain in enumerate(domains, 1):
            # Get domain info
            info = fetch(f"/describe/{domain}")
            if info:
                desc = info.get('description', '')[:50] or info.get('display_name', domain)
                print(f"  {i:2}. {domain:20} - {desc}")
            else:
                print(f"  {i:2}. {domain}")


def option_15_domain_metadata_1():
    """Domain Metadata - Analytics"""
    header("15. Domain Metadata - Analytics")
    print("\nFull metadata for 'analytics' domain:\n")
    result = fetch("/describe/analytics")
    if result:
        print_json(result)


def option_16_domain_metadata_2():
    """Domain Metadata - Reference Data"""
    header("16. Domain Metadata - Reference Data")
    print("\nFull metadata for 'reference' domain:\n")
    result = fetch("/describe/reference")
    if result:
        print_json(result)


def option_17_list_mappings():
    """List Mappings - Full catalog structure"""
    header("17. Full Catalog Mapping")
    print("\nAll registered paths with source bindings:\n")
    result = fetch("/catalog")
    if result:
        paths = sorted(result.get('paths', []))
        print(f"  Total paths: {len(paths)}\n")

        # Group by top-level domain
        by_domain = {}
        for path in paths:
            domain = path.split('/')[0].split('.')[0]
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(path)

        for domain in sorted(by_domain.keys()):
            print(f"  {domain}/")
            for path in by_domain[domain]:
                # Check if it has a source binding
                info = fetch(f"/describe/{path}")
                if info and info.get('has_source_binding'):
                    print(f"    -> {path} [{info.get('source_type')}]")
                else:
                    print(f"    -> {path}")


def option_space():
    """Space info"""
    header("Moniker Service Info")
    print("""
  Moniker Service - Data Catalog Resolution

  The service resolves "monikers" (logical data paths) to actual
  data source connections. It supports:

  - Snowflake, Oracle, REST APIs, Static files, Excel, Bloomberg, etc.
  - Ownership inheritance through path hierarchy
  - Access policies for query guardrails
  - AI/Agent-friendly metadata endpoints

  Architecture:
    Client -> Moniker Service -> Returns connection info
    Client -> Connects directly to data source

  Or for convenience:
    Client -> /fetch endpoint -> Service executes query -> Returns data

  Config UI: http://localhost:8050/config/ui
  API Docs:  http://localhost:8050/docs
""")


# =============================================================================
# Main Menu
# =============================================================================

MENU = """
╔════════════════════════════════════════════════════════════════╗
║                    MONIKER SERVICE DEMO                        ║
╠════════════════════════════════════════════════════════════════╣
║  1.  Health Check                                              ║
║                                                                ║
║  --- Resolution (returns connection info) ---                  ║
║  2.  Resolve - Equity Price (Snowflake)                        ║
║  3.  Resolve - Risk VaR (REST API)                             ║
║  4.  Resolve - Security Master (Oracle)                        ║
║                                                                ║
║  --- Fetch (server-side execution) ---                         ║
║  5.  Fetch - Equity Price data                                 ║
║  6.  Fetch - Digital Assets (REST pass-through)                ║
║                                                                ║
║  --- Metadata & Discovery ---                                  ║
║  7.  Describe - Path metadata                                  ║
║  8.  Lineage - Ownership provenance                            ║
║  9.  List - Children of a path                                 ║
║  10. Sample - Quick data preview                               ║
║  11. Metadata - AI/Agent discovery info                        ║
║  12. Tree - Hierarchical view                                  ║
║                                                                ║
║  --- Batch & Catalog ---                                       ║
║  13. Batch Validate - Multiple monikers                        ║
║  14. List Data Domains                                         ║
║  15. Domain Metadata - Analytics                               ║
║  16. Domain Metadata - Reference Data                          ║
║  17. List Full Mapping                                         ║
║                                                                ║
║  SPACE - Service Info    Q - Quit                              ║
╚════════════════════════════════════════════════════════════════╝
"""

OPTIONS = {
    '1': option_1_health,
    '2': option_2_resolve_equity,
    '3': option_3_resolve_rest,
    '4': option_4_resolve_oracle,
    '5': option_5_fetch_equity,
    '6': option_6_fetch_crypto,
    '7': option_7_describe,
    '8': option_8_lineage,
    '9': option_9_list_children,
    '10': option_10_sample,
    '11': option_11_metadata,
    '12': option_12_tree,
    '13': option_13_batch_validate,
    '14': option_14_list_domains,
    '15': option_15_domain_metadata_1,
    '16': option_16_domain_metadata_2,
    '17': option_17_list_mappings,
    ' ': option_space,
}


def main():
    print("\n" + "=" * 60)
    print("  Moniker Service Demo")
    print("  Ensure service is running: python start.py")
    print("=" * 60)

    while True:
        print(MENU)
        choice = input("  Select option: ").strip().lower()

        if choice == 'q':
            print("\n  Goodbye!\n")
            break
        elif choice in OPTIONS:
            OPTIONS[choice]()
            input("\n  Press Enter to continue...")
        else:
            print(f"\n  Invalid option: {choice}")


if __name__ == "__main__":
    main()
