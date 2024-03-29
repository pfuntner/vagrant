#!/usr/bin/env python
# Adapted from Mark Mandel's implementation
# https://github.com/ansible/ansible/blob/stable-2.1/contrib/inventory/vagrant.py

"""
I originally got this script from https://github.com/pfuntner/ansiblebook/blob/master/ch03/inventory/vagrant.py and made my own changes to it.

Later in reading the book, I learned about a repository for dynamic inventory scripts for various purposes and found https://raw.githubusercontent.com/ansible/ansible/devel/contrib/inventory/vagrant.py which is superior to the one in the book.
"""

import argparse
import json
import paramiko
import subprocess
import sys
import logging
import StringIO

def parse_args():
    parser = argparse.ArgumentParser(description="Vagrant inventory script")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='List all vagrant hosts')
    group.add_argument('--host', help='Display details about a host')

    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debugging')
    return parser.parse_args()


def list_running_hosts():
    cmd = "vagrant status --machine-readable"
    log.debug('cmd: {cmd!r}'.format(**locals()))
    status = subprocess.check_output(cmd.split()).rstrip()
    log.debug('status: {status!r}'.format(**locals()))
    hosts = []
    for line in status.splitlines():
        (_, host, key, value) = line.split(',')[:4]
        log.debug('line: {line!r}, _: {_!r}, host: {host!r}, key: {key!r}, value: {value!r}'.format(**locals()))
        if key == 'state' and value == 'running':
            hosts.append(host)
    return hosts


def get_host_details(host):
    cmd = "vagrant ssh-config {}".format(host)
    log.debug('cmd: {cmd!r}'.format(**locals()))
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    rc = p.wait()
    ok = (rc == 0) and (not stderr)
    log.log(logging.DEBUG if ok else logging.WARNING, '{cmd!r}: {rc}, {stdout!r}, {stderr!r}'.format(**locals()))
    if not ok:
      return {}

    config = paramiko.SSHConfig()
    config.parse(StringIO.StringIO(stdout))
    c = config.lookup(host)
    return {'ansible_host': c['hostname'],
            'ansible_port': c['port'],
            'ansible_user': c['user'],
            'ansible_private_key_file': c['identityfile'][0]}


def main():
    global log
    args = parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(pathname)s:%(lineno)d %(msg)s')
    log = logging.getLogger('vagrant_py')
    log.setLevel(logging.DEBUG if args.verbose else logging.WARNING)

    if args.list:
        hosts = list_running_hosts()
        print json.dumps({'vagrant': hosts})
    else:
        details = get_host_details(args.host)
        print json.dumps(details)

log = None
if __name__ == '__main__':
    main()

