## Project: Search and Sample Return
### Author: Snehal Gor

---

**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator ([MacOS](https://s3-us-west-1.amazonaws.com/udacity-robotics/Rover+Unity+Sims/Mac_Roversim.zip), [Linux](https://s3-us-west-1.amazonaws.com/udacity-robotics/Rover+Unity+Sims/Linux_Roversim.zip), [Windows](https://s3-us-west-1.amazonaws.com/udacity-robotics/Rover+Unity+Sims/Windows_Roversim.zip)) and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/rover_image.jpg
[image2]: ./calibration_images/example_grid1.jpg
[image3]: ./calibration_images/example_rock1.jpg 

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

New function named 'color_thresh_SG' has been written. Following are the modifications compared to base version
1. Pixel values above threshold (rgb_thresh_Gr), identified as Ground pixels - Brighter pixels
2. Obstacle threshold being added : rgb_thresh_Ob
3. Pixel values below threshold (rgb_thresh_Ob), identified as Obstacle pixels - Darker pixels
4. Image converted from RGB -> HSV space using OpenCV function
5. Yellow color pixels identified in HSV space with lower threshold at '20,100,100' & upper threshold at '30,255,255' (Using OpenCV function inRange)
6. Identified rock pixels removed from obstacle pixels (cleanup)

![alt text][image1]

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 

Following modifications done in process_image function
1. Perspective transform call being added after warping function calculation : 
	_Input - Camera image_
	_Output: Warped image / Perspective transformed image_

	```
	warped = perspect_transform(img, source, destination)
	```

2. Call for `color_thresh_SG` being added : 
	_Input - Warped image / Perspective transformed image_
	_Output - Thresholded Image_
	* Height x Width x 3 size image
	* Plane 0: Obstacle pixels marked with 255
	* Plane 1: Rock pixels marked with 255
	* Plane 2: Ground / Navigable pixels marked with 255

	```
	threshed = color_thresh_SG(warped)
	```

3. Call `rover_coords_SG` - Modified to handle 'Height x Width x 3 size image'
	_Input - Thresholded Image - Height x Width x 3 size image_
	_Output - Non-zero pixels locations (in rover coordinate system) & corresponding value index -> 0 - Obstacle, 1 - Rock, 2 - Ground_

	```
	xpix, ypix, valIndx = rover_coords_SG(threshed)
	```

4. Get rover's current position & yaw rate
	
	```
	rover_xpos = data.xpos[data.count]
    	rover_ypos = data.ypos[data.count]
	rover_yaw = data.yaw[data.count]
	```

5. Call for `pix_to_world`
	_Input - Non-zero pixels locations (in rover coordinate system)_
	_Output - Non-zero pixels locations in World coordinate system_

	```
	xpix_w, ypix_w = pix_to_world(xpix, ypix, rover_xpos, rover_ypos, rover_yaw, data.worldmap.shape[0], scale)
	```

6. Update world map as per 
	* Non-zero pixels locations in World coordinate system
	* corresponding value index -> 0 - Obstacle, 1 - Rock, 2 - Ground

	```
	data.worldmap[ypix_w, xpix_w, valIndx] += 1
	```

_Video output in 'Test Output Video' --> Named 'process_image_output_SG.mp4'_

![alt text][image2]

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

Following modifications done in `perception_step`

1. Call for `color_thresh_SG` being added : 
	_Input - Warped image / Perspective transformed image_
	_Output - Thresholded Image_
	* Height x Width x 3 size image
	* Plane 0: Obstacle pixels marked with 255
	* Plane 1: Rock pixels marked with 255
	* Plane 2: Ground / Navigable pixels marked with 255

	```
	threshed = color_thresh_SG(warped)
	```

2. Call `rover_coords_SG` - Modified to handle 'Height x Width x 3 size image'
	_Input - Thresholded Image - Height x Width x 3 size image_
	_Output - Non-zero pixels locations (in rover coordinate system) & corresponding value index -> 0 - Obstacle, 1 - Rock, 2 - Ground_

	```
	xpix, ypix, valIndx = rover_coords_SG(threshed)
	```

3. For improving Fidelity - No World Map update when pitch or roll is high
	```
	if (Rover.pitch > pitch_low_th and Rover.pitch < pitch_high_th) or (Rover.roll > roll_low_th and Rover.roll < roll_high_th):
        	Rover.worldmap[ypix_w, xpix_w, 0] += 1
        	Rover.worldmap[ypix_w, xpix_w, 1] += 1
    	else:   # Update all data - Obstacles, Rock & Navigable world
	        Rover.worldmap[ypix_w, xpix_w, valIndx] += 1
	```

4. Only navigable / gound pixels passed
	```
	xpix_Grnd = xpix[valIndx == 2]
    	ypix_Grnd = ypix[valIndx == 2]

	dist, angles = to_polar_coords(xpix_Grnd, ypix_Grnd)
	```

5. When rover pitch or roll are high, navigable pixels list being pruned - rejecting far distance pixels
	```
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
	```
	
6. Rock pixels passed for decision logic, whereby rocks being picked

	```
	xpix_Rock = xpix[valIndx == 1]
	ypix_Rock = ypix[valIndx == 1]
	    
	dist_r, angles_r = to_polar_coords(xpix_Rock, ypix_Rock)
	    
	Rover.rock_angles = angles_r
	```
	
Following modifications done in `decision_step`

1. To identify cases when rover is stuck (Not moving or stuck with motion) near rocks, logic added with velocity history
	```
	sum_vel[:-1] = sum_vel[1:]
	sum_vel[-1] = Rover.vel
                
	mean_vel = np.mean(sum_vel)
	print('mean_vel=',mean_vel)

	if init_flag == 0 and mean_vel == 0:
		sum_vel[-1] = 1
		mean_vel = np.mean(sum_vel)      #dummy
		init_flag = 1
	```

2. 'Rover.rock_angles' being used to identify nearby rock samples. On identification of rock in path ahead, rover moves towards it. When 'Rover.near_sample' is triggered indicating rock nearby, rover stops & picks up the rock.

	```
	# Rover near sample
        if Rover.near_sample and Rover.vel > 0 and not Rover.picking_up:
	    # Set mode to "stop" and hit the brakes!
            Rover.throttle = 0
            # Set brake to stored brake value
            Rover.brake = Rover.brake_set
            Rover.steer = 0
            Rover.mode = 'stop'

            print('Near Rock - Forward')
        # Rock found - Move towards Rock
        elif(len(Rover.rock_angles) > 0):
            # If mode is forward, navigable terrain looks good 
            # and velocity is below max, then throttle
            if Rover.vel < (0.5 * Rover.max_vel):   #Reducing Max velocity
                # Set throttle value to throttle setting
                Rover.throttle = Rover.throttle_set
            else: # Else coast
                Rover.throttle = 0
                    
            Rover.brake = 0
                
            # Rover is Stuck - SG: Require better way to handle this
            if mean_vel < 0.01: 
                # Set steering to average angle clipped to the range +/- 15
                if flipflop1 < 50:
                    Rover.steer = -15
                    flipflop1 += 1
                    Rover.throttle = 0
                elif flipflop1 < 100:
                    Rover.steer = 15
                    flipflop1 += 1
                    Rover.throttle = 0
                elif flipflop1 < 150:
                    Rover.steer = -15
                    flipflop1 += 1
                elif flipflop1 < 200:
                    Rover.steer = 15
                    flipflop1 += 1
                else:
                    Rover.steer = -15
                    flipflop1 = 0

                print('Moving Towards Rock - Rover Stuck - Forward')
            else:
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)

                print('Moving Towards Rock - Forward') 
	```

3. Logic to handle rover stuck scenario - When navigable pixels are there, but Rover stuck due to Rock / Stone ahead

	```

	# Rover is Stuck - SG: Require better way to handle this
        if mean_vel < 0.01: 
            # Set steering to average angle clipped to the range +/- 15
            if flipflop1 < 50:
                Rover.steer = -15
                flipflop1 += 1
                Rover.throttle = 0
            elif flipflop1 < 100:
                Rover.steer = 15
                flipflop1 += 1
                Rover.throttle = 0
            elif flipflop1 < 150:
                Rover.steer = -15
                flipflop1 += 1
            elif flipflop1 < 200:
                Rover.steer = 15
                flipflop1 += 1
            else:
                Rover.steer = -15
                flipflop1 = 0

            print('Moving Towards Rock - Rover Stuck - Forward')
        else:
            # Set steering to average angle clipped to the range +/- 15
            Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)

            print('Moving Towards Rock - Forward') 

	```

#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  

Following setting used for recording the output
Resolution : 640 X 480
Graphics   : Fastest
FPS 	   : Around 15-16

My approach / experiments
1. In Perception - For identifying Yellow Rocks, HSV space performed well as particular color needs to be identified
2. Stacking Obstacles, Rocks & Navigable pixels as one image, helped generation of vision image & world map
3. Fidelity improved through rejection of perspective transformed mapping when pitch or roll higher
4. Logic to handle Rover stuck scenario being added, but better approach required
5. Navigation towards Rock achieved through use of Rock pixels for navigation. It works, but sometime rover stuck while retrieving the Rock. Logic mentioned in 4 above helped to avoid such situation. 
6. Smoothening to improve Rover fidelity (Reducing impact of sudden movement) tried, but resulted in a oscillatory motion. Some dampening or PID like approach required

Future Improvements or Enhancements
1. Rover sometime circles around one area continuously. Map mapping & avoiding already traced area required.
2. Better approach to Rover stuck case handling may be possible
3. Currently Rover is able to pick up all obstacles, but going back to center of the Map missing

_Video output in 'Test Output Video' --> Named 'RoboND_Rover_SG_Screencast 2018-09-02 17:51:04.mp4'_

![](RoboND_Rover_SG_Screencast 2018-09-02 17_51_04.gif)


