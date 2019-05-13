import numpy as np

sum_vel = np.zeros(15)
init_flag = 0
flipflop = 0
flipflop1 = 0

# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    global sum_vel, init_flag, flipflop, flipflop1

    sum_vel[:-1] = sum_vel[1:]
    sum_vel[-1] = Rover.vel
                
    mean_vel = np.mean(sum_vel)
    print('mean_vel=',mean_vel)

    if init_flag == 0 and mean_vel == 0:
        sum_vel[-1] = 1
        mean_vel = np.mean(sum_vel)      #dummy
        init_flag = 1

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward':
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
                
            # Check the extent of navigable terrain
            elif len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                    
                Rover.brake = 0

                # Rover is Stuck - SG: Require better way to handle this
                if mean_vel < 0.01: 
                    # Set steering to average angle clipped to the range +/- 15
                    if flipflop < 50:
                        Rover.steer = -15
                        flipflop += 1
                        Rover.throttle = 0
                    elif flipflop < 100:
                        Rover.steer = 15
                        flipflop += 1
                        Rover.throttle = 0
                    elif flipflop < 150:
                        Rover.steer = -15
                        flipflop += 1
                    elif flipflop < 200:
                        Rover.steer = 15
                        flipflop += 1
                    else:
                        Rover.steer = -15
                        flipflop = 0

                    print('Rover stuck - Forward')
                else:
                    # Set steering to average angle clipped to the range +/- 15
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    
                    print('Normal Working - Forward')
                
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'
                    
                    print('Stop Working - Forward')

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
                
                print('Stop Hard - Stop')
                
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Rover near sample
                if Rover.near_sample and not Rover.picking_up:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

                    print('Near Rock - Stop')
                # Now we're stopped and we have vision data to see if there's a path forward
                elif len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    # Set steering to average angle clipped to the range +/- 15
                            
                    Rover.steer = -15 # Could be more clever here about which way to turn
                    
                    print('Rotate -15 - Stop')
                    
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
                    
                    print('Normal Forward - Stop')
                    
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    elif Rover.rock_angles is not None:
        # Rover near sample
        if Rover.near_sample and Rover.vel > 0 and not Rover.picking_up:
            # Set mode to "stop" and hit the brakes!
            Rover.throttle = 0
            # Set brake to stored brake value
            Rover.brake = Rover.brake_set
            Rover.steer = 0
            Rover.mode = 'stop'

            print('Near Rock - Rock')
            
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

            # Set steering to average angle clipped to the range +/- 15
            Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)

            print('Moving Towards Rock - Rock')
            
        else:   #Should not come here
            Rover.throttle = Rover.throttle_set
            Rover.steer = -15#0
        
            print('Something wrong')

            Rover.brake = 0
    else:
            Rover.throttle = Rover.throttle_set
            Rover.steer = -15#0
        
            print('No path ahead - None')

            Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

