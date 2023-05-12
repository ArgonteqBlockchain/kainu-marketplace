import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
import django
django.setup()

from django.db import transaction
from scanners.data_structures import TransferData
from scanners.handlers import HandlerTransferBurn
from src.store.models import Collection
from src.activity.models import TokenHistory
from src.networks.models import Network
collection = Collection.objects.first()

data_list = [
TransferData(token_id=150, new_owner='0xa94cd522db29c3518b905d6eb81d5a2b870e46fd', old_owner='0x13d995687c203a71f2a5dc28d7fea458d50daf0e', tx_hash='0xd163d8c09d31ad77e1dba41fea832f5b01813798f5f08061bb806acbcbbe22ea', amount=1),
TransferData(token_id=197, new_owner='0x49458854536c2845b250beb87d2de051ec31616a', old_owner='0x36c72892fcc72b52fa3b82ed3bb2a467d9079b9a', tx_hash='0x509bd307d681c81b7b4fb9d14f2439f6dd9812625ac297ee87cb99128e36a665', amount=1),
TransferData(token_id=499, new_owner='0xe374b16456ebade95423eb709e9a2ca29366b7f0', old_owner='0x36c72892fcc72b52fa3b82ed3bb2a467d9079b9a', tx_hash='0x4d824839d34c33d96a0e47d4219cf9ce39639e59964f95a81c24fa7508f02f47', amount=1),
TransferData(token_id=507, new_owner='0x53201b44e37eec44e97ea0029e16558e8d974fdf', old_owner='0xe15b9f0d3cf0c839010b45908c1af7fda84c983c', tx_hash='0x9a90c463c7db110529844a9c6cd91e15194e38da12f40d2e782a1dccbeb9ddcd', amount=1),
TransferData(token_id=615, new_owner='0xa94cd522db29c3518b905d6eb81d5a2b870e46fd', old_owner='0x13d995687c203a71f2a5dc28d7fea458d50daf0e', tx_hash='0xd163d8c09d31ad77e1dba41fea832f5b01813798f5f08061bb806acbcbbe22ea', amount=1),
TransferData(token_id=711, new_owner='0x69bb65f3a22f7ad72aecb1e34b2c2feed4a68bca', old_owner='0xbd7c4aabd94cb5a5b7516587e30f40b9ee823004', tx_hash='0xaef4b011013ad604ad368b31e1d6ddb68575b7d357ad2166093b473ae8e984de', amount=1),
TransferData(token_id=813, new_owner='0xb62ba52124f3022acaef88e458688bbb568f4bde', old_owner='0x893a478bcb797ecbf4a7c959a677dc8d046b6249', tx_hash='0x4f57f1adabd636e135a66e109f88060ce993c28db75d13de79904e743940df83', amount=1),
TransferData(token_id=824, new_owner='0x114e6de851c6204d6d0de861d402ef262fb216c4', old_owner='0xbfe5dbe545394e841bc93a59da81673d19101ec1', tx_hash='0x2978d02473e1e82b931488b15db9f588a1618e2d5d730cf8893c0dceea8972b6', amount=1),
TransferData(token_id=894, new_owner='0x5142c30205ec73afe445e7ae548016005a0c48f7', old_owner='0x874be0f865da96fc35654d11e9518a11339a2994', tx_hash='0x6b0a29f6217db47d0b668868b45478c1337c3c07a87b123b8b6120091bd53ab0', amount=1),
TransferData(token_id=895, new_owner='0x5142c30205ec73afe445e7ae548016005a0c48f7', old_owner='0x874be0f865da96fc35654d11e9518a11339a2994', tx_hash='0x6b0a29f6217db47d0b668868b45478c1337c3c07a87b123b8b6120091bd53ab0', amount=1),
TransferData(token_id=941, new_owner='0x53201b44e37eec44e97ea0029e16558e8d974fdf', old_owner='0x4cd220244f870977dedc4f29a8684f2a277f1262', tx_hash='0x9a90c463c7db110529844a9c6cd91e15194e38da12f40d2e782a1dccbeb9ddcd', amount=1),
TransferData(token_id=994, new_owner='0x114e6de851c6204d6d0de861d402ef262fb216c4', old_owner='0xbfe5dbe545394e841bc93a59da81673d19101ec1', tx_hash='0x2978d02473e1e82b931488b15db9f588a1618e2d5d730cf8893c0dceea8972b6', amount=1)
]

@transaction.atomic
def fingering():
    for data in data_list:
        print(data.tx_hash)
        handler = HandlerTransferBurn(Network.objects.first(), '', None, None)
        token = handler.get_buyable_token(
            token_id=data.token_id,
            collection=collection,
        )
        new_owner = handler.get_owner(data.new_owner)
        old_owner = handler.get_owner(data.old_owner)
        if TokenHistory.objects.filter(token__internal_id=data.token_id, tx_hash=data.tx_hash).exists():
            print("already exists")
        else:
            handler.transfer_event(
                token=token,
                tx_hash=data.tx_hash,
                token_id=data.token_id,
                new_owner=new_owner,
                old_owner=old_owner,
                amount=data.amount,
            )
            print("history created")
        handler.ownership_quantity_update(
            token=token,
            old_owner=old_owner,
            new_owner=new_owner,
            amount=data.amount,
        )
        print('owner changed')

fingering()
