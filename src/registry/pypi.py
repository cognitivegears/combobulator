import json
import sys
import os
from datetime import datetime as dt
import logging  # Added import
import requests
import requirements
from constants import ExitCodes, Constants

def recv_pkg_info(pkgs, url=Constants.REGISTRY_URL_PYPI):
    logging.info("PyPI registry engaged.")
    payload = {}
    for x in pkgs:
        fullurl = url + x.pkg_name + '/json'
        logging.debug(fullurl)
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        try:
            res = requests.get(fullurl, params=payload, headers=headers)
        except:
            logging.error("Connection error.")
            exit(ExitCodes.CONNECTION_ERROR.value)
        if res.status_code == 404:
            # Package not found
            x.exists = False
            continue
        if res.status_code != 200:
            logging.error("Connection error, status code: %s", res.status_code)
            exit(ExitCodes.CONNECTION_ERROR.value)
        try:
            j = json.loads(res.text)
        except:
            x.exists = False
            return
        if j['info']:
            x.exists = True
            latest = j['info']['version']
            for version in j['releases']:
                if version == latest:
                    timex = j['releases'][version][0]['upload_time_iso_8601']
                    fmtx = '%Y-%m-%dT%H:%M:%S.%fZ'
                    unixtime = int(dt.timestamp(dt.strptime(timex, fmtx)) * 1000)
                    x.timestamp = unixtime
            x.version_count = len(j['releases'])
        else:
            x.exists = False

def scan_source(dir_name, recursive=False):
    try:
        logging.info("PyPI scanner engaged.")
        req_files = []
        if recursive:
            for root, _, files in os.walk(dir_name):
                if Constants.REQUIREMENTS_FILE in files:
                    req_files.append(os.path.join(root, Constants.REQUIREMENTS_FILE))
        else:
            path = os.path.join(dir_name, Constants.REQUIREMENTS_FILE)
            if os.path.isfile(path):
                req_files.append(path)
            else:
                raise FileNotFoundError("requirements.txt not found.")

        all_requirements = []
        for path in req_files:
            with open(path, "r") as file:
                body = file.read()
            reqs = requirements.parse(body)
            all_requirements.extend([x.name for x in reqs])
        return list(set(all_requirements))
    except (FileNotFoundError, IOError) as e:
        logging.error("Couldn't import from given path '%s', error: %s", path, e)
        sys.exit(ExitCodes.FILE_ERROR.value)
