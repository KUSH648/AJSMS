import base64
import numpy as np
import cv2

def decode_barcode_from_base64(image_b64):
    if not image_b64:
        return None
        
    try:
        # Strip metadata header if present
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]
            
        img_data = base64.b64decode(image_b64)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
            
        # Try BarcodeDetector (OpenCV 4.8+)
        try:
            # We use QRCodeDetector as well, in case it's a QR code
            qr_detector = cv2.QRCodeDetector()
            val, pts, straight_qrcode = qr_detector.detectAndDecode(img)
            if val:
                return val
        except Exception as qr_err:
            print(f"QR Detector error: {qr_err}")
            
        # Try OpenCV barcode detector if available
        try:
            if hasattr(cv2, 'barcode_BarcodeDetector'):
                detector = cv2.barcode_BarcodeDetector()
                ok, decoded_info, decoded_type, corners = detector.detectAndDecode(img)
                if ok and decoded_info:
                    # Return first decoded barcode
                    return decoded_info[0]
        except Exception as bc_err:
            print(f"Barcode Detector error: {bc_err}")
            
        # Optional basic edge/contour scanning could go here, but usually OpenCV detectors are enough
        return None
        
    except Exception as e:
        print(f"Error decoding barcode from base64: {e}")
        return None
