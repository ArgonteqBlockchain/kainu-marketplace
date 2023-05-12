from typing import List

from scanners.data_structures import BatchTransferData


class BatchTransferMixin:
    def get_events_batch_transfer(self, last_checked_block, last_network_block):
        event = self.network.get_erc1155main_contract(
            self.contract.address
        ).events.TransferBatch
        return event.createFilter(
            fromBlock=last_checked_block,
            toBlock=last_network_block,
        ).get_all_entries()

    def parse_data_batch_transfer(self, event) -> List[BatchTransferData]:
        data = []
        ids = event["args"].get("ids")
        amounts = event["args"].get("values")
        old_owners = event["args"].get("from")
        new_owners = event["args"].get("to")
        for token_id, amount in zip(ids, amounts):
            data.append(
                BatchTransferData(
                    token_id=token_id,
                    tx_hash=event["transactionHash"].hex(),
                    amount=amount,
                    old_owner=old_owners,
                    new_owner=new_owners,
                )
            )
        return data
