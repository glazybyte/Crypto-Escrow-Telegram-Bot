import struct
import hashlib
import base58
import bech32

def hash256(data):
    """Double SHA256 hash function."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def decode_varint(data, offset):
    """Decodes a Bitcoin varint and returns the value and new offset."""
    first_byte = data[offset]
    if first_byte < 0xfd:
        return first_byte, offset + 1
    elif first_byte == 0xfd:
        return struct.unpack("<H", data[offset + 1:offset + 3])[0], offset + 3
    elif first_byte == 0xfe:
        return struct.unpack("<I", data[offset + 1:offset + 5])[0], offset + 5
    else:
        return struct.unpack("<Q", data[offset + 1:offset + 9])[0], offset + 9

def decode_script(script):
    """Attempts to decode a Litecoin scriptPubKey into an address."""
    if len(script) == 25 and script[:3] == b"\x76\xa9\x14" and script[-2:] == b"\x88\xac":
        # P2PKH (Pay-to-PubKey-Hash)
        pubkey_hash = script[3:-2]
        return base58.b58encode_check(b"\x30" + pubkey_hash).decode()  # Litecoin P2PKH prefix: 0x30
    elif len(script) == 23 and script[:2] == b"\xa9\x14" and script[-1:] == b"\x87":
        # P2SH (Pay-to-Script-Hash)
        script_hash = script[2:-1]
        return base58.b58encode_check(b"\x32" + script_hash).decode()  # Litecoin P2SH prefix: 0x32
    elif len(script) == 22 and script[:2] == b"\x00\x14":
        # P2WPKH (Pay-to-Witness-PubKey-Hash)
        return bech32.encode("ltc", 0, script[2:])
    elif len(script) == 34 and script[:2] == b"\x00\x20":
        # P2WSH (Pay-to-Witness-Script-Hash)
        return bech32.encode("ltc", 0, script[2:])
    return "Unknown script"

def decode_transaction(hex_tx):
    """Decodes a raw Litecoin transaction hex into inputs and outputs."""
    data = bytes.fromhex(hex_tx)
    offset = 0

    version = struct.unpack("<I", data[offset:offset + 4])[0]
    offset += 4

    num_inputs, offset = decode_varint(data, offset)
    inputs = []
    for _ in range(num_inputs):
        txid = data[offset:offset + 32][::-1].hex()
        vout = struct.unpack("<I", data[offset + 32:offset + 36])[0]
        offset += 36

        script_len, offset = decode_varint(data, offset)
        script_sig = data[offset:offset + script_len].hex()
        offset += script_len

        sequence = struct.unpack("<I", data[offset:offset + 4])[0]
        offset += 4

        inputs.append({
            "txid": txid,
            "vout": vout,
            "scriptSig": script_sig,
            "sequence": sequence
        })

    num_outputs, offset = decode_varint(data, offset)
    outputs = []
    for _ in range(num_outputs):
        value = struct.unpack("<Q", data[offset:offset + 8])[0] / 1e8  # Convert satoshis to LTC
        offset += 8

        script_len, offset = decode_varint(data, offset)
        script_pubkey = data[offset:offset + script_len]
        offset += script_len

        address = decode_script(script_pubkey)

        outputs.append({
            "value": value,
            "address": address
        })

    locktime = struct.unpack("<I", data[offset:offset + 4])[0]

    return {
        "version": version,
        "inputs": inputs,
        "outputs": outputs,
        "locktime": locktime
    }

# Example usage
raw_tx = "010000000001018e1d7d0c667678186270941a613b408e776e180fe31f80010b6af7c4d3de832d0000000000ffffffff0184e1260000000000160014000000000000000000000000000000000000000002473044022046e66626ff392c1719bd4951fb6497f22328fbb2c9cfaaf1dd753b6776396d2202204ebd61780d37d0e18c8a38f808a0ab2d737ec0578af581be0fdd956e414c4d25012102e30eb88f49212c82fd237eb040f775852eb2b4fe5b0c9e809cc24f94976d8e3000000000"  # Replace with real transaction hex
decoded = decode_transaction(raw_tx)
print(decoded)
