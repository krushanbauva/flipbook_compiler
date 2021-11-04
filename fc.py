import cv2 as cv
import sys
import os
from PIL import Image

def check_if_file_exists(filename="human_life_span.flip"):
	return os.path.isfile(filename)

def read_properties(filename="human_life_span.flip"):
	properties = []

	if check_if_file_exists(filename) == False:
		print("Couldn't open the properties file. Can you check if it exists and has the required permissions")
		sys.exit(1)

	with open(filename) as f:
		lines = f.readlines()
		properties = [line.strip().split() for line in lines]

	return properties

def create_pdf_from_properties(properties, filename="HLC_flipbook.pdf"):
	image_list = []
	for line in properties:
		start_index = int(line[0])
		end_index = int(line[1])
		image_path = line[2]
		if check_if_file_exists(image_path) == False:
			print("Couldn't open the image file", image_path)
			sys.exit(0)

		temp_image = Image.open(image_path)
		temp_image.convert('RGB')
		for i in range(start_index, end_index+1):
			image_list.append(temp_image)

	temp_image = image_list.pop(0)
	try:
		temp_image.save(filename, save_all=True, append_images=image_list)
	except Exception as e:
		print("error occurred while saving:", e)
		sys.exit(1)

	print("Converted successfully.")

#def create_video_from_properties(properties, filename="HLC_flipbook.pdf"):

def print_help():
	print("Printing help")

def print_version():
	print("Printing version")

def parse_arguments(args):
	l = len(args)
	args = [x.strip() for x in args]
	arguments = {}
	if l == 0:
		print("No arguments supplied")
		sys.exit(1)
	elif l == 1:
		if args[0] in ("-h", "--help"):
			print_help()
			sys.exit(0)
		elif args[0] in ("-v", "--version"):
			print_version()
			sys.exit(0)
		else:
			print("invalid arguments")
			sys.exit(1)
	elif l == 3:
		if args[1] in ("-o", "--output"):
			arguments["properties_file"] = args[0]
			arguments["output_file"] = args[2]
			if args[2].endswith(".pdf"):
				arguments["output_type"] = "pdf"
			elif args[2].endswith(".gif"):
				arguments["output_type"] = "gif"
			elif args[2].endswith(".mp4"):
				arguments["output_type"] = "mp4"
			else:
				print("Unrecognized file type:", args[2])
				sys.exit(1)
	else:
		print("Unrecognized arguments")
		sys.exit(1)

	return arguments


if __name__ == "__main__":
	arguments = parse_arguments(sys.argv[1:])

	properties = read_properties(filename=arguments["properties_file"])
	
	if arguments["output_type"] == "pdf":
		create_pdf_from_properties(properties, filename=arguments["output_file"])
	else:
		print("unrecognized output_type:", arguments["output_type"])
		sys.exit(1)