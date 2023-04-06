import base64
from typing import Tuple
from algosdk import mnemonic, transaction, account
from algosdk.v2client import algod
from pyteal import *

print("█░█░█ █▀▀ █░░ █▀▀ █▀█ █▀▄▀█ █▀▀   ▀█▀ █▀█   ▄▀█ █░░ █▀▄ █▀█ █▄░█ ▄▀█ ▀█▀ █▀▀")
print("▀▄▀▄▀ ██▄ █▄▄ █▄▄ █▄█ █░▀░█ ██▄   ░█░ █▄█   █▀█ █▄▄ █▄▀ █▄█ █░▀█ █▀█ ░█░ ██▄")

txn_history = {}


def donation_escrow(benefactor):

    # Getting AppID
    # AppID = AppParamObject
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
                Txn.config_asset_total() == Int(1),
                Txn.config_asset_unit_name() == Bytes("AlD")
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
benefactor_mnemonic = "mom lottery uniform olive visa occur garlic artefact minimum reward custom legend suit stock install leg doctor favorite retreat cart all exact camp able cute"
sender_mnemonic = "shoe onion turkey shallow belt drop owner merit eager reflect radio gravity stone eyebrow busy dolphin verb bonus load unit engage young decrease ability fame"


# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "http://localhost:4001"
algod_token = "a" * 64

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
    return txid, pmtx["txn"]["txn"]


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
        unit_name="AlD",
        asset_name="AlDonate NFT",
        manager=lsig.address(),
        reserve=lsig.address(),
        freeze=lsig.address(),
        clawback=lsig.address(),
        url="https://tinyurl.com/mt3yzhz4",
        total=1,
        decimals=0,
    )

    # sign the transaction using the logic signature
    stxn = transaction.LogicSigTransaction(txn, lsig)

    # send the transaction to the network
    tx_id = algod_client.send_transaction(stxn)
    print("")
    print(f"Minting Transaction ID: {tx_id}")
    print("")
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)

    return pmtx

# perform opt in transaction for minted NFT


def opt_in_nft(
    encoded_program: str, asset_id: int, algod_client: algod.AlgodClient, receiver_mnemonic: str
):
    sp = algod_client.suggested_params()
    receiver_pk = mnemonic.to_private_key(receiver_mnemonic)
    receiver_address = account.address_from_private_key(receiver_pk)
    optin_txn = transaction.AssetOptInTxn(
        sender=receiver_address, sp=sp, index=asset_id
    )
    signed_optin_txn = optin_txn.sign(receiver_pk)
    txid = algod_client.send_transaction(signed_optin_txn)
    print("")
    print(f"Opting in your wallet to receive NFT: {txid}")

    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")
    print("")


def transfer_nft_to_donor(
        encoded_program: str, asset_id: int, algod_client: algod.AlgodClient, receiver_mnemonic: str, id, txn):
    receiver_pk = mnemonic.to_private_key(receiver_mnemonic)
    receiver_address = account.address_from_private_key(receiver_pk)
    opt_in_nft(encoded_program, asset_id, algod_client, receiver_mnemonic)

    # Create an lsig object using the compiled, b64 encoded program
    program = base64.b64decode(encoded_program)
    lsig = transaction.LogicSigAccount(program)
    note = f"Transaction: {id}, Amount: {txn['amt']}, Fee: {txn['fee']}".encode(
    )
    # Transfer the newly created NFT from escrow to donor
    txn = transaction.AssetTransferTxn(
        sender=lsig.address(),
        sp=algod_client.suggested_params(),
        receiver=receiver_address,
        amt=1,
        index=asset_id,
        note=note
    )
    stxn = transaction.LogicSigTransaction(txn, lsig)
    txid = algod_client.send_transaction(stxn)

    print(f"Sent asset transfer transaction with txid: {txid}")
    # Wait for the transaction to be confirmed
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Result confirmed in round: {results['confirmed-round']}")


def freeze_donor_nft(
    encoded_program: str, asset_id: int, algod_client: algod.AlgodClient, receiver_mnemonic: str
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
    print("")
    print(f"Sent freeze transaction with txid: {txid}")
    print(f"Result confirmed in round: {results['confirmed-round']}")
    print("")
    print("Congrats! NFT has been transferred to you! Note: You will not be able to transfer this asset")


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
    # receiver_public_key = account.address_from_private_key(private_key)

    print("")
    print("")
    print("")
    print("Thank you for your donation! Which charity will you like to send the donation to? Key in the number:")
    print("")
    print("")

    choice = 0

    while (choice != 3):

        print("1: NKF  || Onboarded suppliers: - Penny Appeal(Turkey Food Donation), - Ikea Foundation(Turkey Shelters)")
        print("2: WWF  || Onboarded suppliers: - Ghana Stores(Ghana Food Donation)")
        print("3: To exit this application")
        print("4: View your Donations")
        choice = int(input())
        charity = ""

        if choice == 1:
            print("sending donation to NKF")
            charity = "NKF"
            receiver_public_key = 'S5EEOYBI6FDZT6AF6O342CJEMX3JOO5J2KLX6ST3JOGKDKMBYGDHZYJA6E'

        elif choice == 2:
            print("sending donation to WWF")
            charity = "WWF"
            receiver_public_key = 'XHT4KIAFOP4626AFLA6GMOMST4QO3AO2XADMIJJOACMFEGT5GLA6LOCLWQ'

        elif choice == 3:
            break

        elif choice == 4:
            for charity, transactions_list in txn_history.items():
                print(f"Transactions for {charity}:")
                for txn in transactions_list:
                    print(f"\tTransaction ID: {txn['txn_id']}")
                    print(f"\tAmount Donated: {txn['amount_donated']}")
                    print(f"\tCertificate ID: {txn['certificate_id']}\n")

            continue

        else:
            print("Sending donation to NKF")
            charity = "NKF"
            receiver_public_key = 'S5EEOYBI6FDZT6AF6O342CJEMX3JOO5J2KLX6ST3JOGKDKMBYGDHZYJA6E'

        print("")
        print("Compiling Donation Smart Signature......")
        print("")
        stateless_program_teal = donation_escrow(receiver_public_key)
        escrow_result, escrow_address = compile_smart_signature(
            algod_client, stateless_program_teal
        )

        print("Program:", escrow_result)
        print("LSig Address: ", escrow_address)
        print("")
        print("Activating Donation Smart Signature......")

        # Activate escrow contract by sending 2 algo and 1000 microalgo for transaction fee from creator
        amt = 100000
        id, txn = payment_transaction(
            sender_mnemonic, amt, escrow_address, algod_client)

        if charity not in txn_history.keys():
            txn_history[charity] = []

        # Mint NFT using the escrow address
        print("Thank you for your donation, Minting NFT......")
        pmtx = mint_nft(escrow_result, algod_client)
        created_asset = pmtx["asset-index"]

        txn_history[charity].append(
            {"txn_id": id, "amount_donated": amt, "certificate_id": created_asset})

        print("")
        print("Withdrawing from Donation Smart Signature......")
        print(f"NFT Address: {created_asset}")

        # Withdraws 1 ALGO from smart signature using logic signature.
        withdrawal_amt = 10000
        lsig_payment_txn(escrow_result, withdrawal_amt,
                         receiver_public_key, algod_client)

        transfer_nft_to_donor(escrow_result, created_asset,
                              algod_client, sender_mnemonic, id, txn)
        freeze_donor_nft(escrow_result, created_asset,
                         algod_client, sender_mnemonic)


if __name__ == "__main__":
    main()

