import pytesseract
import cv2
import requests
from datetime import datetime, timedelta
import re

# ThingSpeak credentials
THINGSPEAK_READ_API_KEY = 'XBGMMI20JY2E72I4'
THINGSPEAK_WRITE_API_KEY = 'OB7IOZE1SV5H78JG'
THINGSPEAK_CHANNEL_ID = '2612724'
THINGSPEAK_URL = f'https://api.thingspeak.com/channels/2612724/fields/1.json'

# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def fetch_recent_entries():
    """Fetch the recent entries from ThingSpeak."""
    url = f"{THINGSPEAK_URL}?api_key={THINGSPEAK_READ_API_KEY}&results=100"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve data from ThingSpeak")
        return None

def check_plate_in_entry(plate):
    """Check if the plate has an entry and no exit recorded."""
    data = fetch_recent_entries()
    if data and 'feeds' in data:
        for entry in data['feeds']:
            entry_plate = entry.get('field1') 
            exit_plate = entry.get('field3')
            if entry_plate == plate and not exit_plate:
                entry_time_str = entry.get('field2')
                entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
                return entry.get('entry_id'), entry_time
    return None

def send_to_thingspeak(entry_plate, entry_time, exit_plate=None, exit_time=None, total_duration=None, amount_paid=None):
    """Send entry or exit data to ThingSpeak."""
    data = {
        'api_key': THINGSPEAK_WRITE_API_KEY,
        'field1': entry_plate,
        'field2': entry_time.strftime('%Y-%m-%d %H:%M:%S') if entry_time else None,
        'field3': exit_plate,
        'field4': exit_time.strftime('%Y-%m-%d %H:%M:%S') if exit_time else None,
        'field5': str(total_duration) if total_duration else None,
        'field6': amount_paid if amount_paid else None
    }
    response = requests.post(f'https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_API_KEY}', data=data)
    if response.status_code == 200:
        print("Data successfully sent to ThingSpeak")
    else:
        print("Failed to send data to ThingSpeak")

def add_entry_plate(plate):
    """Add the entry plate to ThingSpeak."""
    current_time = datetime.now()
    send_to_thingspeak(entry_plate=plate, entry_time=current_time)

def update_exit_plate(plate):
    """Update the exit information for the given plate."""
    current_time = datetime.now()

    entry_record = check_plate_in_entry(plate)
    if entry_record:
        entry_id, entry_time = entry_record

        total_duration = current_time - entry_time
        total_hours = total_duration.total_seconds() / 3600
        amount = total_hours * 100

        send_to_thingspeak(entry_plate=plate, entry_time=entry_time, exit_plate=plate,
                           exit_time=current_time, total_duration=total_duration, amount_paid=amount)

def is_valid_plate(plate):
    plate = plate.replace(" ", "").replace("\n", "").upper()
    plate = re.sub(r'^\(IND\)', '', plate).strip()
    print(f"Normalized Plate: '{plate}'")
    pattern = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"
    return re.match(pattern, plate)

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open video")

counter = 0
last_detection_time = datetime.now() - timedelta(seconds=10)

try:
    while True:
        ret, frame = cap.read()
        counter += 1
        if (counter % 20) == 0:

            processed_frame = preprocess_image(frame)

            imgchar = pytesseract.image_to_string(processed_frame).strip()
            imgchar = re.sub(r'[^A-Z0-9]', '', imgchar)
            print(f"Detected Text: '{imgchar}'")

            if (datetime.now() - last_detection_time).total_seconds() >= 10:
                if imgchar:
                    if is_valid_plate(imgchar):
                        print("Valid Plate Detected:", imgchar)

                        plate_record = check_plate_in_entry(imgchar)
                        
                        if plate_record:
                            update_exit_plate(imgchar)
                        else:
                            add_entry_plate(imgchar)

                        last_detection_time = datetime.now()
                    else:
                        print("Invalid plate detected.")

            cv2.imshow('Number Plate Detection', frame)

            if cv2.waitKey(2) & 0xFF == ord('q'):
                break

finally:
    cap.release()
    cv2.destroyAllWindows()