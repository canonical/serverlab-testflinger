#!/usr/bin/python3

"""Export exec user's ssh pubkey (.ssh/id_rsa.pub) into Maas."""

import os
import json
import argparse
from time import sleep
from pathlib import Path
from requests import Request, Session
from requests_oauthlib import OAuth1
# from pudb import set_trace; set_trace()


def file_read(fpath):
    """Read file."""
    try:
        with open(fpath, 'r') as _file:
            return _file.read().splitlines()
    except OSError:
        print('Unable to read file: %s' % fpath)


def delete_pubkey(auth1, url, session):
    """DELETE pubkey via url."""
    hostname = os.uname()[1]
    request = Request('GET', url, auth=auth1)
    response = session.send(request.prepare())

    for _dict in json.loads(response.text):
        if hostname in _dict['key']:
            id_n = _dict['id']
            break
    else:
        id_n = 0

    if id_n:
        # throttle api calls
        sleep(.4)
        url_id = (url + '%i/' % id_n)
        request = Request('DELETE', url_id, auth=auth1)
        response = session.send(request.prepare())

        return response

    return 0


def post_pubkey(auth1, ssh_key, url):
    """POST pubkey via url."""
    payload = {'key': ssh_key}
    session = Session()
    request = Request('POST', url, data=payload, auth=auth1)
    response = session.send(request.prepare())

    if 'key has already been added' in response.text:
        print('User key already exists!')
        print('Replacing offending key...')
        print('    * delete:')
        response_delete = delete_pubkey(auth1, url, session)
        print('        - OK: ' + str(response_delete.ok))
        print('        - Status code: ' + str(response_delete.status_code))

        if response_delete:
            # throttle api calls
            sleep(.4)
            print('    * post:')
            request = Request('POST', url, data=payload, auth=auth1)
            response = session.send(request.prepare())
            print('        - OK: ' + str(response.ok))
            print('        - Status code: ' + str(response.status_code))

    return response


def main():
    # call with api_key and url components (maas ip, port) as args
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='/base/path/of/keyfile/')
    parser.add_argument('--mapi', help='maas api key')
    parser.add_argument('--mhost', help='maas server ip')
    parser.add_argument('--mport', help='maas server port')
    args = parser.parse_args()

    if args.path:
        ssh_key = file_read(os.path.join(
            str(args.path), '.ssh', 'id_rsa.pub'))
    else:
        ssh_key = file_read(os.path.join(
            str(Path.home()), '.ssh', 'id_rsa.pub'))

    if args.mapi:
        api_key = args.mapi
    else:
        raise OSError('API key required!')

    if args.mhost and args.mport:
        url = (
            u'http://%s:%s/MAAS/api/2.0/account/prefs/sshkeys/' % (
                args.mhost, args.mport))
    elif args.mhost and not args.mport:
        def_port = 5240
        url = (
            u'http://%s:%i/MAAS/api/2.0/account/prefs/sshkeys/' % (
                args.mhost, def_port))
    else:
        raise OSError('MaaS host required!')

    # split api_key into tuple for auth components
    api_key = tuple(api_key.split(':'))
    auth1 = OAuth1(api_key[0], u'',
                   api_key[1], api_key[2])

    try:
        response = post_pubkey(auth1, ssh_key, url)
    except OSError:
        print('Check server paramaters.')
    else:
        print('- OK: ' + str(response.ok))
        print('- Status code: ' + str(response.status_code))
        print(response.text)

        if response.ok:
            print('- Sucessfully exported ssh pubkey!')


if __name__ == '__main__':
    main()
