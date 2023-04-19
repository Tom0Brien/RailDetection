import os
import csv
import laspy
import numpy as np
import cv2


def extract_and_save_grid_images(input_las_path, img_size, output_dir='unlabelled_data', resolution=0.01, z_min=-5, z_max=45):
    # Load the LAS file
    las_data = laspy.read(input_las_path)
    x_data, y_data, z_data = np.array(las_data.x), np.array(
        las_data.y), np.array(las_data.z)

    x_min, x_max, y_min, y_max = x_data.min(), x_data.max(), y_data.min(), y_data.max()
    x_grids, y_grids = int((x_max - x_min) / (img_size[0] * resolution)), int(
        (y_max - y_min) / (img_size[1] * resolution))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(os.path.join(output_dir, 'metadata.csv'), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(
            ['image_filename', 'source_file', 'grid_x', 'grid_y', 'x_min', 'y_min'])

        for y_idx in range(y_grids):
            for x_idx in range(x_grids):
                x_min_grid, x_max_grid = x_min + x_idx * \
                    img_size[0] * resolution, x_min + \
                    (x_idx + 1) * img_size[0] * resolution
                y_min_grid, y_max_grid = y_min + y_idx * \
                    img_size[1] * resolution, y_min + \
                    (y_idx + 1) * img_size[1] * resolution

                mask = (x_data >= x_min_grid) & (x_data < x_max_grid) & (
                    y_data >= y_min_grid) & (y_data < y_max_grid)

                if np.any(mask):
                    x_points, y_points, z_points = x_data[mask], y_data[mask], z_data[mask]

                    hist, _, _ = np.histogram2d(y_points, x_points, bins=(img_size[1], img_size[0]),
                                                range=[[y_min_grid, y_max_grid], [x_min_grid, x_max_grid]], weights=z_points)
                    hist_normalized = (hist - z_min) / (z_max - z_min)
                    img = (hist_normalized * 255).astype(np.uint8)

                    image_filename = f'grid_{y_idx}_{x_idx}.png'
                    cv2.imwrite(os.path.join(output_dir, image_filename), img)
                    csv_writer.writerow(
                        [image_filename, input_las_path, x_idx, y_idx, x_min_grid, y_min_grid])


las_file_path = 'data/A_RP-A-1_ - Scanner 1_SIDE_A - 190324_230239_Scanner_1 - originalpoints.las'
img_size = (1024, 1024)
resolution = 0.01  # 1 cm per pixel

extract_and_save_grid_images(las_file_path, img_size, resolution=resolution)
