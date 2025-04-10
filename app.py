import numpy as np
from flask import Flask, render_template, request, Response, jsonify, send_file
from scipy.interpolate import Rbf
from PIL import Image
import base64
import io
import tempfile
from pillow_lut import load_cube_file

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# Helper: convert hex string to normalized RGB array.
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.

def create_deformed_lut(size=65, correction_points=None, function='multiquadric', epsilon=0.05, smooth=3, blend=1.0):
    """
    Create a deformed 3D LUT using RBF interpolation based on correction points.
    Returns a LUT of shape (size, size, size, 3).
    """
    grid = np.linspace(0, 1, size, dtype=np.float32)
    X, Y, Z = np.meshgrid(grid, grid, grid, indexing='ij')
    grid_points = np.vstack([X.ravel(), Y.ravel(), Z.ravel()]).T

    if correction_points is None or len(correction_points) == 0:
        return np.stack([X, Y, Z], axis=-1)

    before_points = np.array([cp[0] for cp in correction_points])
    after_points  = np.array([cp[1] for cp in correction_points])

    rbf_r = Rbf(before_points[:,0], before_points[:,1], before_points[:,2],
                after_points[:,0], function=function, epsilon=epsilon, smooth=smooth)
    rbf_g = Rbf(before_points[:,0], before_points[:,1], before_points[:,2],
                after_points[:,1], function=function, epsilon=epsilon, smooth=smooth)
    rbf_b = Rbf(before_points[:,0], before_points[:,1], before_points[:,2],
                after_points[:,2], function=function, epsilon=epsilon, smooth=smooth)

    new_r = rbf_r(grid_points[:,0], grid_points[:,1], grid_points[:,2])
    new_g = rbf_g(grid_points[:,0], grid_points[:,1], grid_points[:,2])
    new_b = rbf_b(grid_points[:,0], grid_points[:,1], grid_points[:,2])
    rbf_result = np.stack([new_r, new_g, new_b], axis=-1)

    identity = grid_points
    blended = blend * rbf_result + (1 - blend) * identity
    blended = np.clip(blended, 0, 1)

    tolerance = 1e-5
    for c in range(3):
        is_one = np.isclose(identity[:, c], 1.0, atol=tolerance)
        blended[is_one, c] = identity[is_one, c]

    return blended.reshape(size, size, size, 3)

@app.route("/generate_lut", methods=["POST"])
def generate_lut():
    """
    Expects JSON with:
      - "before_data": list of 24 hex color strings (reference)
      - "after_data": list of 24 hex color strings (extracted)
    Returns the generated .cube file.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    before_list = data.get("before_data")
    after_list  = data.get("after_data")
    if before_list is None or after_list is None or len(before_list) != len(after_list):
        return jsonify({"error": "Invalid data format"}), 400

    before_arr = np.array([hex_to_rgb(c) for c in before_list])
    after_arr  = np.array([hex_to_rgb(c) for c in after_list])
    before_min = before_arr.min()
    before_max = before_arr.max()
    after_min  = after_arr.min()
    after_max  = after_arr.max()
    if after_max - after_min > 0:
        after_arr = (after_arr - after_min) / (after_max - after_min) * (before_max - before_min) + before_min

    correction_points_original = [(before_arr[i], after_arr[i]) for i in range(len(before_arr))]
    multipliers = np.linspace(0.6, 2, 20)
    correction_points_augmented = []
    for i in range(len(before_arr)):
        b = before_arr[i]
        a = after_arr[i]
        for m in multipliers:
            b_scaled = b * m
            a_scaled = a * m
            if np.all((b_scaled >= 0.0) & (b_scaled <= 1.0)) and np.all((a_scaled >= 0.0) & (a_scaled <= 1.0)):
                correction_points_augmented.append((b_scaled, a_scaled))
    cube_corners = [[r, g, b] for r in [0.0, 1.0] for g in [0.0, 1.0] for b in [0.0, 1.0]]
    extra_points = [(np.array(pt), np.array(pt)*1.10) for pt in cube_corners]
    correction_points_augmented += extra_points

    lut_3d = create_deformed_lut(size=65, correction_points=correction_points_augmented)

    cube_lines = []
    cube_lines.append("TITLE \"Deformed LUT\"")
    cube_lines.append("LUT_3D_SIZE 65")
    cube_lines.append("DOMAIN_MIN 0.0 0.0 0.0")
    cube_lines.append("DOMAIN_MAX 1.0 1.0 1.0")
    for z in range(65):
        for y in range(65):
            for x in range(65):
                r, g, b = lut_3d[x, y, z]
                cube_lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    cube_content = "\n".join(cube_lines)
    return Response(cube_content,
                    mimetype="text/plain",
                    headers={"Content-Disposition": "attachment;filename=deformed_lut.cube"})

@app.route("/apply_lut", methods=["POST"])
def apply_lut():
    print("1111")
    """
    Expects JSON with:
      - "image_data": base64-encoded PNG image (the original full‐resolution image without grid)
      - "before_data": list of 24 hex strings (reference)
      - "after_data": list of 24 hex strings (extracted)
    Generates the LUT, applies it to the full-resolution image using Pillow and pillow_lut,
    and returns the processed image as a PNG.
    (The preview on the front end is styled via CSS to show a small version.)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    image_data = data.get("image_data")
    before_list = data.get("before_data")
    after_list  = data.get("after_data")
    if image_data is None or before_list is None or after_list is None or len(before_list) != len(after_list):
        print("1111")
        return jsonify({"error": "Invalid data format"}), 400

    try:
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        print("1111")
        return jsonify({"error": "Failed to decode image data"}), 400

    before_arr = np.array([hex_to_rgb(c) for c in before_list])
    after_arr  = np.array([hex_to_rgb(c) for c in after_list])
    before_min = before_arr.min()
    before_max = before_arr.max()
    after_min  = after_arr.min()
    after_max  = after_arr.max()
    if after_max - after_min > 0:
        after_arr = (after_arr - after_min) / (after_max - after_min) * (before_max - before_min) + before_min

    correction_points_original = [(before_arr[i], after_arr[i]) for i in range(len(before_arr))]
    multipliers = np.linspace(0.6, 2, 20)
    correction_points_augmented = []
    for i in range(len(before_arr)):
        b = before_arr[i]
        a = after_arr[i]
        for m in multipliers:
            b_scaled = b * m
            a_scaled = a * m
            if np.all((b_scaled >= 0.0) & (b_scaled <= 1.0)) and np.all((a_scaled >= 0.0) & (a_scaled <= 1.0)):
                correction_points_augmented.append((b_scaled, a_scaled))
    cube_corners = [[r, g, b] for r in [0.0, 1.0] for g in [0.0, 1.0] for b in [0.0, 1.0]]
    extra_points = [(np.array(pt), np.array(pt)*1.10) for pt in cube_corners]
    correction_points_augmented += extra_points

    lut_3d = create_deformed_lut(size=65, correction_points=correction_points_augmented)
    cube_lines = []
    cube_lines.append("TITLE \"Deformed LUT\"")
    cube_lines.append("LUT_3D_SIZE 65")
    cube_lines.append("DOMAIN_MIN 0.0 0.0 0.0")
    cube_lines.append("DOMAIN_MAX 1.0 1.0 1.0")
    for z in range(65):
        for y in range(65):
            for x in range(65):
                r, g, b = lut_3d[x, y, z]
                cube_lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    cube_content = "\n".join(cube_lines)

    with tempfile.NamedTemporaryFile(suffix=".cube", delete=False) as tmp:
        tmp.write(cube_content.encode("utf-8"))
        tmp.flush()
        lut_filter = load_cube_file(tmp.name)

    # Apply the LUT to the full-resolution original image (no grid drawn)
    result_img = img.filter(lut_filter)
    output = io.BytesIO()
    # Save the processed image at its original resolution
    result_img.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png", as_attachment=True,
                     download_name="image-with-lut-applied.png")

if __name__ == "__main__":
    app.run(debug=True)
