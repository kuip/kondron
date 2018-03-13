"""
Showing how the minimal server could look like.
"""
import logging
import os
import click
from flask import request
from web3 import Web3, HTTPProvider

from microraiden.channel_manager import ChannelManager
from microraiden.make_helpers import make_channel_manager
from microraiden.constants import WEB3_PROVIDER_DEFAULT
from microraiden.config import NETWORK_CFG
from microraiden.constants import TKN_DECIMALS
from microraiden.proxy import PaywalledProxy
from microraiden.proxy.resources import Expensive
from microraiden.utils import get_private_key

#from kondron.main import Fly1

host = '192.168.1.1'
# host = '172.16.10.1'

import time
import telnetlib
from telnetlib import Telnet
from kondron.kondron import Kontrol

log = logging.getLogger(__name__)


class StaticPriceResource(Expensive):
    def get(self, url: str, param: str):
        log.info('Resource requested: {} with param "{}"'.format(request.url, param))
        return param


class DynamicPriceResource(Expensive):
    def get(self, url: str):
        log.info('Fly1 sequence requested: {}'.format(request.url))

        with Telnet(host) as tn:
            myKontrol = Kontrol(host, 80, 'admin', '', tn)
            # myKontrol.opentelnet()
            myKontrol.init_telnet_connection()

            time.sleep(0.3)

            # "\xfa\x40\x40\x40\x40\x00\x00"

            sleep = 0.1
            period = 3
            diff = 5
            maxt = 170  # 255
            mint = 64

            t_end = time.time() + period
            throttle = 64
            state = myKontrol.set_state({'throttle': 64, 'rudder': 64, 'elevation': 64, 'aileron': 64, 'time': sleep})
            while time.time() < t_end:
                throttle += diff
                throttle = min(throttle, maxt)
                state = myKontrol.set_state({'throttle': throttle})
                myKontrol.send_comm()

            t_end = time.time() + 2
            i = 0
            while time.time() < t_end:
                if i % 2 == 0:
                    throttle -= diff
                else:
                    throttle += diff
                state = myKontrol.set_state({'throttle': throttle})
                myKontrol.send_comm()
                myKontrol.snapshot(None)

            t_end = time.time() + period
            while time.time() < t_end:
                throttle -= diff
                throttle = max(mint, throttle)
                state = myKontrol.set_state({'throttle': throttle})
                myKontrol.send_comm()

            time.sleep(8)

            myKontrol.close()

            return 'done'

    def price(self):
        log.info('Send requested price of ' + str(int(0.000001 * TKN_DECIMALS)))
        return int(0.000001 * TKN_DECIMALS)


@click.command()
@click.option(
    '--private-key',
    required=True,
    help='The server\'s private key path.',
    type=str
)
@click.option(
    '--rpc-provider',
    default=WEB3_PROVIDER_DEFAULT,
    help='Address of the Ethereum RPC provider'
)
def main(private_key: str, rpc_provider: str):
    private_key = get_private_key(private_key)
    run(private_key, rpc_provider)


def run(
        private_key: str,
        rpc_provider: str,
        state_file_path: str = os.path.join(click.get_app_dir('microraiden'), 'kondron.db'),
        channel_manager: ChannelManager = None,
        join_thread: bool = True
):
    dirname = os.path.dirname(state_file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    # set up a paywalled proxy
    # arguments are:
    #  - private key to use for receiving funds
    #  - file for storing state information (balance proofs)
    if channel_manager is None:
        web3 = Web3(HTTPProvider(rpc_provider))
        NETWORK_CFG.set_defaults(int(web3.version.network))
        channel_manager = make_channel_manager(
            private_key,
            NETWORK_CFG.CHANNEL_MANAGER_ADDRESS,
            state_file_path,
            web3
        )
    app = PaywalledProxy(channel_manager)

    # Add resource defined by regex and with a fixed price of 1 token.
    #app.add_paywalled_resource(
    #    StaticPriceResource,
    #    "/fly1/<int:param>",
    #    price=0.0001
    #)
    # Resource with a price determined by the second parameter.
    app.add_paywalled_resource(
        DynamicPriceResource,
        "/fly1"
    )

    # Start the app. proxy is a WSGI greenlet, so you must join it properly.
    app.run(debug=True)

    if join_thread:
        app.join()
    else:
        return app
    # Now use the Client to get the resources.


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
