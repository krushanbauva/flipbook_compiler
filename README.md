# flipbook_compiler
A flipbook compiler that can convert a flipbook description into a printable pdf or a video (.avi format)

## Current Scope
For specified indices of frames:
- Multiple images can be added and blended together (with specific opacity values)
- Each image can undergo transitions in a way specified by the user where:
  - Scaling of the image can be changed over frames.
  - Relative position of the image can be changed over frames.

The current version of the flipbook compiler takes care of almost all the possible use cases where images can be placed anywhere in the frame and transitions/scaling can be specified by the user.

## How to use
```bash
python3 fc.py <flipbook_name.flip> -o <output_filename>
```

## Language specification for flipbook description
```bash
[page]
//property1=value1
//property2=value2
...

[sequence]
//start_index1:int -> end_index1:int => [(image1_path:string, image1_properties:dict), (image2_path:string, image2_properties:dict), (...), ... ]
//start_index2:int -> end_index2:int => [(image1_path:string, image1_properties:dict), (image2_path:string, image2_properties:dict), (...), ... ]
...
```
Check out `apple.flip` for a better understanding of the language specification.

## Valid page properties
- `height` in px (of the actual flipbook)
- `width` in px (of the actual flipbook)
- `margin` in px with ordering - top, right, bottom, left
  - Usecase : if you want to have additional space on the left/bottom to account for stapling/binding of printed pages
- `margin_color` in hex (of the margin)

## Valid image properties
- `keep_aspect_ratio` in boolean format (true/false)
- `start_position` in (px, px) 
- `end_position` in (px, px) 
- `position` in (px, px) (if the image is not to be moved throughout the transition)
- `start_scale` in percentage 
- `end_scale` in percentage 
- `scale` in percentage (if the image is not to be scaled differently throughout the transition)
- `height` and `width` (in case aspect ratio is not kept constant)
- `opacity` in percentage

## Example
On executing the below command in terminal, we get a video file `apple_flipbook.avi` generated where an apple falls from the tree on a man's head and the man later eats it using just two images `apple.png` and `man.png`
```bash
python3 fc.py apple.flip -o apple_flipbook.avi
```

On executing the below command in terminal, we get a printable pdf file `apple_flipbook.pdf` for the same.
```bash
python3 fc.py apple.flip -o apple_flipbook.pdf
```

## Future Scope
The compiler can have additional options like:
- Appling transformations to the raw images like cropping, flipping, rotating, etc but not limited to just that.
- Exporting to other formats ( `.gif`, `.mp4`, etc)
