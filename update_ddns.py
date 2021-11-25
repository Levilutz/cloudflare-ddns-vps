#!/usr/bin/python3
"""Update DNS records."""

import logging
import os
import sys

from CloudFlare import CloudFlare
from CloudFlare.exceptions import (
    CloudFlareError,
    CloudFlareInternalError,
    CloudFlareAPIError,
)
import requests


DEBUG = True

if DEBUG:
    logging.getLogger().setLevel(logging.INFO)


# Helper functions
def get_public_ip() -> str:
    """Get our public IP address.

    Using https://api.ipify.org/ as it has strong backing and guarantees stability.

    It would be nice if I could use https://www.cloudflare.com/cdn-cgi/trace, but that
    endpoint isn't necessarily stable. 
    """
    return requests.get("https://api.ipify.org/").text


def get_api(token: str) -> CloudFlare:
    """Get the Cloudflare API object and verify token."""
    api = CloudFlare(token=token)
    try:
        api.user.tokens.verify.get()
    except (
        CloudFlareError,
        CloudFlareInternalError,
        CloudFlareAPIError,
    ):
        logging.error("Failed to verify, token likely invalid")
        raise
    return api


def get_zone_id(api: CloudFlare, zone_name: str) -> str:
    """Get a zone id from a zone name."""
    # Get matching zones
    zones = api.zones.get()
    matching_zones = [zone for zone in zones if zone["name"] == zone_name]

    # Ensure we got exactly one
    if not matching_zones:
        zone_names = [zone["name"] for zone in zones]
        logging.error(f"No matching zone for {zone_name} in {zone_names}")
        raise Exception("Failed to find zone")
    if len(matching_zones) > 1:
        logging.error(f"Found multiple matching zones for {zone_name} in {zones}")
        raise Exception("Found multiple zones")

    # Return
    return matching_zones[0]["id"]


# Main function
def update_ddns(token: str, zone_name: str, dns_name: str):
    """Update Cloudflare DNS.

    args:
        token: Your Cloudflare Api Token
        zone_name: The name of the target zone, e.g. 'example.com'
        dns_name: The full url we are DDNSing to us, e.g. 'api.example.com'
    """
    # Get our public ip
    public_ip = get_public_ip()
    logging.info(f"Got public ip: {public_ip}")

    # Get api
    api = get_api(token=token)
    logging.info("Api verified")

    # Get zone id
    zone_id = get_zone_id(api=api, zone_name=zone_name)
    logging.info(f"Found zone_name {zone_name}: {zone_id}")

    # Get zone dns records and clear old ones
    valid_exists = False
    query = {
        "name": dns_name,
        "type": "A",
    }
    zone_dns_records = api.zones.dns_records.get(zone_id, params=query)
    for dns_record in zone_dns_records:
        if dns_record["content"] != public_ip or valid_exists:
            logging.info(f"Deleting unwanted record: {dns_record['id']}")
            api.zones.dns_records.delete(zone_id, dns_record["id"])
        else:
            logging.info(f"Found matching record: {dns_record['id']}")
            valid_exists = True

    # Add a new record if necessary
    if not valid_exists:
        logging.info("No valid record, creating new one")
        dns_record_data = {
            "name": dns_name,
            "type": "A",
            "content": public_ip,
            "TTL": 300,
        }
        dns_record = api.zones.dns_records.post(zone_id, data=dns_record_data)
        logging.info(f"Created new record: {dns_record['id']}")
    else:
        logging.info("Matching record exists, no need for new one")

    logging.info("Complete")


# Run if we are directly called
if __name__ == "__main__":
    """Run the main function from either cli args or env vars, or fail if neither."""
    if len(sys.argv) == 4:
        # CLI args
        token = sys.argv[1]
        zone_name = sys.argv[2]
        dns_name = sys.argv[3]
    elif len(sys.argv) == 1:
        # Env vars
        token = os.environ["CLOUDFLARE_TOKEN"]
        zone_name = os.environ["CLOUDFLARE_ZONE_NAME"]
        dns_name = os.environ["CLOUDFLARE_DNS_NAME"]
    else:
        raise Exception("Supply either all CLI args or all env vars")

    update_ddns(token=token, zone_name=zone_name, dns_name=dns_name)
