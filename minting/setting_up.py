from typing import Dict, Any
import json
from base64 import b64decode
from utils import get_accounts, get_algod_client

from algosdk import transaction, encoding
from algosdk.v2client import algod

# Create a new algod client, configured to connect to our local sandbox
algod_address = "http://localhost:4001"
algod_token = "a" * 64
algod_client = algod.AlgodClient(algod_token, algod_address)

algod_client = get_algod_client()
accts = get_accounts()

acct1 = accts.pop()
private_key, address = acct1.private_key, acct1.address

acct2 = accts.pop()
address2 = acct2.address

# example: ALGOD_FETCH_ACCOUNT_INFO
account_info: Dict[str, Any] = algod_client.account_info(address)
print(f"Account balance: {account_info.get('amount')} microAlgos")
# example: ALGOD_FETCH_ACCOUNT_INFO

# metadata
metadata_dict = {
    "name": "Habibi wallahi",
    "description": "This is an NFT created using Algorand",
    "image": "tinyurl.com/3ezsyafs"
}

# metadata_bytes = encoding.msgpack.packb(metadata_dict, use_bin_type=True)
# meta = encoding.checksum(metadata_bytes)
my_str = "Z0FBQUFBQmtLWndHa05iTmR3cHhQUDFK"
my_bytes = encoding.checksum(my_str.encode())
print(my_bytes)

# Account 1 creates an asset called `rug` with a total supply
# of 1000 units and sets itself to the freeze/clawback/manager/reserve roles
sp = algod_client.suggested_params()
txn = transaction.AssetConfigTxn(
    sender=acct2.address,
    sp=sp,
    default_frozen=False,
    unit_name="SAH",
    asset_name="NHI WITH ENCRYPT NFT",
    manager=acct2.address,
    reserve=acct2.address,
    freeze=acct2.address,
    clawback=acct2.address,
    url="tinyurl.com/3ezsyafs",
    total=1,
    decimals=0,
    metadata_hash= my_bytes,
)

# Sign with secret key of creator
stxn = txn.sign(acct2.private_key)
# Send the transaction to the network and retrieve the txid.
txid = algod_client.send_transaction(stxn)
print(f"Sent asset create transaction with txid: {txid}")
# Wait for the transaction to be confirmed
results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")

# grab the asset id for the asset we just created
created_asset = results["asset-index"]
print(f"Asset ID created: {created_asset}")