from django.db import transaction
from django.db.models import Sum

from scanners.handlers.transfer_burn import HandlerTransferBurn
from src.accounts.models import AdvUser
from src.activity.models import TokenHistory
from src.games.import_limits import increment_import_requests
from src.store.models import Token


class HandlerBatchTransferBurn(HandlerTransferBurn):
    TYPE = "batch_transfer"

    @transaction.atomic
    def save_event(self, event_data):
        data_list = self.scanner.parse_data_batch_transfer(event_data)
        for data in data_list:
            self.logger.debug(f"New transfer batch event: {data}")

            token = Token.objects.filter(
                collection__network=self.network,
                collection__address=self.contract.address,
                internal_id=data.token_id,
            ).first()
            if not token:
                continue

            increment_import_requests(self.network)

            new_owner = self.get_owner(data.new_owner)
            old_owner = self.get_owner(data.old_owner)
            _, created = TokenHistory.objects.get_or_create(
                tx_hash=data.tx_hash,
                token=token,
                defaults={
                    "method": "Transfer",
                    "price": None,
                    "amount": data.amount,
                    "new_owner": new_owner,
                    "old_owner": old_owner,
                },
            )

            if not created:
                self.logger.debug(f"History with tx hash {data.tx_hash} exists")
                continue

            new_owner = data.new_owner.lower()
            new_owner = (
                self.get_owner(new_owner)
                if new_owner != self.scanner.EMPTY_ADDRESS.lower()
                else None
            )
            old_owner = data.old_owner.lower()
            old_owner = (
                self.get_owner(old_owner)
                if old_owner != self.scanner.EMPTY_ADDRESS.lower()
                else None
            )

            amount = correct_ownership_amount(data.amount, new_owner, token)

            self.ownership_quantity_update(
                token=token,
                old_owner=old_owner,
                new_owner=new_owner,
                amount=amount,
            )


def correct_ownership_amount(amount: int, owner: "AdvUser", token: "Token") -> int:
    difference = (
        TokenHistory.objects.filter(
            new_owner=owner,
            token=token,
            method__in=["Transfer", "Mint", "Burn", "Buy", "AuctionWin"],
        ).aggregate(receive_amount=Sum("amount"))["receive_amount"]
        or 0
    ) - (
        TokenHistory.objects.filter(
            old_owner=owner,
            token=token,
            method__in=["Transfer", "Mint", "Burn", "Buy", "AuctionWin"],
        ).aggregate(sent_amount=Sum("amount"))["sent_amount"]
        or 0
    )
    return amount + min(difference, 0)
