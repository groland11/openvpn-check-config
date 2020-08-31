#!/usr/bin/env python3

import argparse
import re


class Keyword():
    def __init__(self, name, par_len, par_type = None, par_values = None):
        self.name = name
        self.len = par_len
        self.type = par_type
        self.vals = par_values


def parseargs():
    """Process command line arguments"""
    parser = argparse.ArgumentParser(description="Check OpenVPN configuration file")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="generate additional debug information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("config", type=str,
                        help="configuration file to be checked")
    parser.add_argument("-V", "--version", action="version", version="1.0.0")
    return parser.parse_args()


def get_config_keywords():
    """Retrieve list of valid configuration keywords"""
    keywords = { "port": Keyword("port", 2),
                 "proto": Keyword("proto", 2),
                 "dev": Keyword("dev", 2),
                 "ca": Keyword("ca", 2),
                 "cert": Keyword("cert", 2),
                 "key": Keyword("key", 2),
                 "dh": Keyword("dh", 2),
                 "server": Keyword("server", 3),
                 "ifconfig-pool-persist": Keyword("ifconfig-pool-persist", 2),
                 "keepalive": Keyword("keepalive", 3),
                 "tls-auth": Keyword("tls-auth", 3),
                 "cipher": Keyword("cipher", 2),
                 "persist-key": Keyword("persist-key", 1),
                 "persist-tun": Keyword("persist-tun", 1),
                 "status": Keyword("status", 2),
                 "verb": Keyword("verb", 2),
                 "explicit-exit-notify": Keyword("explicit-exit-notify", 2),
                 }

    return keywords


def check_line(line:str, config_keywords:list) -> None:
    """Syntax checking single configuration line"""
    words = line.split()
    keyword = words[0]

    # Check if keyword is valid
    if keyword not in config_keywords:
        raise(BaseException(f"ERROR: Unknown keyword '{keyword}'"))

    # Check number of words in line
    if len(words) != config_keywords[keyword].len:
        raise(BaseException(f"ERROR: Invalid number of arguments for keyword '{keyword}'"))


def check_config(config_file:str, config_keywords:list) -> None:
    """Checking OpenVPN configuration file for syntax errors"""
    with open(config_file) as file:
        linenr = 0
        for line in file:
            linenr += 1

            # Skip empty lines
            if re.match(r"^\s*$", line): continue
            # Skip comments
            if re.match(r"^\s*(#|;)+", line): continue
            # Remove comments at end of line
            pos = line.find("#")
            if pos > 0:
                line = line[:pos]

            # Check syntax for each line
            try:
                check_line(line.strip(), config_keywords)
            except BaseException as e:
                raise(BaseException(f"{linenr:>4} " + e.__str__()))

            print(f"{linenr:>4} OK:", line.strip())


def main():
    """Main program flow"""
    args = parseargs()
    config_keywords = get_config_keywords()

    try:
        check_config(args.config, config_keywords)
    except BaseException as e:
        print(e)
    except:
        print("Unknown error")


if __name__ == '__main__':
    main()