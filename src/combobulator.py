import argparse
import os
from dotenv import load_dotenv

# internal module imports
from metapackage import MetaPackage as metapkg
import registry.npm as npm
import registry.maven as maven
import registry.pypi as pypi
from analysis import heuristics as heur

# export
import csv
import sys
import logging  # Added import

from constants import ExitCodes, PackageManagers, Constants  # Import Constants including LOG_FORMAT

SUPPORTED_PACKAGES = Constants.SUPPORTED_PACKAGES

def init_args():
    # WARNING: don't populate this instance with a hard-coded value
    # it is merely for initializing a string variable.
    GITHUB_TOKEN=""

def parse_args():
    parser = argparse.ArgumentParser(
        prog="combobulator.py",
        description="Dependency Combobulator - Dependency Confusion Checker",
        epilog='Apiiro <Heart> Community',
        add_help=True)
    parser.add_argument("-t", "--type",
                        dest="package_type",
                        help="Package Manager Type, i.e: npm, PyPI, maven",
                        action="store",type=str, choices=SUPPORTED_PACKAGES,
                        required=True )
    # https://docs.python.org/3/library/argparse.html#mutual-exclusion
    # input_group as a mutually exclusive arg group: 
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-l", "--load_list",
                        dest="LIST_FROM_FILE",
                        help="Load list of dependencies from a file",
                        action="append",type=str,
                        default=[] )
    input_group.add_argument("-d", "--directory",
                    dest="FROM_SRC",
                    help="Extract dependencies from local source repository",
                    action="append",
                    type=str)
    input_group.add_argument("-p", "--package",
                            dest="SINGLE",
                            help="Name a single package.",
                            action="append",type=str )
    output_group = parser.add_mutually_exclusive_group(required=False)
    output_group.add_argument("-c", "--csv",
        dest="CSV",
        help="Export packages properties onto CSV file",
                    action="store", type=str)
    # support variables
    parser.add_argument("-gh", "--github",
                    dest="GITHUB_TOKEN",
                    help="GitHub Access Token (Overrides .env file setting)",
                    action="store", type=str )
    parser.add_argument("-a", "--analysis",
        dest="LEVEL",
        help="Required analysis level - compare (comp), heuristics (heur) (default: compare)",
                    action="store", default="compare", type=str,
                    choices = Constants.LEVELS)
    # Added new arguments for logging
    parser.add_argument("--loglevel",
                        dest="LOG_LEVEL",
                        help="Set the logging level",
                        action="store",
                        type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO')
    parser.add_argument("--logfile",
                        dest="LOG_FILE",
                        help="Log output file",
                        action="store",
                        type=str)
    parser.add_argument("-r", "--recursive",
                        dest="RECURSIVE",
                        help="Recursively scan directories when scanning from source.",
                        action="store_true")
    return parser.parse_args()


def load_env():
    """
    .env file example:

    # GitHub Token
    GITHUB_TOKEN=ghp_123456789012345678901234567890123456
    """

    load_dotenv('.env')
    GITHUB_TOKEN=os.getenv('GITHUB_TOKEN')


def load_pkgs_file(pkgs):
    try:
        lister = []
        lines = open(pkgs).readlines()
        for i in lines:
            lister.append(i.strip())
        return lister
    except:
        logging.error("Cannot process input list/file")
        raise TypeError

def scan_source(pkgtype, dir, recursive=False):
    if pkgtype == PackageManagers.NPM.value:
        return npm.scan_source(dir, recursive)
    elif pkgtype == PackageManagers.MAVEN.value:
        return maven.scan_source(dir, recursive)
    elif pkgtype == PackageManagers.PYPI.value:
        return pypi.scan_source(dir, recursive)
    else:
        logging.error("Selected package type doesn't support import scan.")
        sys.exit(ExitCodes.FILE_ERROR.value)

def check_against(check_type, check_list):
    if check_type == PackageManagers.NPM.value:
        response = npm.recv_pkg_info(check_list)
        return response
    elif check_type == PackageManagers.MAVEN.value:
        response = maven.recv_pkg_info(check_list)
        return response
    elif check_type == PackageManagers.PYPI.value:
        response = pypi.recv_pkg_info(check_list)

def export_csv(instances, path):
    #filer = open(path, 'w', newline='')
    headers = ["Package Name","Package Type", "Exists on External",
            "Org/Group ID","Score","Version Count","Timestamp"]
    rows = [headers]
    for x in instances:
        rows.append(x.listall())
    try:
        with open(path, 'w', newline='') as file:
            export = csv.writer(file)
            export.writerows(rows)
        logging.info("CSV file has been successfully exported at: %s", path)
    except:
        logging.error("CSV file couldn't be written to disk.")
        sys.exit(1)
        
        
    
def main():
    # envs to be consumed: GITHUB_TOKEN
    init_args()
    load_env()

    # the most important part of any program starts here

    args = parse_args()

    # Configure logging
    log_level = getattr(logging, args.LOG_LEVEL.upper(), logging.INFO)
    if '-h' in sys.argv or '--help' in sys.argv:
        # Ensure help output is always at INFO level
        logging.basicConfig(level=logging.INFO, format=Constants.LOG_FORMAT)
    else:
        if args.LOG_FILE:
            logging.basicConfig(filename=args.LOG_FILE, level=log_level,
                                format=Constants.LOG_FORMAT)  # Used LOG_FORMAT constant
        else:
            logging.basicConfig(level=log_level, format=Constants.LOG_FORMAT)  # Used LOG_FORMAT constant

    logging.info("Arguments parsed.")
    GITHUB_TOKEN = args.GITHUB_TOKEN

    # Logging the ASCII art banner
    logging.info(r"""
  ____  _____ ____  _____ _   _ ____  _____ _   _  ______   __
 |  _ \| ____|  _ \| ____| \ | |  _ \| ____| \ | |/ ___\ \ / /
 | | | |  _| | |_) |  _| |  \| | | | |  _| |  \| | |    \ V / 
 | |_| | |___|  __/| |___| |\  | |_| | |___| |\  | |___  | |  
 |____/|_____|_|   |_____|_| \_|____/|_____|_| \_|\____| |_|  

   ____ ____  __  __ ____   ____  ____  _   _ _        _  _____ ____  ____  
  / ___/ /\ \|  \/  | __ ) / /\ \| __ )| | | | |      / \|_   _/ /\ \|  _ \ 
 | |  / /  \ \ |\/| |  _ \/ /  \ \  _ \| | | | |     / _ \ | |/ /  \ \ |_) |
 | |__\ \  / / |  | | |_) \ \  / / |_) | |_| | |___ / ___ \| |\ \  / /  _ < 
  \____\_\/_/|_|  |_|____/ \_\/_/|____/ \___/|_____/_/   \_\_| \_\/_/|_| \_\
""")

    # are you amazed yet?

    # SCAN & FLAG ARGS
    args = parse_args()
    logging.info("Arguments parsed.")
    GITHUB_TOKEN = args.GITHUB_TOKEN

    # Check if recursive option is used without directory
    if args.RECURSIVE and not args.FROM_SRC:
        logging.warning("Recursive option is only applicable to source scans.")

    #IMPORT
    if args.LIST_FROM_FILE:
        pkglist = load_pkgs_file(args.LIST_FROM_FILE[0])
    elif args.FROM_SRC:
        pkglist = scan_source(args.package_type, args.FROM_SRC[0], recursive=args.RECURSIVE)
    elif args.SINGLE:
        pkglist = []
        pkglist.append(args.SINGLE[0])
    logging.info("Package list imported: %s", str(pkglist))
    
    if args.package_type == PackageManagers.NPM.value:
        for x in pkglist:
            metapkg(x, args.package_type)
    elif args.package_type == PackageManagers.MAVEN.value:
        for x in pkglist: # format orgId:packageId
            metapkg(x.split(':')[1], args.package_type, x.split(':')[0])
    elif args.package_type == PackageManagers.PYPI.value:
        for x in pkglist:
            metapkg(x, args.package_type)

    # QUERY & POPULATE
    check_against(args.package_type, metapkg.instances)

    # ANALYZE
    if args.LEVEL == Constants.LEVELS[0] or args.LEVEL == Constants.LEVELS[1]:
        heur.combobulate_min(metapkg.instances)
    elif args.LEVEL == Constants.LEVELS[2] or args.LEVEL == Constants.LEVELS[3]:
        heur.combobulate_heur(metapkg.instances)

    # OUTPUT
    if args.CSV:
        export_csv(metapkg.instances, args.CSV)

if __name__ == "__main__":
    main()