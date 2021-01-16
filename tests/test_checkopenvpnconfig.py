#!/usr/bin/env python3
import checkopenvpnconfig as coc
import unittest


class ConfigTest(unittest.TestCase):
    config_keywords = coc.get_config_keywords();

    def test_missing_keyword(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Unknown keyword "):
            coc.check_line("servers 10.0.0.0 255.0.0.0", ConfigTest.config_keywords)

    def test_argument_count(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid number of arguments "):
            coc.check_line("server 10.0.0.0/8", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid number of arguments "):
            coc.check_line("keepalive 10", ConfigTest.config_keywords)

    def test_argument_type_int(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid integer value "):
            coc.check_line("keepalive 1O 20", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid integer value "):
            coc.check_line("keepalive 10 -20", ConfigTest.config_keywords)

    def test_argument_type_ascii(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid ascii value "):
            coc.check_line("key server.keü", ConfigTest.config_keywords)

    def test_argument_type_enum(self):
        coc.check_line("resolv-retry 0", ConfigTest.config_keywords)
        coc.check_line("resolv-retry 10", ConfigTest.config_keywords)
        coc.check_line("resolv-retry infinite", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid number of arguments "):
            coc.check_line("resolv-retry   ", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid enumeration value "):
            coc.check_line("proto ucp", ConfigTest.config_keywords)

    def test_argument_type_ipv4(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid IP address "):
            coc.check_line("local 10.0.0.O", ConfigTest.config_keywords)

    def test_argument_type_ipv4net(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid IP network address "):
            coc.check_line("server 10.10.0.0 255.0.0.0", ConfigTest.config_keywords)

    def test_argument_type_string(self):
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid string format "):
            coc.check_line("push route 10.10.0.0 255.0.0.0", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid string format "):
            coc.check_line("push \"route 10.10.0.0 255.0.0.0", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid string format "):
            coc.check_line("push route \"10.10.0.0 255.0.0.0\"", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid string format "):
            coc.check_line("push \"route \"10.10.0.0 255.0.0.0\"", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid number of arguments "):
            coc.check_line("push", ConfigTest.config_keywords)

    def test_optional_argument(self):
        coc.check_line("server 10.0.0.0 255.0.0.0", ConfigTest.config_keywords)
        coc.check_line("server 10.0.0.0 255.0.0.0 nopool", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid enumeration value "):
            coc.check_line("server 10.0.0.0 255.0.0.0 nopoll", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid optional argument "):
            coc.check_line("server 10.0.0.0 255.0.0.0 nopool invalid", ConfigTest.config_keywords)

    def test_multiple_optional_arguments(self):
        coc.check_line("remote 10.10.10.1", ConfigTest.config_keywords)
        coc.check_line("remote 10.10.10.1 1194", ConfigTest.config_keywords)
        coc.check_line("remote 10.10.10.1 1194 udp", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid integer value "):
            coc.check_line("remote 10.10.10.1 udp 1194", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid enumeration value "):
            coc.check_line("remote 10.10.10.1 1194 ucp", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Invalid optional argument "):
            coc.check_line("remote 10.10.10.1 1194 udp invalid", ConfigTest.config_keywords)

    def test_noarguments(self):
        coc.check_line("client", ConfigTest.config_keywords)
        with self.assertRaisesRegex(BaseException, "ERROR: Keyword 'client' takes no arguments"):
            coc.check_line("client 10.0.0.0", ConfigTest.config_keywords)


if __name__ == '__main__':
    unittest.main()