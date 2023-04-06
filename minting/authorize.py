import base64
from typing import Tuple
from algosdk import mnemonic, transaction, account
from algosdk.v2client import algod
from pyteal import *


def donation_escrow(benefactor):

    # Getting AppID
    AppID = AppParamObject
    # Getting Minimum Allowed Fee
    Fee = Global.min_txn_fee()

    program = And(
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address(),
        Txn.fee() <= Fee,
        Or(
            And(
                Txn.type_enum() == TxnType.Payment,
                Txn.receiver() == Addr(benefactor),
            ),
            And(
                Txn.type_enum() == TxnType.AssetConfig,
                Txn.config_asset_total()==Int(1),
                Txn.config_asset_unit_name()==Bytes("Don")
                # ensure nft is the logo of the charity
                # Txn.config_asset_url()
            ),
            And(
                Txn.type_enum() == TxnType.AssetTransfer,

            ),
            And(
                Txn.type_enum() == TxnType.AssetFreeze,
            )
        )
    )

    return compileTeal(program, Mode.Signature, version=5)


# user declared account mnemonics
benefactor_mnemonic = "visit tiger car apple produce kingdom next wrap drum clean review rifle laugh tube sausage target cave gold already tissue comfort dove cart absorb twice"
sender_mnemonic = "burden cargo fever spirit loop oxygen brush trouble human mistake pigeon gloom shiver shop above kid fork depth never elbow junior throw gallery above room"


# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# helper function to compile program source
def compile_smart_signature(
    client: algod.AlgodClient, source_code: str
) -> Tuple[str, str]:
    compile_response = client.compile(source_code)
    return compile_response["result"], compile_response["hash"]

def payment_transaction(
    creator_mnemonic: str, amt: int, rcv: str, algod_client: algod.AlgodClient
) -> dict:
    creator_pk = mnemonic.to_private_key(creator_mnemonic)
    creator_address = account.address_from_private_key(creator_pk)

    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(creator_address, params, rcv, amt)
    signed = unsigned_txn.sign(creator_pk)

    txid = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, txid, 5)
    return pmtx


# for minting nft
def mint_nft(encoded_program: str, algod_client: algod.AlgodClient):
    sp = algod_client.suggested_params()
    # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)

    # define NFT asset parameters
    txn = transaction.AssetConfigTxn(
        sender=lsig.address(),
        sp=sp,
        default_frozen=False,
        unit_name="Don",
        asset_name="NHI ENCRYPT NFT",
        manager=lsig.address(),
        reserve=lsig.address(),
        freeze=lsig.address(),
        clawback=lsig.address(),
        url="tinyurl.com/3ezsyafs",
        total=1,
        decimals=0,
    )

    # sign the transaction using the logic signature
    stxn = transaction.LogicSigTransaction(txn, lsig)

    # send the transaction to the network
    tx_id = algod_client.send_transaction(stxn)
    print(f"Transaction ID: {tx_id}")
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
    

    return pmtx

# perform opt in transaction for minted NFT
def opt_in_nft(
    encoded_program: str, asset_id : int, algod_client: algod.AlgodClient,receiver_mnemonic: str
):
    sp = algod_client.suggested_params()
    receiver_pk = mnemonic.to_private_key(receiver_mnemonic)
    receiver_address = account.address_from_private_key(receiver_pk)
    optin_txn = transaction.AssetOptInTxn(
        sender=receiver_address, sp=sp, index=asset_id
    )
    signed_optin_txn = optin_txn.sign(receiver_pk)
    txid = algod_client.send_transaction(signed_optin_txn)
    print(f"Sent opt in transaction with txid: {txid}")

    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")

def transfer_nft_to_donor(
    encoded_program: str, asset_id : int, algod_client: algod.AlgodClient,receiver_mnemonic: str
):
    receiver_pk = mnemonic.to_private_key(receiver_mnemonic)
    receiver_address = account.address_from_private_key(receiver_pk)
    opt_in_nft(encoded_program,asset_id,algod_client,receiver_mnemonic)

    # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)

    # Transfer the newly created NFT from escrow to donor
    txn = transaction.AssetTransferTxn(
        sender=lsig.address(),
        sp=algod_client.suggested_params(),
        receiver=receiver_address,
        amt=1,
        index=asset_id,
    )
    stxn = transaction.LogicSigTransaction(txn, lsig)
    txid = algod_client.send_transaction(stxn)

    print(f"Sent asset transfer transaction with txid: {txid}")
    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")


def freeze_donor_nft(
    encoded_program: str, asset_id : int, algod_client: algod.AlgodClient,receiver_mnemonic: str
):
    receiver_pk = mnemonic.to_private_key(receiver_mnemonic)
    receiver_address = account.address_from_private_key(receiver_pk)

     # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)

    # Create freeze transaction to freeze the asset in acct2 balance
    freeze_txn = transaction.AssetFreezeTxn(
        sender=lsig.address(),
        sp=algod_client.suggested_params(),
        target=receiver_address,
        index=asset_id,
        new_freeze_state=True,
    )

    stxn = transaction.LogicSigTransaction(freeze_txn, lsig)
    txid = algod_client.send_transaction(stxn)
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Sent freeze transaction with txid: {txid}")
    print(f"Result confirmed in round: {results['confirmed-round']}")
    

def lsig_payment_txn(
    encoded_program: str, amt: int, rcv: str, algod_client: algod.AlgodClient
):
    # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)

    # Create transaction with the lsig address as the sender
    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(lsig.address(), params, rcv, amt)

    # sign the transaction using the logic
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 10)
    return pmtx

def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define private keys
    private_key = mnemonic.to_private_key(benefactor_mnemonic)
    receiver_public_key = account.address_from_private_key(private_key)

    print("Compiling Donation Smart Signature......")

    stateless_program_teal = donation_escrow(receiver_public_key)
    escrow_result, escrow_address = compile_smart_signature(
        algod_client, stateless_program_teal
    )

    print("Program:", escrow_result)
    print("LSig Address: ", escrow_address)

    print("Activating Donation Smart Signature......")

    # Activate escrow contract by sending 2 algo and 1000 microalgo for transaction fee from creator
    amt = 100000
    payment_transaction(sender_mnemonic, amt, escrow_address, algod_client)
    
    # Mint NFT using the escrow address
    print("Minting NFT......")
    pmtx = mint_nft(escrow_result,algod_client)
    created_asset = pmtx["asset-index"]

    print("Withdraw from Donation Smart Signature......")
    print(f"NFT Address: {created_asset}")

    # Withdraws 1 ALGO from smart signature using logic signature.
    withdrawal_amt = 10000
    lsig_payment_txn(escrow_result, withdrawal_amt, receiver_public_key, algod_client)

    transfer_nft_to_donor(escrow_result,created_asset,algod_client,sender_mnemonic)
    freeze_donor_nft(escrow_result,created_asset,algod_client,sender_mnemonic)
   



if __name__ == "__main__":
    main()
