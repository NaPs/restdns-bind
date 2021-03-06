import os
import subprocess

import requests

import dns.zone
import dns.name

from .zones import RecordFactory, SOA


TMPL_ZONE = '''
zone "{name}." {{
        type master;
        file "{fullname}";
}};
'''


def json_compat(response):
    """ Compatibility layer for requests JSON helper pre and post v1.0.0.
    """
    if callable(response.json):
        return response.json()
    else:
        return response.json


class RestdnsBind(object):

    def __init__(self, logger, restdns_base_url, output_directory, run_rndc, rndc_binary_path):
        self.logger = logger
        self._restdns_base_url = restdns_base_url.rstrip('/')
        self._output_directory = output_directory
        self._run_rndc = run_rndc
        self._rndc_binary_path = rndc_binary_path
        self.zones = []

    def run(self):
        remote_zones = self._get_remote_zones()
        self.zones = remote_zones
        local_zones = self._get_local_zones()

        to_write = set()
        to_delete = set()

        # Get zones to delete (zones existing locally but no more on the
        # restdns server):
        to_delete |= set(local_zones) - set(remote_zones)
        self.logger.debug('Zones to delete: %s', ','.join(to_delete) or 'none')

        # Get zones to generate (not existing locally or higher serial):
        for name, infos in remote_zones.iteritems():
            local_infos = local_zones.get(name)
            if local_infos is None:
                to_write.add(name)  # Zone not exiting yet locally
            else:
                if infos['serial'] > local_infos['serial']:
                    to_write.add(name)
        self.logger.debug('Zones to write: %s', ','.join(to_write) or 'none')

        # Delete old zones:
        for name in to_delete:
            filename = os.path.join(self._output_directory, '%s.zone' % name)
            os.unlink(filename)
            self.logger.debug('Removed: %s', filename)

        # Generate zones:
        for name in to_write:
            url = remote_zones[name]['url']
            self._write_zone(url)

        # Regenerate Bind configuration file if something have changed;
        if to_write or to_delete:
            self._write_zone_conf(remote_zones.keys())
            self.logger.debug('Regenerated configuration file')

        # Reload Bind configuration using rndc:
        if self._run_rndc and (to_write or to_delete):
            self.logger.debug('Executing rndc reload...')
            try:
                rndc = subprocess.Popen([self._rndc_binary_path, 'reload'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            except OSError as err:
                self.logger.warning('Error while invoking rndc reload: %s', err)
            else:
                rcode = rndc.wait()
                if rcode:
                    self.logger.warning('Non-null return code when executing rndc reload (%s)', rcode)

    def _write_zone_conf(self, zones):
        """ Write the zone list configuration.
        """
        with open(os.path.join(self._output_directory, 'zones.conf'), 'w') as fzones:
            for zone in zones:
                fzones.write(TMPL_ZONE.format(name=zone, fullname=os.path.join(self._output_directory, '%s.zone' % zone)))

    def _get_remote_zones(self):
        zones_url = self._restdns_base_url + '/zones'
        zones = {}
        for zone in json_compat(requests.get(zones_url))['zones']:
            zones[zone['name']] = {'url': zone['url'], 'serial': zone['serial']}
        return zones

    def _get_local_zones(self):
        zones = {}
        for filename in os.listdir(self._output_directory):
            if filename.endswith('.zone'):
                fullname = os.path.join(self._output_directory, filename)
                name, serial = self._read_zone(fullname)
                zones[name] = {'serial': serial}
        return zones

    def _read_zone(self, path):
        zone = dns.zone.from_file(path, check_origin=False, allow_include=False)
        rd_set = zone.get_rdataset('', SOA)
        soa = rd_set[0]  # Only one SOA is allowed per zone
        return zone.origin.to_text(omit_final_dot=True), soa.serial

    def _install_records(self, record_factory, dns_zone, records_url, prefix=''):
        records = json_compat(requests.get(self._restdns_base_url + records_url))
        for record in records['records']:
            if record['type'] == 'include':
                zone_name = record['parameters']['zone']
                if zone_name in self.zones:
                    zone_infos = self.zones[zone_name]
                    zone_url = self._restdns_base_url + zone_infos['url']
                    zone = json_compat(requests.get(zone_url))
                    self._install_records(record_factory, dns_zone, zone['records_url'], prefix=record['name'])
            else:
                if prefix and record['name']:
                    name = '.'.join((prefix, record['name']))
                elif prefix:
                    name = prefix
                else:
                    name = record['name']
                rd_set = dns_zone.get_rdataset(name, record['type'], create=True)
                rd_set.add(record_factory.create_record(record['type'], record['parameters']))


    def _write_zone(self, zone_url):
        """ Write a local zone file using a remote zone URL.
        """
        # Get the zone details:
        zone_url = self._restdns_base_url + zone_url
        zone = json_compat(requests.get(zone_url))
        origin = dns.name.from_text(zone['name'] + '.')
        dns_zone = dns.zone.Zone(origin)
        record_factory = RecordFactory(origin)

        # Create the SOA record:
        rd_set = dns_zone.get_rdataset('', SOA, create=True)
        rd_set.add(record_factory.create_soa(zone['rname'],
                                             zone['serial'],
                                             zone['refresh'],
                                             zone['retry'],
                                             zone['expire'],
                                             zone['minimum']))

        self._install_records(record_factory, dns_zone, zone['records_url'])

        zone_filename = os.path.join(self._output_directory, '%s.zone' % zone['name'])
        fzone = open(zone_filename, 'w')
        # Write the $ORIGIN statement (dnspython seem not able to write it)
        fzone.write('$ORIGIN %s\n' % origin)
        dns_zone.to_file(fzone, relativize=False)
        self.logger.debug('Wrote: %s', zone_filename)
