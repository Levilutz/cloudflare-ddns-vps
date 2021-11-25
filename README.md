# cloudflare-ddns-vps
Lightweight script to enable DDNS using Cloudflare, made with VPSs in mind. 

## Purpose
Let's say I have a little VPS that I just spun up with a public IP address. I want this VPS to serve something (an API, static web content, etc) on the public internet. Furthermore, I want this VPS to be accessible through a .com domain I own and manage through Cloudflare.

How do I get api.example.com attached my VPS? I'll assume that I'm unwilling to pay the premium for the server to have a static IP. It's clear I have to use some DDNS, but solutions like [timothymiller/cloudflare-ddns](https://github.com/timothymiller/cloudflare-ddns) seem more heavyweight that I need in this use case.

So I created this little tool. With only 2 direct dependencies and <140 lines of python, this tool connects to Cloudflare's API and ensures our public IP is listed in an A record.

## Requirements
* Python >=3.7.
* A domain you own, managed on Cloudflare.
* A [Cloudflare API token](https://support.cloudflare.com/hc/en-us/articles/200167836-Managing-API-Tokens-and-Keys#12345680) with `Zone.DNS.Edit` permission on the relevant DNS zone.

## Preparation
1. Ensure all requirements met.
2. Install dependencies: `sudo python3 -m pip install -r requirements.txt`
  * sudo may or may not be required to install the Cloudflare API.

## Usage
Ensure arguments as listed in `update_ddns.py::update_ddns` are available when it is run.
You'll probably end up throwing whichever method you choose below into a cronjob that runs every few minutes. DNS A records this program creates have a TTL of 5 minutes, though that's easy to change in the code if necessary for your use case.

### With CLI arguments
1. Run `python3 update_ddns.py <CLOUDFLARE_TOKEN> <CLOUDFLARE_ZONE_NAME> <CLOUDFLARE_DNS_NAME>`

### With environment variables
1. Set `CLOUDFLARE_TOKEN`, `CLOUDFLARE_ZONE_NAME`, and `CLOUDFLARE_DNS_NAME` appropriately in the environment.
2. Run `python3 update_ddns.py`

### Programatically
```python
from update_ddns import update_ddns

# Get values as necessary
token = ...
zone_name = ...
dns_name = ...

update_ddns(
    token=token,
    zone_name=zone_name,
    dns_name=dns_name,
)
```

## Methods
When executed, this script follows a few steps:
* Get the runner's public IP address
* Connect to Cloudflare's API with the token and data provided
* If there exists a DNS A record matching what we want in place:
  * Leave that record alone and clean up any other A records on this dns name
* If no current DNS A records match what we want
  * Clear all A records on this dns name
  * Create a new A record associated with the runner's public IP address

## Limitations
The code as written here only inspects, adds, and removes A records. Since AAAA records aren't considered here, this does not yet support ipv6. 
