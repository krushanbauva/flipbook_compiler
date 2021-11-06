import cv2 as cv
import sys
import os
import numpy as np
from PIL import Image


def check_if_file_exists(filename):
	return os.path.isfile(filename)


def hex_to_rgb(hex):
	return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))


def delete_frames():
	for root, dirs, files in os.walk("temp", topdown=False):
		for name in files:
			os.remove(os.path.join(root, name))
		for name in dirs:
			os.rmdir(os.path.join(root, name))

	try:
		os.rmdir("temp")
	except OSError as error:
		print("Error occurred while removing directory. Try using rm -rf temp/")


def get_page_property(line):
	if "height" in line:
		height = int(line[line.find("=")+1:line.find("px")].strip())
		return ("height", height)

	if "width" in line:
		width = int(line[line.find("=")+1:line.find("px")].strip())
		return ("width", width)

	if "margin_color" in line:
		margin_color = hex_to_rgb(line[line.find("#")+1:].strip())
		return ("margin_color", margin_color)

	elif "margin" in line:
		line = line[line.find("=")+1:]
		line_arr = [int(x.strip("px")) for x in line.strip().split()]
		if len(line_arr) == 4:
			margin = (line_arr[0], line_arr[1], line_arr[2], line_arr[3])
		elif len(line_arr) == 3:
			margin = (line_arr[0], line_arr[1], line_arr[2], 0)
		elif len(line_arr) == 2:
			margin = (line_arr[0], line_arr[1], 0, 0)
		elif len(line_arr) == 1:
			margin = (line_arr[0], 0, 0, 0)
		return ("margin", margin)


def render_file(filename):
	lines = []

	page_properties = {"height":1920, "width":1080, "margin":(0, 0, 0, 0), "margin_color":(0, 0, 0)}

	if check_if_file_exists(filename) == False:
		print("Couldn't open the properties file.")
		sys.exit(1)

	with open(filename) as f:
		l1 = f.readlines()
		lines = [line.strip() for line in l1]

	i = 0
	while i < len(lines):
		if "[page]" in lines[i]:
			i+=1
			while "[sequence]" not in lines[i]:
				if lines[i] != "":
					line = lines[i]
					(property, value) = get_page_property(line)
					page_properties[property] = value
				i+=1

		elif "[sequence]" in lines[i]:
			i+=1
			while i<len(lines):
				if lines[i] != "":
					frame_description = parse_sequence(lines[i])
					create_frames_from_description(page_properties, frame_description)
				i+=1
	return 0


def fit_image(height, width, position, img, img_path):
	(im_height, im_width, _) = img.shape
	(position_x, position_y) = position
	
	if im_height+position_y <= height and im_width+position_x <= width:
		img = cv.copyMakeBorder(img, position_y, (height-im_height-position_y), position_x, (width-im_width-position_x), cv.BORDER_CONSTANT, value = [0, 0, 0])
	else:
		print("Invalid scaling for the image", img_path)
		sys.exit(1)
	return img


def add_margin(img, margin, margin_color):
	img = cv.copyMakeBorder(img, margin[0], margin[2], margin[3], margin[1], cv.BORDER_CONSTANT, value = [margin_color[0], margin_color[1], margin_color[2]])
	return img


def create_frames_from_description(page_properties, frame_description):
	(start_index, end_index, image_properties) = frame_description
	height = page_properties["height"]
	width = page_properties["width"]
	margin = page_properties["margin"]
	margin_color = page_properties["margin_color"]
	num_frames = end_index-start_index+1

	try: 
		os.mkdir("temp") 
	except OSError as error: 
		_ = 0

	for i in range(start_index, end_index+1):
		dst = np.zeros((height, width, 3), np.uint8)
		for image in image_properties:
			image_path = image["path"]
			if check_if_file_exists(image_path) == False:
				print("Couldn't open the image file", image_path)
				sys.exit(1)
			
			src = cv.imread(image_path)
			(im_height, im_width, _) = src.shape
			opacity = image["opacity"]

			start_scale = image["start_scale"]
			end_scale = image["end_scale"]
			scale = start_scale + int((i-start_index+1)*(end_scale-start_scale)/num_frames)

			(start_position_x, start_position_y) = image["start_position"]
			(end_position_x, end_position_y) = image["end_position"]
			position_x = start_position_x + int((i-start_index+1)*(end_position_x - start_position_x)/num_frames)
			position_y = start_position_y + int((i-start_index+1)*(end_position_y - start_position_y)/num_frames)
			position = (position_x, position_y)

			if image["keep_aspect_ratio"] == True:
				src = cv.resize(src, (int(im_width*scale/100), int(im_height*scale/100)))
			elif image["keep_aspect_ratio"] == False and image["width"] != -1 and image["height"] != -1:
				src = cv.resize(src, (int(image["width"]), int(image["height"]*scale/100)))
			src = fit_image(height, width, position, src, image_path)
	
			dst = cv.addWeighted(dst, 1, src, opacity/100, 0)

		dst = add_margin(dst, margin, margin_color)

		frame_name = "temp/" + str(i) + ".jpg"
		cv.imwrite(frame_name, dst)


def create_pdf_from_frames(filename):
	image_list = []
	i = 1
	image_path = "temp/" + str(i) + ".jpg"
	while(check_if_file_exists(image_path) == True):
		temp_image = Image.open(image_path)
		temp_image.convert("RGB")
		image_list.append(temp_image)
		i+=1
		image_path = "temp/" + str(i) + ".jpg"
	
	temp_image = image_list.pop(0)

	try:
		temp_image.save(filename, save_all=True, append_images=image_list)
	except Exception as e:
		print("error occurred while saving:", e)
		sys.exit(1)

	delete_frames()

	print("Converted successfully.")


def create_avi_from_frames(filename):
	img_array = []
	i = 1
	image_path = "temp/" + str(i) + ".jpg"
	while(check_if_file_exists(image_path) == True):
		img = cv.imread(image_path)
		(height, width, _) = img.shape
		size = (width, height)
		img_array.append(img)
		i+=1
		image_path = "temp/" + str(i) + ".jpg"

	out = cv.VideoWriter(filename, cv.VideoWriter_fourcc(*'DIVX'), 4, size)
	 
	for i in range(len(img_array)):
	    out.write(img_array[i])
	out.release()

	delete_frames()

	print("Converted successfully.")


def parse_sequence(line):
	image_properties = []
	image_lines = []
	line = line.strip()
	if '->' in line:
		i = line.find("->")
		start_index = int(line[0:i].strip())
		if '=>' in line:
			j = line.find("=>")
			end_index = int(line[i+2:j].strip())
			line = line[j+2:]
			brackets = 0
			q = line.find("[")+1
			w = q
			while(w < len(line)):
				if line[w] == "(":
					brackets+=1
				if line[w] == ")":
					brackets-=1
				if line[w] == "," and brackets == 0:
					l2 = line[q:w].strip(",").strip()
					image_lines.append(l2)
					q = w
				w+=1
			l3 = line[q:w].strip(",").strip()
			l3 = l3[0:l3.find("]")]
			image_lines.append(l3)
			for i in image_lines:
				property = get_image_properties(i)
				image_properties.append(property)
		else:
			print("Invalid sequence")
			sys.exit(1)
	else:
		print("Invalid sequence")
		sys.exit(1)
	return (start_index, end_index, image_properties)


def set_image_property(arg):
	if "keep_aspect_ratio" in arg:
		if arg[arg.find("=")+1:].strip().lower() == "false":
			return [("keep_aspect_ratio", False)]
		
	if "start_position" in arg:
		arg = arg[arg.find("=")+1:].strip()
		arg = arg.strip("()")
		if "," in arg:
			A = [x.strip() for x in arg.split(",")]
			temp = A[0]
			pos_x = int(temp[:temp.find("px")])
			temp = A[1]
			pos_y = int(temp[:temp.find("px")])
			return [("start_position", (pos_x, pos_y))]
		else:
			pos = int(arg[:arg.find("px")])
			return [("start_position", (pos, pos))]
		
	if "end_position" in arg:
		arg = arg[arg.find("=")+1:].strip()
		arg = arg.strip("()")
		if "," in arg:
			A = [x.strip() for x in arg.split(",")]
			temp = A[0]
			pos_x = int(temp[:temp.find("px")])
			temp = A[1]
			pos_y = int(temp[:temp.find("px")])
			return [("end_position", (pos_x, pos_y))]
		else:
			pos = int(arg[:arg.find("px")])
			return [("end_position", (pos, pos))]
		
	if "start_position" not in arg and "end_position" not in arg:
		if "position" in arg:
			arg = arg[arg.find("=")+1:].strip()
			arg = arg.strip("()")
			if "," in arg:
				A = [x.strip() for x in arg.split(",")]
				temp = A[0]
				pos_x = int(temp[:temp.find("px")])
				temp = A[1]
				pos_y = int(temp[:temp.find("px")])
				return [("start_position", (pos_x, pos_y)), ("end_position", (pos_x, pos_y))]
			else:
				pos = int(arg[:arg.find("px")])
				return [("start_position", (pos, pos)), ("end_position", (pos, pos))]

	if "start_scale" in arg:
		start_scale = int(arg[arg.find("=")+1:arg.find("%")].strip())
		return [("start_scale", start_scale)]
		
	if "end_scale" in arg:
		end_scale = int(arg[arg.find("=")+1:arg.find("%")].strip())
		return [("end_scale", end_scale)]
		
	if "start_scale" not in arg and "end_scale" not in arg:
		if "scale" in arg:
			scale = int(arg[arg.find("=")+1:arg.find("%")].strip())
			return [("start_scale", scale), ("end_scale", scale)]

	if "height" in arg:
		height = int(arg[arg.find("=")+1:arg.find("px")].strip())
		return [("height", height)]
		
	if "width" in arg:
		width = int(arg[arg.find("=")+1:arg.find("px")].strip())
		return [("width", width)]

	if "opacity" in arg:
		opacity = float(arg[arg.find("=")+1:arg.find("%")].strip())
		return [("opacity", opacity)]

	return []


def get_image_properties(line):
	image_properties = []
	
	if "(" in line:
		k = line.find("(")
		l = k
		count = 1
		while count > 0:
			l += 1
			if line[l] == "(":
				count += 1
			elif line[l] == ")":
				count -= 1
		
		img_line = line[k:l+1].strip()
		img = {"path":"", "keep_aspect_ratio":True, "height":-1, "width":-1, "start_position":(0,0), "end_position":(0,0), "start_scale":100, "end_scale":100, "opacity":100}
		img["path"] = img_line[1:img_line.find(",")].strip()
		img_line = img_line[img_line.find(",")+1:-1].strip().strip("{}")
		args = [x.strip() for x in img_line.split(";")]

		if "" in args:
			args.remove("")		
		for arg in args:
			for (property, value) in set_image_property(arg):
				img[property] = value

	else:
		line = line.strip("[]")
		B = [x.strip() for x in line.split(",")]
		for i in B:
			img = {"path":"", "keep_aspect_ratio":True, "height":-1, "width":-1, "start_position":(0,0), "end_position":(0,0), "start_scale":100, "end_scale":100, "opacity":100}
			img["path"] = i

	return img


def print_help():
	print("Usage: python3 fc.py <flipbook_name.flip> -o <output_filename>")
	print()
	print("Current version of the tool only supports .pdf and .avi as")
	print("output file extension")
	print()
	print("Check the README.md file for more details on flipbook language")

def print_version():
	print("Version 1.0.0")


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
			arguments["input_file"] = args[0]
			arguments["output_file"] = args[2]
			if args[2].endswith(".pdf"):
				arguments["output_type"] = "pdf"
			elif args[2].endswith(".gif"):
				arguments["output_type"] = "gif"
			elif args[2].endswith(".avi"):
				arguments["output_type"] = "avi"
			else:
				print("Unrecognized file type:", args[2])
				sys.exit(1)
	else:
		print("Unrecognized arguments")
		sys.exit(1)

	return arguments


if __name__ == "__main__":
	arguments = parse_arguments(sys.argv[1:])

	render_file(filename=arguments["input_file"])
	
	if arguments["output_type"] == "pdf":
		create_pdf_from_frames(filename=arguments["output_file"])
	elif arguments["output_type"] == "avi":
		create_avi_from_frames(filename=arguments["output_file"])
	else:
		print("unrecognized output_type:", arguments["output_type"])
		sys.exit(1)