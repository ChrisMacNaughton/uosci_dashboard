import argparse
from jinja2 import Environment, PackageLoader, select_autoescape

import os
import sys

import uosci_dashboard.mojo as mojo

UOS_COMBOS = [
    'trusty-icehouse',
    'trusty-kilo',
    'trusty-liberty',
    'trusty-mitaka',
    'xenial-mitaka',
    'xenial-newton',
    'xenial-ocata',
    'xenial-pike',
    'xenial-queens',
    # 'artful-pike',
    'bionic-queens',
    'bionic-rocky',
    # 'cosmic-rocky',
]


def parse_args(args):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        help='Jenkins User',
                        required=False)
    parser.add_argument('-p', '--password',
                        help='Jenkins password',
                        required=False)
    parser.add_argument('-t', '--host',
                        help='Jenkins host')
    parser.add_argument('-f', '--path',
                        help='Site build path')
    parser.set_defaults(host='http://10.245.162.58:8080')
    parser.set_defaults(filter=None)
    parser.set_defaults(path='site')
    return parser.parse_args(args)


def main():
    env = Environment(
        loader=PackageLoader('uosci_dashboard'),
        autoescape=select_autoescape(['html', 'xml']),
    )
    env.globals['uos_combos'] = UOS_COMBOS
    args = parse_args(sys.argv[1:])
    env.globals['jenkins_host'] = args.host
    jenkins_conf = {
        'host': args.host,
        'username': args.username,
        'password': args.password,
    }
    try:
        os.mkdir(args.path)
    except:
        pass
    templates = []
    templates.append((
        env.get_template('index.html'),
        {}
    ))
    for template in mojo.execute(jenkins_conf, env):
        templates.append(template)

    for template, data in templates:
        print("Rendering {}".format(template.name))
        with open("{}/{}".format(args.path, template.name), 'w') as f:
            f.write(template.render(data))
    # template = get_template('index')
    # template.render()
    # mojo.execute(jenkins_conf, 'site')
