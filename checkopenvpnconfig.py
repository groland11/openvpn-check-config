#!/usr/bin/env python3

import argparse
import re
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, AddressValueError


class ArgTye(Enum):
    """Enumeration for all possible argument types"""
    NONE = 0
    INT = 1
    ASCII = 2
    STRING = 3      # argument contains multiple words enclosed in double quotes
    BOOL = 4
    ENUM = 5
    IPADDR = 6
    IPNET = 7
    IPSUBNET = 8
    ROUTE = 9       # specific for 'route' keyword


class Keyword:
    def __init__(self, name, par_len=0, par_types=[], par_values=[]):
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


def get_config_keywords() -> dict:
    """Retrieve list of valid configuration keywords"""
    keywords = { "client": Keyword("client"),
                 "remote": Keyword("remmote", 1, [ArgTye.IPADDR, ArgTye.INT, ArgTye.ENUM], [[], [], ["udp", "tcp"]]),
                 "resolv-retry": Keyword("resolv-retry", 1, [ArgTye.ENUM], [["infinite", "\d+"]]),
                 "nobind": Keyword("nobind"),
                 "mode": Keyword("mode", 1, [ArgTye.ENUM], [["p2p", "server"]]),
                 "server": Keyword("server", 2, [ArgTye.IPNET, ArgTye.IPSUBNET, ArgTye.ENUM], [[], [], ["nopool"]]),
                 "local": Keyword("local", 1, [ArgTye.IPADDR]),
                 "port": Keyword("port", 1, [ArgTye.INT]),
                 "proto": Keyword("proto", 1, [ArgTye.ENUM], [["udp", "tcp"]]),
                 "dev": Keyword("dev", 1, [ArgTye.ASCII]),
                 "ca": Keyword("ca", 1, [ArgTye.ASCII]),
                 "cert": Keyword("cert", 1, [ArgTye.ASCII]),
                 "key": Keyword("key", 1, [ArgTye.ASCII]),
                 "pkcs12": Keyword("pkcs12", 1, [ArgTye.ASCII]),
                 "dh": Keyword("dh", 1, [ArgTye.ASCII]),
                 "tls-server": Keyword("tls-server"),
                 "tls-client": Keyword("tls-client"),
                 "tls-version-min": Keyword("tls-version-min", 1, [ArgTye.ENUM], [["1.0", "1.1", "1.2", "1.3"]]),
                 "tls-version-max": Keyword("tls-version-max", 1, [ArgTye.ENUM], [["1.0", "1.1", "1.2", "1.3"]]),
                 "remote-cert-tls": Keyword("remote-cert-tls", 1, [ArgTye.ENUM], [["server", "client"]]),
                 "ifconfig-pool-persist": Keyword("ifconfig-pool-persist", 1, [ArgTye.ASCII]),
                 "ifconfig": Keyword("ifconfig", 2, [ArgTye.IPADDR, ArgTye.IPADDR]),
                 "push": Keyword("push", 1, [ArgTye.STRING]),
                 "client-config-dir": Keyword("client-config-dir", 1, [ArgTye.ASCII]),
                 "route": Keyword("route", -1, [ArgTye.ROUTE]),
                 "route-metric": Keyword("route-metric", 1, [ArgTye.INT]),
                 "client-to-client": Keyword("client-to-client"),
                 "keepalive": Keyword("keepalive", 2, [ArgTye.INT, ArgTye.INT]),
                 "tls-auth": Keyword("tls-auth", 1, [ArgTye.ASCII, ArgTye.ENUM], [[], ["0", "1"]]),
                 "tls-crypt": Keyword("tls-crypt", 1, [ArgTye.ASCII]),
                 "cipher": Keyword("cipher", 1, [ArgTye.ASCII]),
                 "compress": Keyword("compress", 1, [ArgTye.ENUM], [["lzo", "lz4", "lz4-v2"]]),
                 "comp-lzo": Keyword("comp-lzo"),
                 "mtu-test": Keyword("mtutest"),
                 "tun-mtu": Keyword("tun-mtu", 1, [ArgTye.INT]),
                 "link-mtu": Keyword("link-mtu", 1, [ArgTye.INT]),
                 "fregment": Keyword("fragment", 1, [ArgTye.INT]),
                 "mss-fix": Keyword("mss-fix", 1, [ArgTye.INT]),
                 "sndbuf": Keyword("sndbuf", 1, [ArgTye.INT]),
                 "rcvbuf": Keyword("rcvbuf", 1, [ArgTye.INT]),
                 "max-clients": Keyword("max-clients", 1, [ArgTye.INT]),
                 "user": Keyword("user", 1, [ArgTye.ASCII]),
                 "group": Keyword("group", 1, [ArgTye.ASCII]),
                 "persist-key": Keyword("persist-key"),
                 "persist-tun": Keyword("persist-tun"),
                 "status": Keyword("status", 1, [ArgTye.ASCII]),
                 "log": Keyword("log", 1, [ArgTye.ASCII]),
                 "log-append": Keyword("log-append", 1, [ArgTye.ASCII]),
                 "verb": Keyword("verb", 1, [ArgTye.INT]),
                 "mute": Keyword("mute", 1, [ArgTye.INT]),
                 "mute-replay-warnings": Keyword("mute-replay-warnings"),
                 "replay-window": Keyword("replay-window", 1, [ArgTye.INT, ArgTye.INT]),
                 "explicit-exit-notify": Keyword("explicit-exit-notify", 1, [ArgTye.ENUM], [["1", "2"]])
                 }

    return keywords


def check_line(line: str, config_keywords: dict) -> int:
    """Syntax checking single configuration line"""
    words = line.split()
    keyword = words[0]

    # Check if keyword is valid
    if keyword not in config_keywords:
        raise(BaseException(f"ERROR: Unknown keyword '{keyword}'"))

    # Check number of mandatory arguments
    if len(words) <= config_keywords[keyword].len:
        raise(BaseException(f"ERROR: Invalid number of arguments for keyword '{keyword}'"))

    # Array with type for each argument
    arg_types = config_keywords[keyword].types

    # Check type for every argument value
    for i, word in enumerate(words[1:], start=1):
        if not arg_types:
            raise(BaseException(f"ERROR: Keyword '{keyword}' takes no arguments"))
        if i > len(arg_types):
            raise(BaseException(f"ERROR: Invalid optional argument for keyword '{keyword}'"))

        # Current argument type
        arg_type = arg_types[i-1]

        # Unprintable characters may also be ASCII characters
        if not word.isprintable():
            raise(BaseException(f"ERROR: Invalid characters in value for keyword '{keyword}'"))

        if arg_type == ArgTye.STRING:
            try:
                val_string = line.split(maxsplit=1)[1]
                if not val_string.startswith('"') or not val_string.endswith('"')\
                        or len(val_string) < 3 or val_string.find('"', 1, -1) >= 0:
                    raise(BaseException(f"ERROR: Invalid string format for keyword '{keyword}'"))
                return 1
            except IndexError:
                raise(BaseException(f"ERROR: Missing string argument for keyword '{keyword}'"))
        elif arg_type == ArgTye.ROUTE:
            # TODO
            return 0
        elif arg_type == ArgTye.IPNET:
            try:
                IPv4Network(f"{words[i]}/{words[i+1]}")
            except IndexError:
                raise(BaseException(f"ERROR: Missing IP network address part for keyword '{keyword}'"))
            except ValueError:
                raise(BaseException(f"ERROR: Invalid IP network address for keyword '{keyword}'"))
        elif arg_type == ArgTye.INT:
            if not word.isnumeric():
                raise(BaseException(f"ERROR: Invalid integer value '{word}' for keyword '{keyword}'"))
        elif arg_type == ArgTye.ASCII:
            try:
                word.encode("ascii")
            except UnicodeEncodeError:
                raise(BaseException(f"ERROR: Invalid ascii value '{word}' for keyword '{keyword}'"))
        elif arg_type == ArgTye.ENUM:
            if not config_keywords[keyword].vals:
                raise(BaseException(f"ERROR: No enumeration values defined for keyword '{keyword}'"))
            for val_enum in config_keywords[keyword].vals[i-1]:
                regex = re.compile("^" + val_enum + "$")
                if regex.match(word):
                    break
            else:
                raise(BaseException(f"ERROR: Invalid enumeration value '{word}' for keyword '{keyword}'"))
        elif arg_type == ArgTye.IPADDR:
            try:
                ip_address = IPv4Address(word)
            except AddressValueError:
                raise(BaseException(f"ERROR: Invalid IP address '{word}' for keyword '{keyword}'"))

    return 0


def check_config(config_file: str, config_keywords: dict) -> tuple:
    """Checking OpenVPN configuration file for syntax errors"""
    ret = 1
    output = []

    with open(config_file) as file:
        for linenr, line in enumerate(file, start=1):
            # Skip empty lines
            if re.match(r"^\s*$", line):
                continue

            # Skip comments
            if re.match(r"^\s*[#;]+", line):
                continue

            # Remove comments at end of line
            pos = line.find("#")
            if pos > 0:
                line = line[:pos]

            # Check syntax for each line
            try:
                ret = check_line(line.strip(), config_keywords)
            except BaseException as e:
                output.append(f"{linenr:>4} " + e.__str__())
                ret = 1
                continue

            output.append(f"{linenr:>4} OK: {line.strip()}")

        return ret, output


def main():
    """Main program flow"""
    ret: int = 1
    errcount: int = 0
    args = parseargs()
    config_keywords = get_config_keywords()

    try:
        output: list
        ret, output = check_config(args.config, config_keywords)

        for line in output:
            if line.find("ERROR") >= 0:
                print(line)
                errcount += 1
            elif args.debug:
                print(line)

        if args.verbose:
            print(f"Stats: {len(output)} line(s) with {errcount} error(s)")
    except BaseException as e:
        print(e)
        exit(2)

    exit(ret)


if __name__ == '__main__':
    main()
