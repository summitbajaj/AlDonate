from algosdk import account, transaction
from algosdk.v2client import algod
from algosdk import mnemonic

sender_mnemonic = "opera track ladder fury gospel merit citizen glass window assist citizen winner sound actress thunder base lock cheap axis vanish impact lobster distance abstract crane"
receiver = "A6PBGDL3XFYJT3GLWOS2W7QCUA33BP5IO3AVKLJOZ4LUKRNNTP2PQWQGCA"

def charity_to_supplier(sender_mnemonic,receiver):
    # Your Algorand node settings (replace with your own values)
    ALGOD_ADDRESS = "http://localhost:4001"
    ALGOD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    # Sender and receiver addresses (replace with your own values)

    approved_wallets = ["A6PBGDL3XFYJT3GLWOS2W7QCUA33BP5IO3AVKLJOZ4LUKRNNTP2PQWQGCA"]


    if receiver not in approved_wallets:
        print("Transaction unsucessful, wallet not approved")

    else: 
    # Create an Algod client
        algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

        # Recover the private key from the mnemonic
        sender_private_key = mnemonic.to_private_key(sender_mnemonic)

        # Get the suggested transaction parameters
        params = algod_client.suggested_params()

        # Define the note (message) as a string
        message = "50 USD sent for the purchase of food to be sent for Turkiye Earthquake relief"

        # Convert the message to bytes
        note = message.encode()

        print(note)

        # Create the transaction
        txn = transaction.PaymentTxn(mnemonic.to_public_key(sender_mnemonic), params, receiver, 100000, None, note)

        # Sign the transaction
        signed_txn = txn.sign(sender_private_key)

        # Send the transaction
        txid = algod_client.send_transaction(signed_txn)
        print("Transaction ID:", txid)

charity_to_supplier(sender_mnemonic,receiver)
