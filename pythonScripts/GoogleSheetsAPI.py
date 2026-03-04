from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv
import os

def main(sheetID, rangeVal, filename_base):
    # service account key file
    SERVICE_ACCOUNT_FILE = os.path.join(".", "data", "long-equinox-460223-f6-db89ecf412ff.json")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # credentials and service
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    # values
    result = sheet.values().get(spreadsheetId=sheetID, range=rangeVal).execute()
    values = result.get('values', [])

    # notes using batchGet
    sheet_metadata = sheet.get(
        spreadsheetId=sheetID,
        ranges=[rangeVal],
        fields="sheets(data(rowData(values(note))))"
    ).execute()

    # notes
    note_data = []
    try:
        rows = sheet_metadata['sheets'][0]['data'][0]['rowData']
        for row in rows:
            note_row = []
            for cell in row.get('values', []):
                note_row.append(cell.get('note', ''))  # Get note if exists, else ''
            note_data.append(note_row)
    except KeyError:
        print("No notes found.")
    

    if not values:
        print('No data found.')
        return ''

    cleaned_values = [
        [cell.replace("’", "'") if isinstance(cell, str) else cell for cell in row]
        for row in values
    ]

    # save values
    with open(f"{filename_base}_values.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(cleaned_values)
    
    if(note_data != []):
        with open(f"{filename_base}_notes.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(note_data)

    print(f"Data and notes saved successfully to {filename_base}.")
    return cleaned_values, note_data

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current script directory
    os.chdir("..")  # go one level up to root
    print("starting!")
    main(
        "1qJ1Pkeqy7DTlGwDymSalzyUXKJZfYPIi6r3Qvq7KXHE",
        'Boost Data!A1:H1050',
        os.path.join(".", "data", "boostdata")
    )
