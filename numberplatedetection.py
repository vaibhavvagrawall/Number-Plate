import pytesseract
import cv2
import mysql.connector
from datetime import datetime, timedelta
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
<<<<<<< HEAD
    password="bANSAL1809",
    database="parkinglot"
=======
    password="**********",
    database="parkinglot" # Database Name
>>>>>>> 9541ed78ca33706c18ea1fe69821233cb5fac030
)
cursor = conn.cursor()

def check_plate_in_entry(plate):
    cursor.execute("SELECT * FROM ParkingLog WHERE EntryPlate = %s AND ExitPlate IS NULL", (plate,))
    return cursor.fetchone()

def add_entry_plate(plate):
    current_time = datetime.now()
    cursor.execute("INSERT INTO ParkingLog (EntryPlate, Date, EntryTimestamp) VALUES (%s, %s, %s)", 
                   (plate, current_time.date(), current_time))
    conn.commit()
    print(f"Car with plate '{plate}' can enter.")

def update_exit_plate(plate):
    current_time = datetime.now()
    
    cursor.execute("SELECT EntryTimestamp FROM ParkingLog WHERE EntryPlate = %s AND ExitPlate IS NULL", (plate,))
    entry_time = cursor.fetchone()[0]

    total_duration = current_time - entry_time
    total_hours = total_duration.total_seconds() / 3600

    amount = total_hours * 100 

    cursor.execute("""UPDATE ParkingLog
                      SET ExitPlate = %s, ExitTimestamp = %s, TotalDuration = %s, AmountPaid = %s
                      WHERE EntryPlate = %s AND ExitPlate IS NULL""",
                   (plate, current_time, total_duration, amount, plate))
    conn.commit()

    print(f"Car with plate '{plate}' is exiting. Payment due: {amount:.2f} INR")
    
    while True:
        payment_confirmed = input("Is payment done? (yes/no): ").strip().lower()
        if payment_confirmed == 'yes':
            print("Car can exit.")
            break
        elif payment_confirmed == 'no':
            print("Waiting for payment...")
        else:
            print("Please enter 'yes' or 'no'.")

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
    cursor.close()
    conn.close()
    cv2.destroyAllWindows()
