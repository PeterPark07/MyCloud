import os
from flask import Flask, request, render_template, redirect
from database import log
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded file
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index'))
