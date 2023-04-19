import os
import csv
import laspy
import numpy as np
import cv2


def save_lidar_grid(las_data, mask, las_file_name):
    las_out = laspy.create()
    for dim_name in las_data.point_format.dimension_names:
        dim_data = getattr(las_data, dim_name)[mask]
        setattr(las_out, dim_name, dim_data)

    las_out.write(las_file_name)


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

                # Create directory for the grid
                grid_name = f'grid_{y_idx}_{x_idx}'
                grid_dirname = os.path.join(output_dir, grid_name)

                if not os.path.exists(grid_dirname):
                    os.makedirs(grid_dirname)

                # Save image
                image_filename = f'{grid_dirname}.png'
                image_filepath = os.path.join(grid_dirname, image_filename)
                cv2.imwrite(image_filepath, img)

                # Save LAS file
                lidar_filename = f'{grid_dirname}.las'
                lidar_filepath = os.path.join(grid_dirname, lidar_filename)
                save_lidar_grid(las_data, mask, lidar_filepath)

                # Save metadata
                metadata_filename = f'{grid_dirname}.csv'
                metadata_filepath = os.path.join(
                    grid_dirname, metadata_filename)

                with open(metadata_filepath, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(
                        ['image_filename', 'grid_x', 'grid_y', 'x_min', 'y_min', 'x_max', 'y_max', 'z_min', 'z_max'])
                    csv_writer.writerow([image_filename, x_idx, y_idx, x_min_grid,
                                        y_min_grid, x_max_grid, y_max_grid, z_min, z_max])


las_file_path = 'data/A_RP-A-1_ - Scanner 1_SIDE_A - 190324_230239_Scanner_1 - originalpoints.las'
img_size = (1024, 1024)
resolution = 0.01  # 1 cm per pixel

extract_and_save_grid_images(las_file_path, img_size, resolution=resolution)
