import pyzxing

def scan_barcode_local(image_path: str):
    """
    Detect and decode barcodes from an image using pyzxing (offline, cross-platform).
    """
    reader = pyzxing.BarCodeReader()
    results = reader.decode(image_path)

    if not results:
        print("No barcode detected.")
        return None

    data = results[0].get("raw", None)
    print(f"Detected barcode: {data}")
    return data
