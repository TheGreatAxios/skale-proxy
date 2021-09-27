import time
import json
import filecmp
import os
import sys
import os.path
import subprocess
from os import path
from shutil import copyfile

CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"
CERT_FILE = "/data/server.crt"
KEY_FILE = "/data/server.key"
RESULTS_PATH = "/tmp/chains.json"
PROXY_FULL_HOST_NAME = os.environ.get("PROXY_FULL_HOST_NAME")

if PROXY_FULL_HOST_NAME is None:
    print("Fatal error: PROXY_FULL_HOST_NAME is not set. Exiting ...")
    exit(-2)

ENDPPOINT_PREFIX = os.environ.get("ENDPOINT_PREFIX")

if ENDPPOINT_PREFIX is None:
    print("Fatal error: ENDPOINT_PREFIX is not set. Exiting ...")
    exit(-3)


ABI_FILENAME = os.environ.get("ABI_FILENAME")

if ABI_FILENAME is None:
    print("Fatal error: ABI_FILENAME is not set. Exiting ...")
    exit(-4)

if not path.exists(CERT_FILE):
    print("Fatal error: could not find:" + CERT_FILE + " Exiting.")
    exit(-5)

if not path.exists(KEY_FILE):
    print("Fatal error: could not find:" + KEY_FILE + " Exiting.")
    exit(-6)


def parse_chains(_network: str, _path: str) -> list:
    json_file = open(_path,)
    parsed_json = json.load(json_file)

    chain_infos = list()

    for schain in parsed_json:
        name = schain["schain"][0]
        print("Schain name = ", name)
        nodes = schain["nodes"]

        list_of_http_endpoints = list()
        list_of_https_endpoints = list()
        list_of_ws_endpoints = list()
        list_of_wss_endpoints = list()
        list_of_domains = list()

        for node in nodes:
            endpoint_http = node["http_endpoint_domain"]
            print("Http endpoint: " + endpoint_http)
            list_of_http_endpoints.append(endpoint_http)
            endpoint_https = node["https_endpoint_domain"]
            print(endpoint_https)
            list_of_https_endpoints.append(endpoint_https)
            endpoint_ws = node["ws_endpoint_domain"]
            endpoint_wss = node["wss_endpoint_domain"]
            list_of_ws_endpoints.append(endpoint_ws)
            list_of_wss_endpoints.append(endpoint_wss)
            list_of_domains.append(node['domain'])

        chain_infos.append(ChainInfo(_network, name, list_of_http_endpoints,
                                     list_of_https_endpoints, list_of_ws_endpoints,
                                     list_of_wss_endpoints, list_of_domains))
    return chain_infos


class ChainInfo:
    def __init__(self, _network: str, _chain_name: str, _list_of_http_endpoints: list,
                 _list_of_https_endpoints: list, _list_of_ws_endpoints: list,
                 _list_of_wss_endpoints: list, _list_of_domains: list):
        self.network = _network
        self.chain_name = _chain_name
        self.list_of_http_endpoints = _list_of_http_endpoints
        self.list_of_https_endpoints = _list_of_https_endpoints
        self.list_of_ws_endpoints = _list_of_ws_endpoints
        self.list_of_wss_endpoints = _list_of_wss_endpoints
        self.list_of_domains = _list_of_domains


def run(_command) -> None:
    print(">" + _command)
    subprocess.check_call(_command, shell=True)


def print_global_server_config(_f, _use_ssl: bool) -> None:
    _f.write("server {\n")
    if _use_ssl:
        _f.write("	listen 443 ssl;\n")
        _f.write("	ssl_certificate " + CERT_FILE + ";\n")
        _f.write("	ssl_certificate_key " + KEY_FILE + ";\n")
        _f.write("	ssl_verify_client off;\n")
    else:
        _f.write("	listen 80;\n")
    # _f.write("	root /usr/share/nginx/www;\n")
    # _f.write("	index index.php index.html index.htm;\n")
    _f.write("	server_name " + PROXY_FULL_HOST_NAME + ";\n")

    _f.write("	location / {\n")
    _f.write("		proxy_http_version 1.1;\n")
    _f.write("		proxy_pass  http://proxy-ui:5000/;\n")
    _f.write("		proxy_set_header Upgrade $http_upgrade;\n")
    _f.write("		proxy_set_header Connection 'upgrade';\n")
    _f.write("		proxy_set_header Host $host;\n")
    _f.write("		proxy_cache_bypass $http_upgrade;\n")
    _f.write("	}\n")


def print_group_definition(_chain_info: ChainInfo, _f) -> None:
    _f.write("upstream " + _chain_info.chain_name + " {\n")
    _f.write("   ip_hash;\n")
    for endpoint in _chain_info.list_of_http_endpoints:
        _f.write("   server " + endpoint[7:] + " max_fails=1 fail_timeout=600s;\n")
    _f.write("}\n")


def print_ws_group_definition(_chain_info: ChainInfo, _f) -> None:
    _f.write("upstream ws-" + _chain_info.chain_name + " {\n")
    _f.write("   ip_hash;\n")
    for endpoint in _chain_info.list_of_ws_endpoints:
        _f.write("   server " + endpoint[5:] + " max_fails=1 fail_timeout=600s;\n")
    _f.write("}\n")


def print_storage_group_definition(_chain_info: ChainInfo, _f) -> None:
    _f.write("upstream storage-" + _chain_info.chain_name + " {\n")
    _f.write("   ip_hash;\n")
    for domain in _chain_info.list_of_domains:
        _f.write("   server " + domain + " max_fails=1 fail_timeout=600s;\n")
    _f.write("}\n")


def print_loadbalacing_config_for_chain(_chain_info: ChainInfo, _f) -> None:
    _f.write("	location /v1/" + _chain_info.chain_name + " {\n")
    _f.write("	      proxy_http_version 1.1;\n")
    _f.write("	      proxy_pass http://" + _chain_info.chain_name + "/;\n")
    _f.write("	    }\n")


def print_ws_config_for_chain(_chain_info: ChainInfo, _f) -> None:
    _f.write("	location /v1/ws/" + _chain_info.chain_name + " {\n")
    _f.write("	      proxy_http_version 1.1;\n")
    _f.write("	      proxy_set_header Upgrade $http_upgrade;\n")
    _f.write("	      proxy_set_header Connection \"upgrade\";\n")
    _f.write("	      proxy_pass http://ws-" + _chain_info.chain_name + "/;\n")
    _f.write("	    }\n")


def print_storage_proxy_for_chain(_chain_info: ChainInfo, _f) -> None:
    _f.write("	location /fs/" + _chain_info.chain_name + " {\n")
    _f.write("	      rewrite /fs/" + _chain_info.chain_name + "/(.*) /" + _chain_info.chain_name + "/$1 break;\n")
    _f.write("	      proxy_http_version 1.1;\n")
    _f.write("	      proxy_pass http://storage-" + _chain_info.chain_name + "/;\n")
    _f.write("	    }\n")


def print_config_file(_chain_infos: list) -> None:
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        for chain_info in _chain_infos:
            print_group_definition(chain_info, f)
            print_ws_group_definition(chain_info, f)
            print_storage_group_definition(chain_info, f)
        print_global_server_config(f, False)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
            print_ws_config_for_chain(chain_info, f)
            print_storage_proxy_for_chain(chain_info, f)
        f.write("}\n")
        print_global_server_config(f, True)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
            print_ws_config_for_chain(chain_info, f)
            print_storage_proxy_for_chain(chain_info, f)
        f.write("}\n")
        f.close()


def copy_config_file_if_modified() -> None:
    if (not path.exists(CONFIG_FILE)) or (not filecmp.cmp(CONFIG_FILE, TMP_CONFIG_FILE, shallow=False)):
        print("New config file. Reloading server")
        os.remove(CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        run("/usr/sbin/nginx -s reload")


def main():
    while True:
        print("Updating chain info ...")
        subprocess.check_call(["/bin/bash", "-c", "rm -f /tmp/*"])
        subprocess.check_call(["/bin/bash", "-c",
                              "cp /etc/abi.json /tmp/abi.json"])
        subprocess.check_call(["python3", "/etc/endpoints.py"])
        subprocess.check_call(["/bin/bash", "-c", "mkdir -p /usr/share/nginx/www"])
        subprocess.check_call(["/bin/bash", "-c", "cp -f /tmp/chains.json /usr/share/nginx/www/chains.json"])
        subprocess.check_call(["/bin/bash", "-c", "cp -f /etc/VERSION /usr/share/nginx/www/VERSION.txt"])

        if not os.path.exists(RESULTS_PATH):
            print("Fatal error: Chains file does not exist. Exiting ...")
            exit(-4)

        print("Generating config file ...")

        chain_infos = parse_chains(ENDPPOINT_PREFIX, RESULTS_PATH)

        print("Checking Config file ")
        print_config_file(chain_infos)
        copy_config_file_if_modified()
        print("monitor loop iteration")
        sys.stdout.flush()
        time.sleep(6000)


# run main
main()
