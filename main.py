from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import pytesseract
import pandas as pd
import numpy as np
import io

app = FastAPI()

# Set the path to the Tesseract executable (replace with your Tesseract installation path)
#pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
@app.route('/')
def extract_text_from_image(img):
    try:
        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_invoice_text(text):
    # Add your logic to process the extracted text
    # This could involve regular expressions, string manipulation, etc.
    # For this example, let's assume the text is comma-separated values
    lines = text.split('\n')
    data = [line.split(',') for line in lines if line.strip()]
    return data

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        # Read the image file
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # Extract text from the image
        extracted_text = extract_text_from_image(img)

        if extracted_text:
            # Process the extracted text
            processed_data = process_invoice_text(extracted_text)

            # Determine the maximum number of columns in the processed data
            max_columns = max(len(row) for row in processed_data)

            # Fill missing values with a placeholder
            processed_data = [row + [''] * (max_columns - len(row)) for row in processed_data]

            # Create a DataFrame with fixed column names
            df = pd.DataFrame(processed_data, columns=[f'Column{i}' for i in range(1, max_columns + 1)])

            # Save to Excel file
            excel_output_path = 'Invoice_output.xlsx'
            df.to_excel(excel_output_path, index=False)

            return {"message": "File processed successfully", "excel_output_path": excel_output_path}
        else:
            raise HTTPException(status_code=500, detail="Text extraction failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")

# Mount static files (Excel output) for serving through FastAPI
app.mount("/static", StaticFiles(directory="."), name="static")

