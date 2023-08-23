#!/usr/bin/env python

import argparse
import sys
import requests
import pandas as pd
from io import StringIO
import base64
import subprocess
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='Connect to a VPN server based on country name or code.')
    parser.add_argument('-l', '--list', action='store_true', help='List name of the country available')
    parser.add_argument('-c', '--country', help='Name or code of the country to connect to')
    args = parser.parse_args()

    if not (args.list or args.country):
        parser.print_help()
        sys.exit()
    elif args.country and len(args.country) < 2:
        print('Country code is incorrect.')
        sys.exit()
    else:
        return args


def download_vpn_data():
    try:
        r = requests.get('http://www.vpngate.net/api/iphone/')
        csv_data = '\n'.join(r.text.split('\n')[1:-2])
        csv_file = StringIO(csv_data)
        df = pd.read_csv(csv_file)
        return df
    except requests.RequestException as e:
        print('Cannot get VPN servers data:', e)
        sys.exit()


def get_available_countries():
    countries = {row['CountryShort']: row['CountryLong'] for index, row in df.iterrows()}
    print(countries)
    sys.exit()


def get_best_server():
    if len(args.country) == 2:
        filtered_servers = df[df['CountryShort'] == args.country.upper()]
    elif len(args.country) > 2:
        filtered_servers = df[df['CountryLong'] == args.country.capitalize()]

    filtered_servers = filtered_servers[['#HostName', 'Speed','CountryLong', 'OpenVPN_ConfigData_Base64']]
    winner = filtered_servers.loc[filtered_servers['Speed'].idxmax()]
    print(f"{len(filtered_servers)} servers found for country {winner['CountryLong']} with OpenVPN support")

    print('\n== Best server ==')
    print(f"Hostname: {winner['#HostName']}.opengw.net")
    print(f"Bandwidth: {float(winner['Speed']/ 10**6)} MBps")

    return winner['OpenVPN_ConfigData_Base64']


def write_config_to_file(config):
    f = open('vpngate.ovpn', 'w')
    f.write(base64.b64decode(config).decode('utf-8'))
    f.close()

def launch_vpn_connection():
    try:
        x = subprocess.Popen(['sudo', 'openvpn', '--config', 'vpngate.ovpn', '--data-ciphers', 'AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305:AES-128-CBC', '--auth-user-pass', 'pass.txt'])

        while True:
            try:
                time.sleep(600)
            except KeyboardInterrupt:
                x.terminate()
                x.wait()
                print('\nVPN terminated')
                sys.exit()
    except OSError as e:
        print('Error launching VPN:', e)
        sys.exit()


if __name__ == '__main__':
    args = parse_arguments()

    df = download_vpn_data()

    if args.list:
        get_available_countries()

    bestServer = get_best_server()

    while True:
        choice = input('\nDo you want to connect [y|n] ? ')
        if choice == 'y':
            print('\nLaunching VPN...')
            write_config_to_file(bestServer)
            launch_vpn_connection()
        elif choice == 'n':
            sys.exit()
        else:
            print('Invalid input')
