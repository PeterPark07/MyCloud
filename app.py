import os
from flask import Flask, request, render_template, redirect
from database import log
import time
import requests

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded file
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# PixelDrain API endpoint
PIXELDRAIN_API_URL = 'https://pixeldrain.com/api/file'
PIXELDRAIN_API_INFO_URL = 'https://pixeldrain.com/api/file/{}/info'

@app.route('/')
def index():
    # Retrieve all files from the collection
    files = log.find()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        # Save the uploaded file to the uploads folder
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Upload the file to PixelDrain
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(PIXELDRAIN_API_URL, files=files)
        result = response.json()
        
        # Check if the upload was successful
        if result['success']:
            file_id = result['id']
            info_response = requests.get(PIXELDRAIN_API_INFO_URL.format(file_id))
            info_result = info_response.json()            
            log_entry = {
                "file_id": file_id,
                "file_name": filename,
                "file_size": info_result["size"],
                "mime_type": info_result["mime_type"],
                "timestamp": info_result["date_upload"]
            }
            log.insert_one(log_entry)
            return f'File uploaded successfully.'
        else:
            return f'Failed to upload file to PixelDrain: {response.status_code} \n {str(result)}'

if __name__ == '__main__':
    app.run(debug=True)
