"""Moniker parsing utilities."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from .types import Moniker, MonikerPath, QueryParams


class MonikerParseError(ValueError):
    """Raised when a moniker string cannot be parsed."""
    pass


# Valid segment pattern: alphanumeric, hyphens, underscores, dots
# Must start with alphanumeric
SEGMENT_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.\-]*$")

# Namespace pattern: alphanumeric, hyphens, underscores (no dots - those are for paths)
NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]*$")

# Version pattern: digits (date) or alphanumeric (like "latest")
VERSION_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")

# Revision pattern: /vN where N is a positive integer
REVISION_PATTERN = re.compile(r"^v(\d+)$")


def validate_segment(segment: str) -> bool:
    """Check if a path segment is valid."""
    if not segment:
        return False
    if len(segment) > 128:
        return False
    return bool(SEGMENT_PATTERN.match(segment))


def validate_namespace(namespace: str) -> bool:
    """Check if a namespace is valid."""
    if not namespace:
        return False
    if len(namespace) > 64:
        return False
    return bool(NAMESPACE_PATTERN.match(namespace))


def parse_path(path_str: str, *, validate: bool = True) -> MonikerPath:
    """
    Parse a path string into a MonikerPath.

    Args:
        path_str: Path string like "indices.sovereign/developed/EUR"
        validate: Whether to validate segment names

    Returns:
        MonikerPath instance

    Raises:
        MonikerParseError: If path is invalid
    """
    if not path_str or path_str == "/":
        return MonikerPath.root()

    # Strip leading/trailing slashes
    clean = path_str.strip("/")
    if not clean:
        return MonikerPath.root()

    segments = clean.split("/")

    if validate:
        for seg in segments:
            if not validate_segment(seg):
                raise MonikerParseError(
                    f"Invalid path segment: '{seg}'. "
                    "Segments must start with alphanumeric and contain only "
                    "alphanumerics, hyphens, underscores, or dots."
                )

    return MonikerPath(tuple(segments))


def parse_moniker(moniker_str: str, *, validate: bool = True) -> Moniker:
    """
    Parse a full moniker string.

    Format: [namespace@]path/segments[@version][/vN][?query=params]

    Examples:
        indices.sovereign/developed/EUR/ALL
        commodities.derivatives/crypto/ETH@20260115/v2
        verified@reference.security/ISIN/US0378331005@latest
        user@analytics.risk/views/my-watchlist@20260115/v3
        moniker://holdings/20260115/fund_alpha?format=json

    Args:
        moniker_str: The moniker string to parse
        validate: Whether to validate segment names

    Returns:
        Moniker instance

    Raises:
        MonikerParseError: If moniker is invalid
    """
    if not moniker_str:
        raise MonikerParseError("Empty moniker string")

    moniker_str = moniker_str.strip()

    # Handle scheme
    if moniker_str.startswith("moniker://"):
        # Parse as URL
        parsed = urlparse(moniker_str)
        body = parsed.netloc + parsed.path
        query_str = parsed.query
    elif "://" in moniker_str:
        raise MonikerParseError(
            f"Invalid scheme. Expected 'moniker://' or no scheme, got: {moniker_str}"
        )
    else:
        # No scheme - check for query string
        if "?" in moniker_str:
            body, query_str = moniker_str.split("?", 1)
        else:
            body = moniker_str
            query_str = ""

    # Parse namespace (prefix before first @, but only if @ appears before first /)
    namespace = None
    remaining = body

    # Check for namespace@ prefix
    # The @ must appear before any / to be a namespace (otherwise it's a version)
    first_at = body.find("@")
    first_slash = body.find("/")

    if first_at != -1 and (first_slash == -1 or first_at < first_slash):
        # This @ is a namespace prefix
        namespace = body[:first_at]
        remaining = body[first_at + 1:]

        if validate and not validate_namespace(namespace):
            raise MonikerParseError(
                f"Invalid namespace: '{namespace}'. "
                "Namespace must start with a letter and contain only "
                "alphanumerics, hyphens, or underscores."
            )

    # Parse revision suffix (/vN at the end)
    revision = None
    if "/v" in remaining:
        # Find the last /vN pattern
        parts = remaining.rsplit("/v", 1)
        if len(parts) == 2:
            potential_rev = parts[1]
            # Check if it's a valid revision (just digits, possibly followed by more path or @version)
            # Actually revision should be at the very end or before ?
            rev_match = re.match(r"^(\d+)(?:$|(?=\?))", potential_rev)
            if rev_match:
                revision = int(rev_match.group(1))
                remaining = parts[0]

    # Parse version suffix (@version at the end of path, but before /vN)
    version = None
    if "@" in remaining:
        # Find the last @ that's a version (after all path segments)
        # The version @ comes after the last /
        last_slash_idx = remaining.rfind("/")
        at_idx = remaining.rfind("@")

        if at_idx > last_slash_idx:
            # This @ is a version suffix on the last segment
            version = remaining[at_idx + 1:]
            remaining = remaining[:at_idx]

            if validate and version and not VERSION_PATTERN.match(version):
                raise MonikerParseError(
                    f"Invalid version: '{version}'. "
                    "Version must be alphanumeric (e.g., 'latest', '20260115')."
                )

    # Parse path
    path = parse_path(remaining, validate=validate)

    # Parse query params
    params: dict[str, str] = {}
    if query_str:
        parsed_qs = parse_qs(query_str, keep_blank_values=True)
        # Take first value for each param (no multi-value support)
        for key, values in parsed_qs.items():
            if values:
                params[key] = values[0]

    return Moniker(
        path=path,
        namespace=namespace,
        version=version,
        revision=revision,
        params=QueryParams(params),
    )


def normalize_moniker(moniker_str: str) -> str:
    """
    Normalize a moniker string to canonical form.

    Always returns: moniker://[namespace@]path[@version][/vN][?sorted_params]
    """
    m = parse_moniker(moniker_str)
    return str(m)


def build_moniker(
    path: str,
    *,
    namespace: str | None = None,
    version: str | None = None,
    revision: int | None = None,
    **params: str,
) -> Moniker:
    """
    Build a Moniker from components.

    Args:
        path: The path string
        namespace: Optional namespace prefix
        version: Optional version (date or 'latest')
        revision: Optional revision number
        **params: Query parameters

    Returns:
        Moniker instance
    """
    return Moniker(
        path=parse_path(path),
        namespace=namespace,
        version=version,
        revision=revision,
        params=QueryParams(params) if params else QueryParams({}),
    )
