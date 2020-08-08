# Interactions
#
# Log into a blade
# Log out of a blade
#
# View identity of a blade
# List subscriptions
# List timeline
# List private messages
# Post entry
#   Required data: none?
# Read entry
#   Go to related entries (replying to, replies, etc)
#   New entry based on this one
#   Should also show previews of related entries
#   Required data: Entry content, related entry previews + relation info
# At listings
#   Paginated, go to next/previous page
#   Required data: List of entry previews

import requests
import sys
import time
from urllib3.exceptions import NewConnectionError


def pause():
    time.sleep(0.2)


def slow_print(l=''):
    typewriter_print(l)
    # time.sleep(0.2)


def typewriter_print(l):
    for c in l:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(0.005)
    sys.stdout.write('\n')
    sys.stdout.flush()


PROTOCOL = 'http://'

COMMAND_HELP = {
    'help': {
        'description': 'Display help information about commands.'
    },

    'exit': {
        'description': 'Exit the CLI client.'
    },

    'connect': {
        'description': 'Connect to a blade at the given address.',
        'usages': [{
            'syntax': 'connect <address>'
        }]
    },

    'disconnect': {
        'description': 'Disconnect from the current blade.'
    },

    'blade': {
        'description': 'Display information about the connected blade.'
    },

    'subscriptions': {
        'description': 'List the blade\'s subscriptions.'
    }
}


class SimpleCLIClient:
    __slots__ = ['connected_blade', 'cookies']

    def __init__(self):
        self.connected_blade = None
        self.cookies = None

    def start(self):
        slow_print()
        slow_print('Labrys Simple CLI Client')
        slow_print()
        slow_print('Type the command `help` to get help information.')

        self.interact()

    def interact(self):
        should_exit = False
        while not should_exit:
            slow_print()
            cmd = input('> ')
            parsed_cmd = SimpleCLIClient.parse_command(cmd)
            should_exit = self.handle_command(parsed_cmd)

        self.stop()

    def stop(self):
        slow_print()
        slow_print('Goodbye!')
        slow_print()

    @staticmethod
    def parse_command(cmd):
        words = cmd.split()

        if len(words) < 1:
            return None

        return {
            'command': words[0],
            'arguments': words[1:]
        }

    def handle_command(self, cmd):
        if cmd is None:
            return

        name = cmd['command']
        args = cmd['arguments']

        if name == 'exit':
            return self.command_exit()
        elif name == 'connect':
            return self.command_connect(args)
        elif name == 'disconnect':
            return self.command_disconnect()
        elif name == 'help':
            return self.command_help()
        elif name == 'blade':
            return self.command_blade()
        elif name == 'subscriptions':
            return self.command_subscriptions()
        else:
            slow_print()
            slow_print('Command not recognized.')

    def command_exit(self):
        return True

    def command_connect(self, args):
        if len(args) != 1:
            slow_print()
            slow_print('Incorrect usage. Please try:')
            slow_print()
            slow_print('    connect <address>')

        else:
            address = args[0]
            slow_print()
            slow_print('Connecting to %s...' % address)
            slow_print('Please wait...')
            pause()

            try:
                response = requests.get(
                    PROTOCOL + address + '/identity/public_signing_key')
                address_is_blade = response.status_code == 200
            except:
                address_is_blade = False

            if address_is_blade:
                slow_print('Connection established!')
                slow_print()
                slow_print('Please enter the login password for this blade.')
                password = input('> ')

                response = requests.post(
                    PROTOCOL + address + '/identity/authenticate', data=password)

                if response.status_code == 200:
                    slow_print()
                    slow_print('Successfully logged into the blade.')
                    self.connected_blade = address
                    self.cookies = response.cookies
                else:
                    slow_print('Incorrect password.')
            else:
                slow_print(
                    'Connection failed: address does not point to a labrys blade.')

    def command_disconnect(self):
        slow_print()
        slow_print('Disconnecting from %s...' % self.connected_blade)
        pause()
        self.connected_blade = None
        self.cookies = None

    def command_help(self):

        for name in COMMAND_HELP:
            cmd = COMMAND_HELP[name]
            slow_print()
            if 'usages' in cmd and len(cmd['usages']) == 1:
                slow_print(cmd['usages'][0]['syntax'])
            else:
                slow_print(name)
            slow_print('  ' + cmd['description'])
            if 'usages' in cmd and len(cmd['usages']) > 1:
                for usage in cmd['usages']:
                    slow_print('  Usage:  ' + usage['syntax'])

    def command_blade(self):
        if self.connected_blade is None:
            slow_print()
            slow_print('Not connected to a blade.')
        else:

            slow_print()
            slow_print('Blade Address: ' + self.connected_blade)

            response = requests.get(
                PROTOCOL + self.connected_blade + '/identity/display_name')
            if response.status_code == 200:
                slow_print()
                slow_print('Display Name: ' + response.text)

            response = requests.get(
                PROTOCOL + self.connected_blade + '/identity/bio')
            if response.status_code == 200:
                slow_print()
                slow_print('Bio:')
                slow_print()
                for l in response.text.split('\n'):
                    slow_print('  ' + l)

            response = requests.get(
                PROTOCOL + self.connected_blade + '/identity/public_signing_key')
            if response.status_code == 200:
                slow_print()
                slow_print('Public Signing Key:')
                slow_print()
                for l in response.text.split('\n'):
                    slow_print('  ' + l)

    def command_subscriptions(self):
        slow_print()
        slow_print('====== Subscriptions ======')


if __name__ == '__main__':
    client = SimpleCLIClient()
    client.start()
