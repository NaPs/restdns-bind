import dns.name
import dns.zone
import dns.rdtypes.ANY.SOA
import dns.rdtypes.ANY.MX
import dns.rdtypes.ANY.NS
import dns.rdtypes.ANY.CNAME
import dns.rdtypes.ANY.TXT
import dns.rdtypes.ANY.HINFO
import dns.rdtypes.ANY.PTR
import dns.rdtypes.IN.A
import dns.rdtypes.IN.AAAA
import dns.rdtypes.IN.SRV

from dns.rdataclass import IN
from dns.rdatatype import SOA, A, AAAA, NS, CNAME, SRV, TXT, MX, HINFO, PTR


class RecordFactory(object):

    def __init__(self, origin):
        self.origin = origin

    def create_record(self, record_type, params):
        """ Create a dns-python record according to the passed type.
        """

        func_create = getattr(self, 'create_%s' % record_type.lower())
        if func_create is None:
            raise RuntimeError('Unknown record type')
        return func_create(**params)

    def create_soa(self, rname, serial, refresh, retry, expire, minimum):
        return dns.rdtypes.ANY.SOA.SOA(IN,
                                       SOA,
                                       self.origin,
                                       dns.name.from_text(rname, self.origin),
                                       serial,
                                       refresh,
                                       retry,
                                       expire,
                                       minimum)

    def create_a(self, ip):
        return dns.rdtypes.IN.A.A(IN, A, ip)

    def create_aaaa(self, ipv6):
        return dns.rdtypes.IN.AAAA.AAAA(IN, AAAA, ipv6)

    def create_mx(self, pref, name):
        return dns.rdtypes.ANY.MX.MX(IN, MX, int(pref), dns.name.from_text(name, self.origin))

    def create_ns(self, name):
        return dns.rdtypes.ANY.NS.NS(IN, NS, dns.name.from_text(name, self.origin))

    def create_cname(self, name):
        return dns.rdtypes.ANY.CNAME.CNAME(IN, CNAME, dns.name.from_text(name, self.origin))

    def create_txt(self, text):
        return dns.rdtypes.ANY.TXT.TXT(IN, TXT, text)

    def create_srv(self, priority, weight, port, target):
        return dns.rdtypes.IN.SRV.SRV(IN, SRV, int(priority), int(weight), int(port), dns.name.from_text(target, self.origin))

    def create_hinfo(self, hardware, os):
        return dns.rdtypes.ANY.HINFO.HINFO(IN, HINFO, hardware, os)

    def create_ptr(self, name):
        return dns.rdtypes.ANY.PTR.PTR(IN, PTR, dns.name.from_text(name))