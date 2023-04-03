import base64
from typing import Tuple
from algosdk import mnemonic, transaction, account
from algosdk.v2client import algod
from pyteal import *

# example: LSIG_SIMPLE_ESCROW
def donation_escrow(benefactor):
    Fee = Int(1000)

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


# # example: LSIG_SIMPLE_ESCROW

# # example: LSIG_SIMPLE_ESCROW_INIT
# charity_addr = "E7KMYV5NKFHLT2XKSBMPMD7LQ5OJEBV7CMPPQBWBK4JHSXZTLWODL2XACU"
# teal_program = donation_escrow(charity_addr)
# # example: LSIG_SIMPLE_ESCROW_INIT

# # Output the TEAL program to a file
# with open("test.teal", "w") as f:
#     f.write(teal_program)

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


    print("Minting NFT......")

    # Mint NFT using the escrow address
    pmtx = mint_nft(escrow_result,algod_client)
    created_asset = pmtx["asset-index"]

    print("Withdraw from Donation Smart Signature......")
    print(f"NFT Address: {created_asset}")

    # Withdraws 1 ALGO from smart signature using logic signature.
    withdrawal_amt = 10000
    lsig_payment_txn(escrow_result, withdrawal_amt, receiver_public_key, algod_client)


    sp = algod_client.suggested_params()
    # Create opt-in transaction
    # asset transfer from me to me for asset id we want to opt-in to with amt==0
    optin_txn = transaction.AssetOptInTxn(
        sender=receiver_public_key, sp=sp, index=created_asset
    )
    signed_optin_txn = optin_txn.sign(private_key)
    txid = algod_client.send_transaction(signed_optin_txn)
    print(f"Sent opt in transaction with txid: {txid}")

    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")

    # Transfer the newly created NFT from acct2 to acct1
    txn = transaction.AssetTransferTxn(
        sender=escrow_address,
        sp=algod_client.suggested_params(),
        receiver=receiver_public_key,
        amt=1,
        index=created_asset,
    )

    program = base64.b64decode(escrow_result)
    lsig = transaction.LogicSigAccount(program)
    stxn = transaction.LogicSigTransaction(txn, lsig)
    txid = algod_client.send_transaction(stxn)

    print(f"Sent asset transfer transaction with txid: {txid}")
    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")

    # Create freeze transaction to freeze the asset in acct2 balance
    freeze_txn = transaction.AssetFreezeTxn(
        sender=escrow_address,
        sp=algod_client.suggested_params(),
        target=receiver_public_key,
        index=created_asset,
        new_freeze_state=True,
    )

    stxn = transaction.LogicSigTransaction(freeze_txn, lsig)
    txid = algod_client.send_transaction(stxn)
    print(f"Sent freeze transaction with txid: {txid}")

    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")



if __name__ == "__main__":
    main()
