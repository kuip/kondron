import logging
from eth_utils import decode_hex, is_same_address, is_hex, remove_0x_prefix, to_checksum_address
from microraiden.utils import get_logs
from microraiden.client import Client, Channel

from microraiden.config import NETWORK_CFG

log = logging.getLogger(__name__)

start_sync_block = NETWORK_CFG.start_sync_block


class NewClient(Client):
    def sync_channels(self):
        """
        Merges locally available channel information, including their current balance signatures,
        with channel information available on the blockchain to make up for local data loss.
        Naturally, balance signatures cannot be recovered from the blockchain.
        """
        filters = {'_sender_address': self.context.address}
        create = get_logs(
            self.context.channel_manager,
            'ChannelCreated',
            argument_filters=filters,
            from_block=start_sync_block,
            to_block='latest'
        )
        topup = get_logs(
            self.context.channel_manager,
            'ChannelToppedUp',
            argument_filters=filters,
            from_block=start_sync_block,
            to_block='latest'
        )
        close = get_logs(
            self.context.channel_manager,
            'ChannelCloseRequested',
            argument_filters=filters,
            from_block=start_sync_block,
            to_block='latest'
        )
        settle = get_logs(
            self.context.channel_manager,
            'ChannelSettled',
            argument_filters=filters,
            from_block=start_sync_block,
            to_block='latest'
        )

        channel_key_to_channel = {}

        def get_channel(event) -> Channel:
            sender = to_checksum_address(event['args']['_sender_address'])
            receiver = to_checksum_address(event['args']['_receiver_address'])
            block = event['args'].get('_open_block_number', event['blockNumber'])
            assert is_same_address(sender, self.context.address)
            return channel_key_to_channel.get((sender, receiver, block), None)

        for c in self.channels:
            channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in create:
            c = get_channel(e)
            if c:
                c.deposit = e['args']['_deposit']
            else:
                c = Channel(
                    self.context,
                    to_checksum_address(e['args']['_sender_address']),
                    to_checksum_address(e['args']['_receiver_address']),
                    e['blockNumber'],
                    e['args']['_deposit'],
                    on_settle=lambda channel: self.channels.remove(channel)
                )
                assert is_same_address(c.sender, self.context.address)
                channel_key_to_channel[(c.sender, c.receiver, c.block)] = c

        for e in topup:
            c = get_channel(e)
            c.deposit += e['args']['_added_deposit']

        for e in close:
            # Requested closed, not actual closed.
            c = get_channel(e)

            c.update_balance(e['args']['_balance'])
            c.state = Channel.State.settling

        for e in settle:
            c = get_channel(e)
            c.state = Channel.State.closed

        # Forget closed channels.
        self.channels = [
            c for c in channel_key_to_channel.values() if c.state != Channel.State.closed
        ]

        log.debug('Synced a total of {} channels.'.format(len(self.channels)))
