
# Enhanced ColorChecker Grid Tool

This repository contains an application that helps you generate and apply a deformed 3D LUT (Look-Up Table) for color correction using a ColorChecker grid. The tool provides an interactive web interface for capturing reference and extracted color values, and then either exporting a cube file or applying the LUT directly to an image. The code is built on Flask and uses HTML, CSS, and JavaScript (with Canvas) for the front end.

## Project Structure

```
Enhanced-ColorChecker-Grid-Tool/
├── app.py
├── requirements.txt
└── templates/
    └── index.html
```

- **app.py**  
  The core Flask application. It contains endpoints for:
  - Displaying the home page (`/`).
  - Generating a 3D LUT file (`/generate_lut`) based on provided color values.
  - Applying the generated LUT to a full-resolution image (`/apply_lut`) and returning the result as a PNG.
  
  The code in `app.py` uses several libraries such as NumPy, SciPy, Pillow, and a custom module `pillow_lut` for LUT filtering.

- **templates/index.html**  
  This file contains the user interface code (HTML, CSS, JavaScript) for:
  - Uploading an image.
  - Selecting the grid mode (interactive or manual).
  - Adjusting or defining the grid corners.
  - Displaying the reference colors (which can be modified) and the automatically extracted colors side by side.
  - Generating and applying the LUT, with a built-in loading overlay.
  - Downloading the processed image (click the image to download) or the cube file.
  
  The UI has been designed to be clean and user-friendly with real-time updating of the grid and color extraction.

## Features

- **Interactive Grid Mode (Default):**  
  A grid with draggable red handles is overlayed on the uploaded image. As you move the handles, the extracted colors are updated in real time.

- **Manual Corner Picking Mode:**  
  Simply click 4 times anywhere on the image to define the corners (order doesn’t matter). The tool reorders points into a convex quadrilateral, automatically extracts colors, and applies the best grid orientation.

- **LUT Generation & Application:**  
  - Generate a `.cube` LUT file based on reference and extracted color data.
  - Apply the generated LUT to the original full-resolution image.
  - A loading overlay is displayed while the LUT is being applied.
  - The processed image is shown in the preview area with an accompanying download link.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your_username/Enhanced-ColorChecker-Grid-Tool.git
   cd Enhanced-ColorChecker-Grid-Tool
   ```

2. **Create and activate a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   # On Windows:
   venv\\Scripts\\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   Make sure your `requirements.txt` includes at least the following dependencies:
   - Flask
   - NumPy
   - SciPy
   - Pillow
   - pillow_lut (if available via pip or include installation instructions)

## Running the Application

Start the Flask development server by running:

```bash
python app.py
```

Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) to access the application.

## Usage

1. **Load an Image:**  
   Use the file input to upload an image. The grid will automatically be initialized in **Interactive Mode**.

2. **Adjust the Grid or Choose Manual Mode:**  
   - In **Interactive Mode**, drag the red grid corners to adjust the extraction areas. Colors update automatically.
   - In **Manual Mode**, simply click four times on the image. The tool will automatically order the points and extract the colors.

3. **Generate LUT or Apply LUT:**  
   - Click **"Download Cube File"** to generate and download the LUT file.
   - Click **"Apply LUT"** to process the image. A loading overlay will display while processing. Once done, the processed image appears in the preview area with a download link underneath.

## Screenshot

![Screenshot](screenshot.png)


## Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](LICENSE)

## Acknowledgements

- Built using [Flask](https://flask.palletsprojects.com/).
- Interpolation powered by [SciPy](https://www.scipy.org/).
- Image processing via [Pillow](https://python-pillow.org/).
```
