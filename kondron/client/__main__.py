"""
Showing how the minimal client app could look like.
"""
import click
import re
import logging
import requests
from web3 import Web3, HTTPProvider
from microraiden import Session
from microraiden.constants import WEB3_PROVIDER_DEFAULT, TKN_DECIMALS
from microraiden.config import NETWORK_CFG

# from kondron.client.client import Client
# Client should be enough, but at this point in time there was a bug related to event retrieval
from kondron.client.client import NewClient


log = logging.getLogger(__name__)


@click.command()
@click.option(
    '--private-key',
    required=True,
    help='Path to private key file or a hex-encoded private key.',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--password-path',
    default=None,
    help='Path to file containing the password for the private key specified.',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--command',
    default='fly1',
    required=True,
    help='Get this resource.'
)
@click.option(
    '--rpc-provider',
    default=WEB3_PROVIDER_DEFAULT,
    help='Address of the Ethereum RPC provider'
)
def main(
        private_key: str,
        password_path: str,
        command: str,
        rpc_provider: str
):
    run(private_key, password_path, command, rpc_provider)


def run(
        private_key: str,
        password_path: str,
        command: str,
        rpc_provider: str,
        channel_manager_address: str = None,
        web3: Web3 = None,
        retry_interval: float = 5,
        endpoint_url: str = 'http://localhost:5000'
):
    if channel_manager_address is None:
        web3 = Web3(HTTPProvider(rpc_provider))
        NETWORK_CFG.set_defaults(int(web3.version.network))

    # Create the client session.
    client = NewClient(
        private_key,
        password_path,
        NETWORK_CFG.CHANNEL_MANAGER_ADDRESS,
        web3
    )

    session = Session(
        client=client,
        endpoint_url=endpoint_url,
        private_key=private_key,
        key_password_path=password_path,
        channel_manager_address=NETWORK_CFG.CHANNEL_MANAGER_ADDRESS,
        web3=web3,
        retry_interval=retry_interval,
        initial_deposit= lambda price: 5 * TKN_DECIMALS,
        topup_deposit= lambda price: 5 * TKN_DECIMALS,
        close_channel_on_exit=False
    )
    # Get the resource. If payment is required, client will attempt to create
    # a channel or will use existing one.
    resource = command
    response = session.get('{}/{}'.format(endpoint_url, resource))

    if response.status_code == requests.codes.OK:
        if re.match('^text/', response.headers['Content-Type']):
            logging.info(
                "Got the resource {} type={}:\n{}".format(
                    resource,
                    response.headers.get('Content-Type', '???'),
                    response.text
                )
            )
        else:
            logging.info(
                "Got the resource {} type={} (not echoed)".format(
                    resource,
                    response.headers.get('Content-Type', '???')
                )
            )
    else:
        logging.error(
            "Error getting the resource. Code={} body={}".format(
                response.status_code,
                response.text
            )
        )
    return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("channel_manager").setLevel(logging.INFO)
    logging.getLogger("client").setLevel(logging.INFO)
    logging.getLogger("session").setLevel(logging.INFO)
    main()
