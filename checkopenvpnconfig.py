#!/usr/bin/env python3

import argparse
import re
from enum import Enum
from ipaddress import IPv4Address as ipv4, IPv4Network as ipv4net, AddressValueError


class ValType(Enum):
    """Enumeration for all possible value types"""
    NONE = 0
    INT = 1
    ASCII = 2
    BOOL = 3
    ENUM = 4
    IPADDR = 5
    IPNET = 6


class Keyword():
    def __init__(self, name, par_len, par_type = ValType.NONE, par_values = None):
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
    keywords = { "local": Keyword("local", 2, ValType.IPADDR),
                 "port": Keyword("port", 2, ValType.INT),
                 "proto": Keyword("proto", 2, ValType.ENUM, ["udp", "tcp"]),
                 "dev": Keyword("dev", 2, ValType.ASCII),
                 "ca": Keyword("ca", 2, ValType.ASCII),
                 "cert": Keyword("cert", 2, ValType.ASCII),
                 "key": Keyword("key", 2, ValType.ASCII),
                 "dh": Keyword("dh", 2, ValType.ASCII),
                 "server": Keyword("server", 3, ValType.IPNET),
                 "ifconfig-pool-persist": Keyword("ifconfig-pool-persist", 2, ValType.ASCII),
                 "keepalive": Keyword("keepalive", 3, ValType.INT),
                 "tls-auth": Keyword("tls-auth", 3, ValType.ASCII),
                 "cipher": Keyword("cipher", 2, ValType.ASCII),
                 "persist-key": Keyword("persist-key", 1),
                 "persist-tun": Keyword("persist-tun", 1),
                 "status": Keyword("status", 2, ValType.ASCII),
                 "verb": Keyword("verb", 2, ValType.INT),
                 "explicit-exit-notify": Keyword("explicit-exit-notify", 2, ValType.ENUM, ["1", "2"]),
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

    # Check if all values have correct type
    val_type = config_keywords[keyword].type

    if val_type == ValType.IPNET:
        try:
            ipv4net(f"{words[1]}/{words[2]}")
        except IndexError:
            raise(BaseException(f"ERROR: Missing IP network address part for keyword '{keyword}'"))
        except ValueError:
            raise(BaseException(f"ERROR: Invalid IP network address for keyword '{keyword}'"))

    for word in words[1:]:
        if not word.isprintable():
            raise(BaseException(f"ERROR: Invalid characters in value for keyword '{keyword}'"))
        if val_type == ValType.INT:
            if not word.isnumeric():
                raise(BaseException(f"ERROR: Invalid integer value '{word}' for keyword '{keyword}'"))
        elif val_type == ValType.ASCII:
            try:
                word.encode("ascii")
            except UnicodeEncodeError:
                raise(BaseException(f"ERROR: Invalid ascii value '{word}' for keyword '{keyword}'"))
        elif val_type == ValType.ENUM:
            if config_keywords[keyword].vals is None:
                raise(BaseException(f"ERROR: No enumeration values defined for keyword '{keyword}'"))
            if word not in config_keywords[keyword].vals:
                raise(BaseException(f"ERROR: Invalid enumeration value '{word}' for keyword '{keyword}'"))
        elif val_type == ValType.IPADDR:
            try:
                ip_address = ipv4(word)
            except AddressValueError:
                raise(BaseException(f"ERROR: Invalid IP address '{word}' for keyword '{keyword}'"))


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