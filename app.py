import os
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory, send_file
import uuid
import moviepy.editor as moviepy
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set the upload folder for whatever we upload
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set of allowed extensions
app.config['UPLOAD_EXTENSIONS'] = ['.mp4', '.avi', '.mkv', '.flv', '.webm', '.wmv']

# Set input and output video absolute paths
INPUT_FOLDER_PATH = os.path.join(UPLOAD_FOLDER, "input_videos/")
OUTPUT_FOLDER_PATH = os.path.join(UPLOAD_FOLDER, "output_videos/")


@app.route('/')
@app.route('/home')
@app.route('/<error>')
def home(error=None):
	# global uuid for user
	session['user_uuid'] = str(uuid.uuid4().hex)
	return render_template('home.html', error=error)


'''
	Route that is triggered when the Convert button on "home.html" is clicked and all the client side validation is passed
	This route performs server-side validation, if failed, redirects to home with proper error code and if succeeded
	converts video to requested format and then leads to the "download.html" page
'''
@app.route('/results', methods=['POST'])
def results():

	# Check whether user has visited home page first to get user_uuid before coming to results
	if 'user_uuid' in session:

		file_object = request.files['uploadButton']
		convert_format = request.form['fileFormatSelect']

		# Server Side Validation
		# If failed, then redirect to home with the appropriate error message
		user_filename = file_object.filename

		error_code = server_side_validation(request, user_filename, convert_format)
		if error_code != None:
			return redirect(url_for('home', error=error_code))

		# Generate unique filename for uploaded file
		file_id = str(uuid.uuid4().hex)[:5]

		# Filename = User ID + File ID + "." + Uploaded File Format
		file_format = os.path.splitext(user_filename)[1]
		input_filename = session['user_uuid'] + file_id + file_format
		output_filename = session['user_uuid'] + file_id + convert_format

		# Save video on local machine at given path
		input_filepath = os.path.join(INPUT_FOLDER_PATH, input_filename)
		file_object.save(input_filepath)

		# Function that takes video file path and file format and converts it
		video_converter(input_filepath, convert_format, OUTPUT_FOLDER_PATH)

		return render_template('download.html', filename=output_filename)

	return redirect(url_for('home'))


'''
	Route that sends the converted video for download when the "Download" button on downloads.html page is clicked
'''
@app.route('/download/<filename>', methods=['GET', 'POST'])
def download(filename):
	return send_from_directory(directory=OUTPUT_FOLDER_PATH, filename=filename, as_attachment=True)

'''
	Performs server side validation
	Returns: error_code
	If validation is successful, error_code = None
	Else, error_code would contain the appropriate error code which will be matched with error message in the home.html page
'''
def server_side_validation(request, user_filename, convert_format):
	file_format = os.path.splitext(user_filename)[1]

	error_code = None

	# 1. Is file uploaded
	if user_filename == "":
		# error_code = "No file uploaded"
		error_code = 101

	# 2. Is file in supported format
	elif file_format not in app.config['UPLOAD_EXTENSIONS']:
		# error_code = "The uploaded file format is not supported"
		error_code = 102

	# 3. Is file format and converted format same 
	elif file_format == convert_format:
		# error_code = "File format to convert to should be different than uploaded file format"
		error_code = 103

	# 4. Is file size greater than 10MB
	elif request.content_length > 10 * 1024 * 1024:
		# error_code = "File size should not be greater than 10MB"
		error_code = 104

	return error_code


def video_converter(filepath, extension, output_directory):
	clip = moviepy.VideoFileClip(filepath)

	head, tail = os.path.split(filepath)
	basename = Path(tail).stem  # Gintama.mkv -> Gintama

	output_filename = basename + extension   # Gintama + new_extension
	output_filepath = output_directory + output_filename

	if extension == '.mp4':
		clip.write_videofile(output_filepath)
	elif extension == '.flv':
		clip.write_videofile(output_filepath, codec='libx264')
	else:
		clip.write_videofile(output_filepath, codec='libvpx')










