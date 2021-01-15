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
    STRING = 3      # value contains multiple words enclosed in double quotes
    BOOL = 4
    ENUM = 5
    IPADDR = 6
    IPNET = 7
    IPSUBNET = 8
    ROUTE = 9       # specific for 'route' config values


class Keyword():
    def __init__(self, name, par_len = 0, par_types = [], par_values = []):
        self.name = name
        self.len = par_len       # Number of mandatory arguments
        self.types = par_types   # Array with argument types, may contain optional arguments
        self.vals = par_values   # Array with allowed values for each argument


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
    keywords = { "client": Keyword("client"),
                 "mode": Keyword("mode", 1, [ValType.ENUM], [["p2p", "server"]]),
                 "server": Keyword("server", 2, [ValType.IPNET, ValType.IPSUBNET, ValType.ENUM], [[], [], ['nopool']]),
                 "local": Keyword("local", 1, [ValType.IPADDR]),
                 "port": Keyword("port", 1, [ValType.INT]),
                 "proto": Keyword("proto", 1, [ValType.ENUM], [["udp", "tcp"]]),
                 "dev": Keyword("dev", 1, [ValType.ASCII]),
                 "ca": Keyword("ca", 1, [ValType.ASCII]),
                 "cert": Keyword("cert", 1, [ValType.ASCII]),
                 "key": Keyword("key", 1, [ValType.ASCII]),
                 "pkcs12": Keyword("pkcs12", 1, [ValType.ASCII]),
                 "dh": Keyword("dh", 1, [ValType.ASCII]),
                 "tls-server": Keyword("tls-server"),
                 "tls-client": Keyword("tls-client"),
                 "tls-version-min": Keyword("tls-version-min", 1, [ValType.ENUM], [["1.0", "1.1", "1.2", "1.3"]]),
                 "tls-version-max": Keyword("tls-version-max", 1, [ValType.ENUM], [["1.0", "1.1", "1.2", "1.3"]]),
                 "ifconfig-pool-persist": Keyword("ifconfig-pool-persist", 1, [ValType.ASCII]),
                 "push": Keyword("push", 1, [ValType.STRING]),
                 "client-config-dir": Keyword("client-config-dir", 1, [ValType.ASCII]),
                 "route": Keyword("route", -1, [ValType.ROUTE]),
                 "client-to-client": Keyword("client-to-client"),
                 "keepalive": Keyword("keepalive", 2, [ValType.INT, ValType.INT]),
                 "tls-auth": Keyword("tls-auth", 1, [ValType.ASCII, ValType.INT], [[], [0, 1]]),
                 "tls-crypt": Keyword("tls-crypt", 1, [ValType.ASCII]),
                 "cipher": Keyword("cipher", 1, [ValType.ASCII]),
                 "compress": Keyword("compress", 1, [ValType.ENUM], [["lzo", "lz4", "lz4-v2"]]),
                 "comp-lzo": Keyword("comp-lzo"),
                 "max-clients": Keyword("max-clients", 1, [ValType.INT]),
                 "user": Keyword("user", 1, [ValType.ASCII]),
                 "group": Keyword("group", 1, [ValType.ASCII]),
                 "persist-key": Keyword("persist-key"),
                 "persist-tun": Keyword("persist-tun"),
                 "status": Keyword("status", 1, [ValType.ASCII]),
                 "log": Keyword("log", 1, [ValType.ASCII]),
                 "log-append": Keyword("log-append", 1, [ValType.ASCII]),
                 "verb": Keyword("verb", 1, [ValType.INT]),
                 "mute": Keyword("mute", 1, [ValType.INT]),
                 "explicit-exit-notify": Keyword("explicit-exit-notify", 1, [ValType.ENUM], [["1", "2"]])
                 }

    return keywords


def check_line(line:str, config_keywords:list) -> None:
    """Syntax checking single configuration line"""
    words = line.split()
    keyword = words[0]

    # Check if keyword is valid
    if keyword not in config_keywords:
        raise(BaseException(f"ERROR: Unknown keyword '{keyword}'"))

    # Check number of mandatory arguments
    if len(words) <= config_keywords[keyword].len:
        raise(BaseException(f"ERROR: Invalid number of arguments for keyword '{keyword}'"))

    val_types = config_keywords[keyword].types

    # Check type for every parameter value
    for i in range(1, len(words)):
        if len(val_types) == 0:
            raise(BaseException(f"ERROR: Keyword '{keyword}' takes no parameters"))
        if i > len(val_types):
            raise(BaseException(f"ERROR: Invalid optional argument for keyword '{keyword}'"))

        val_type = val_types[i-1]
        word = words[i]

        if not words[i].isprintable():
            raise(BaseException(f"ERROR: Invalid characters in value for keyword '{keyword}'"))

        if val_type == ValType.STRING:
            try:
                val_string = line.split(maxsplit=1)[1]
                if not val_string.startswith('"') or not val_string.endswith('"')\
                        or len(val_string) < 3 or val_string.find('"', 1, -1) >= 0:
                    raise(BaseException(f"ERROR: Invalid string format for keyword '{keyword}'"))
                return
            except IndexError:
                raise(BaseException(f"ERROR: Missing string argument for keyword '{keyword}'"))

        if val_type == ValType.ROUTE:
            ###TODO###
            return

        if val_type == ValType.IPNET:
            try:
                ipv4net(f"{words[i]}/{words[i+1]}")
                continue
            except IndexError:
                raise(BaseException(f"ERROR: Missing IP network address part for keyword '{keyword}'"))
            except ValueError:
                raise(BaseException(f"ERROR: Invalid IP network address for keyword '{keyword}'"))

        if val_type == ValType.INT:
            if not word.isnumeric():
                raise(BaseException(f"ERROR: Invalid integer value '{word}' for keyword '{keyword}'"))
        elif val_type == ValType.ASCII:
            try:
                word.encode("ascii")
            except UnicodeEncodeError:
                raise(BaseException(f"ERROR: Invalid ascii value '{word}' for keyword '{keyword}'"))
        elif val_type == ValType.ENUM:
            if len(config_keywords[keyword].vals) == 0:
                raise(BaseException(f"ERROR: No enumeration values defined for keyword '{keyword}'"))
            if word not in config_keywords[keyword].vals[i-1]:
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
        exit(1)
    except:
        print("Unknown error")
        exit(2)


if __name__ == '__main__':
    main()