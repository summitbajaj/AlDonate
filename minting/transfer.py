from algosdk import account, transaction
from algosdk.v2client import algod
from algosdk import mnemonic


# Create a new algod client, configured to connect to our local sandbox
algod_address = "http://localhost:4001"
algod_token = "a" * 64
algod_client = algod.AlgodClient(algod_token, algod_address)

sender_mnemonic = "mom lottery uniform olive visa occur garlic artefact minimum reward custom legend suit stock install leg doctor favorite retreat cart all exact camp able cute"


print ("░██████╗██╗░░░██╗██████╗░██████╗░██╗░░░░░██╗███████╗██████╗░")
print("██╔════╝██║░░░██║██╔══██╗██╔══██╗██║░░░░░██║██╔════╝██╔══██╗")
print("╚█████╗░██║░░░██║██████╔╝██████╔╝██║░░░░░██║█████╗░░██████╔╝")
print("░╚═══██╗██║░░░██║██╔═══╝░██╔═══╝░██║░░░░░██║██╔══╝░░██╔══██╗")
print("██████╔╝╚██████╔╝██║░░░░░██║░░░░░███████╗██║███████╗██║░░██║")
print("╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝░░░░░╚══════╝╚═╝╚══════╝╚═╝░░╚═╝")

print("████████╗██████╗░░█████╗░███╗░░██╗░██████╗░█████╗░░█████╗░████████╗██╗░█████╗░███╗░░██╗")
print("╚══██╔══╝██╔══██╗██╔══██╗████╗░██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗████╗░██║")
print("░░░██║░░░██████╔╝███████║██╔██╗██║╚█████╗░███████║██║░░╚═╝░░░██║░░░██║██║░░██║██╔██╗██║")
print("░░░██║░░░██╔══██╗██╔══██║██║╚████║░╚═══██╗██╔══██║██║░░██╗░░░██║░░░██║██║░░██║██║╚████║")
print("░░░██║░░░██║░░██║██║░░██║██║░╚███║██████╔╝██║░░██║╚█████╔╝░░░██║░░░██║╚█████╔╝██║░╚███║")
print("░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝╚═════╝░╚═╝░░╚═╝░╚════╝░░░░╚═╝░░░╚═╝░╚════╝░╚═╝░░╚══╝")

print("")
print("")
print("")

print("Enter supplier's public address to transfer to: ")
print("")
print("")

receiver = input()
# receiver = "ZVOU4DSUBM74XKLLPW4AUCUG2E7BJ2AQVE7JJCUUFWLLJ5NKW6DQHSXBNM"

def charity_to_supplier(sender_mnemonic,receiver):
    # Your Algorand node settings (replace with your own values)
    ALGOD_ADDRESS = "http://localhost:4001"
    ALGOD_TOKEN = "a" * 64

    # Sender and receiver addresses (replace with your own values)

    approved_wallets = ["A6PBGDL3XFYJT3GLWOS2W7QCUA33BP5IO3AVKLJOZ4LUKRNNTP2PQWQGCA"]


    approved_wallets1 = ["S5EEOYBI6FDZT6AF6O342CJEMX3JOO5J2KLX6ST3JOGKDKMBYGDHZYJA6E"] #to show if wallet not approved


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
        # message = "50 USD sent for the purchase of food to be sent for Turkiye Earthquake relief"
        message = input("Add message to be tied to this transaction: ")
        print("")

        # Convert the message to bytes
        note = message.encode()

        print(note)

        # Create the transaction
        txn = transaction.PaymentTxn(account.address_from_private_key(mnemonic.to_private_key(sender_mnemonic)), params, receiver, 1000, None, note)

        # Sign the transaction
        signed_txn = txn.sign(sender_private_key)

        # Send the transaction
        txid = algod_client.send_transaction(signed_txn)
        print("Sending...")
        print("")
        print("Transaction ID:", txid)

charity_to_supplier(sender_mnemonic,receiver)

