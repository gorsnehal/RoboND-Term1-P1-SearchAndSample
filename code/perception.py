import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

def color_thresh_SG(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img)
    
    # For Ground Pixels
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    GrdPix_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[GrdPix_thresh,2] = 255
    
    # For Obstacles
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    ObstPix_thresh = (  (img[:,:,0] <= rgb_thresh[0]) \
                      | (img[:,:,1] <= rgb_thresh[1]) \
                      | (img[:,:,2] <= rgb_thresh[2]) )
    # Index the array of zeros with the boolean array and set to 1
    color_select[ObstPix_thresh,0] = 255
    
    # For Rocks
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
        
    #Convert to HSI
    imgHSV = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    
    lower_yellow = np.array([20,100,100])
    upper_yellow = np.array([30,255,255])
    
    #rgb_yellow = cv2.cvtColor(np.uint8([[[30,255,255]]]),cv2.COLOR_HSV2RGB)
    #print(rgb_yellow)

    # Threshold the HSV image to get only yellow colors
    imgThreshed = cv2.inRange(imgHSV, lower_yellow, upper_yellow)
    
    Rocks_x, Rocks_y = imgThreshed.nonzero()

    # Index the array of zeros with the boolean array and set to 1
    color_select[Rocks_x, Rocks_y, 1] = 255
    
    # Also make corresponding obstacles pixels 0
    # NOTE : Last index 0, Assigned value 0
    color_select[Rocks_x, Rocks_y, 0] = 0
    
    # Return the binary image
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel

def rover_coords_SG(color_img):
    # Identify nonzero pixels
    ypos, xpos, vIndx = color_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - color_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - color_img.shape[1]/2).astype(np.float)
    
    return x_pixel, y_pixel, vIndx


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    source = np.float32([[118.5,95.8],[199.5,95.8],[303.1,140.4],[13.6,140.4]])
    
    dst_sz = 5
    bottom_offset = 4
    half_wd = Rover.img.shape[1]/2;
    row_wOffset = Rover.img.shape[0] - bottom_offset;
    
    destination = np.float32([[half_wd - dst_sz, row_wOffset - 2*dst_sz],
                              [half_wd + dst_sz, row_wOffset - 2*dst_sz],
                              [half_wd + dst_sz, row_wOffset],
                              [half_wd - dst_sz, row_wOffset]])
    
    # 2) Apply perspective transform
    warped = perspect_transform(Rover.img, source, destination)
    
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed = color_thresh_SG(warped)
    
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image
    Rover.vision_image = threshed

    # 5) Convert map image pixel values to rover-centric coords
    xpix, ypix, valIndx = rover_coords_SG(threshed)
    
    # 6) Convert rover-centric pixel values to world coordinates
    rover_xpos = Rover.pos[0]
    rover_ypos = Rover.pos[1]
    rover_yaw = Rover.yaw
    
    scale = 10
    
    xpix_w, ypix_w = pix_to_world(xpix, ypix, rover_xpos, rover_ypos, rover_yaw, Rover.worldmap.shape[0], scale)

    #pitch & roll threshold
    pitch_low_th = 1
    pitch_high_th = 359
    roll_low_th = 1
    roll_high_th = 359
    
    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    #For Fidelity improvement - Only updating obstacles & rock data
    # As pitxh and/or roll are high, mapping will be wrong
    if (Rover.pitch > pitch_low_th and Rover.pitch < pitch_high_th) or (Rover.roll > roll_low_th and Rover.roll < roll_high_th):
        Rover.worldmap[ypix_w, xpix_w, 0] += 1
        Rover.worldmap[ypix_w, xpix_w, 1] += 1
    else:   # Update all data - Obstacles, Rock & Navigable world
        Rover.worldmap[ypix_w, xpix_w, valIndx] += 1

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Get navigable area pixels
    xpix_Grnd = xpix[valIndx == 2]
    ypix_Grnd = ypix[valIndx == 2]

    dist, angles = to_polar_coords(xpix_Grnd, ypix_Grnd)

    # To avoid making decision when rover has more pitch or roll
    # Effectively making control decision with near distance data
    if (Rover.pitch > pitch_low_th and Rover.pitch < pitch_high_th) or (Rover.roll > roll_low_th and Rover.roll < roll_high_th):
        mul_sd = 2
    else:
        mul_sd = 3
            
    mean_dist = np.mean(dist)
    std_dist = np.std(dist)

    pruned_list = dist[:] < (mean_dist + mul_sd * std_dist)
        
    p_dist = dist[pruned_list]
    p_angles = angles[pruned_list]

    # Update Rover pixel distances and angles
    Rover.nav_dists = p_dist
    Rover.nav_angles = p_angles
    
    # Get Rock pixels
    xpix_Rock = xpix[valIndx == 1]
    ypix_Rock = ypix[valIndx == 1]
    
    dist_r, angles_r = to_polar_coords(xpix_Rock, ypix_Rock)
    
    Rover.rock_angles = angles_r
    
    return Rover
