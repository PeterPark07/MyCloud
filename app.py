import os
from flask import Flask, request, render_template, redirect
from database import log
import time
import requests

import base64





app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded file
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# PixelDrain API endpoint
PIXELDRAIN_API_KEY = 'd224aab0-a8d3-4231-a580-ff8207e6cf42'
PIXELDRAIN_API_URL = 'https://pixeldrain.com/api/file'
PIXELDRAIN_API_INFO_URL = 'https://pixeldrain.com/api/file/{}/info'

# Encode the API key to Base64
auth_string = ":" + PIXELDRAIN_API_KEY
encoded_auth_string = base64.b64encode(auth_string.encode()).decode()



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
            # Set the Authorization header
            headers = {'Authorization': 'Basic ' + encoded_auth_string}

            # Send the request with the updated headers
            response = requests.post(PIXELDRAIN_API_URL, files=files, headers=headers)

        result = response.json()
        print(result)
        # Delete the file from the server after uploading
        os.remove(file_path)
        
        # Check if the upload was successful
        if result['success']:
            file_id = result['id']
            info_response = requests.get(PIXELDRAIN_API_INFO_URL.format(file_id))
            info_result = info_response.json()            
            log_entry = {
                "file_id": file_id,
                "file_name": info_result["name"],
                "file_size": info_result["size"],
                "mime_type": info_result["mime_type"],
                "timestamp": info_result["date_upload"]
            }
            log.insert_one(log_entry)
            return redirect('/')
        else:
            return f'Failed to upload file to PixelDrain: {response.status_code} \n {str(result)}'

@app.route('/log', methods=['POST'])
def log_file():
    file_id = request.data.decode('utf-8')
    print(file_id)
    info_response = requests.get(PIXELDRAIN_API_INFO_URL.format(file_id))
    info_result = info_response.json()            
    log_entry = {
        "file_id": file_id,
        "file_name": info_result["name"],
        "file_size": info_result["size"],
        "mime_type": info_result["mime_type"],
        "timestamp": info_result["date_upload"]
    }
    log.insert_one(log_entry)
    return redirect('/')



@app.route('/delete/file/<file_id>', methods=['POST'])
def delete_file(file_id):
    # Check if the file exists in the database
    file_entry = log.find_one({"file_id": file_id})
    if file_entry:
        # Set the Authorization header with PixelDrain API key
        headers = {'Authorization': 'Basic ' + encoded_auth_string}
        # Send DELETE request to PixelDrain API
        delete_response = requests.delete(PIXELDRAIN_API_URL + '/' + file_id, headers=headers)
        delete_result = delete_response.json()
        if delete_result['success']:
            # Delete the file entry from the database
            log.delete_one({"file_id": file_id})
            return redirect('/')
        else:
            return f'Failed to delete file {delete_response.status_code} \n {str(delete_result)}'


if __name__ == '__main__':
    app.run(debug=True)
