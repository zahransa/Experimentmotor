import random
import serial
import time
import pygame
import csv
import sys
from psychopy.data import QuestHandler
import os
import re

# --------------------------- Configuration ---------------------------

# Define distances and speeds for Conditions 1 to 6
distances = [0.5, 1.5, 3.0]  # Distances for stepper motor in cm
speeds = [1, 3]  # Speeds in cm/s for slower and faster conditions

# Define total sets and trials per set
total_sets_per_condition = 2
trials_per_set = 20
total_conditions = 8
total_trials = total_conditions * total_sets_per_condition * trials_per_set  # 320 trials

# Serial configuration to communicate with Arduino
arduino_port = 'COM3'  # Adjust according to your system
baud_rate = 57600
ser = None

# Initialize Pygame for key handling
pygame.init()
screen = pygame.display.set_mode((300, 200))  # Small window for Pygame events
pygame.display.set_caption('Foot Switch Input')

# --------------------------- Functions ---------------------------

def create_new_quest():
    """
    Initializes a new QuestHandler instance.
    """
    return QuestHandler(startVal=4, startValSd=0.5, pThreshold=0.75, nTrials=20, minVal=1, maxVal=7)

def initialize_quest_handlers():
    """
    Initializes QuestHandler instances for each condition and each set.
    Returns a dictionary with keys as 'condition_set' and values as QuestHandler objects.
    """
    quest_dict = {}
    for condition in range(1, total_conditions + 1):
        for set_num in range(1, total_sets_per_condition + 1):
            key = f"{condition}_set{set_num}"
            quest_dict[key] = create_new_quest()
    return quest_dict

def initialize_serial():
    """
    Attempts to establish a serial connection with the Arduino.
    Returns the serial object and a boolean indicating connection status.
    """
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        print("Serial connection established.")
        return ser, True
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        print("Proceeding without serial connection. Motor commands and taps will not be sent.")
        return None, False

def initialize_csv(participant_name):
    """
    Initializes the CSV file for data recording.
    Returns the file object and CSV writer.
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    sanitized_name = "".join(c for c in participant_name if c.isalnum() or c in (" ", "_")).rstrip()
    filename = f"participant_{sanitized_name}_{timestamp}.csv"
    directory = os.path.join(os.getcwd(), "data")
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    filepath = os.path.join(directory, filename)
    try:
        csv_file = open(filepath, mode='w', newline='', buffering=1)  # Line-buffered
        fieldnames = ['SubjectID', 'Condition', 'OverallTrial', 'SpecificTrial',
                      'ProbeLevel', 'ReferenceLevel', 'Response', 'TrialDuration']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        print(f"CSV file initialized at {filepath}")
        return csv_file, writer
    except Exception as e:
        print(f"Failed to initialize CSV file: {e}")
        sys.exit(1)

def get_foot_response():
    """
    Waits for the participant to press the Right or Left arrow key.
    Returns 'Yes' for Right and 'No' for Left.
    """
    print("Waiting for foot response (Right for 'Yes', Left for 'No')")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:  # Right arrow key (Yes)
                    print("Right foot pressed (Yes)")
                    return 'Yes'
                elif event.key == pygame.K_LEFT:  # Left arrow key (No)
                    print("Left foot pressed (No)")
                    return 'No'

def wait_for_up_arrow():
    """
    Waits for the participant to press the Up Arrow key to proceed.
    """
    print("Waiting for Up Arrow key press to move back to the wall...")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    print("Up Arrow key pressed.", end=' ')
                    if serial_connected and ser and ser.is_open:
                        ser.write(b'continue\n')  # Send "continue" to Arduino
                        print("Sent 'continue' to Arduino.")
                    else:
                        print("Serial not connected. Cannot send 'continue'.")
                    return


# Function to read force data and capture the highest value
# Function to read force data and capture the highest value
def read_highest_force_data(duration=0.5):
    """
    Reads force data continuously for the given duration (in seconds) and returns the highest value recorded.
    Assumes continuous data is being sent by Arduino.
    """
    start_time = time.time()
    highest_force = -float('inf')  # Initialize with the lowest possible value

    while (time.time() - start_time) < duration:
        if serial_connected and ser and ser.is_open:
            try:
                # Read force data from the serial port
                force_data = ser.readline().decode('utf-8').strip()

                # Extract numeric part using regex
                force_value_str = re.findall(r"[-+]?\d*\.\d+|\d+", force_data)

                if force_value_str:
                    # Convert to float if a number is found
                    force_value = float(force_value_str[0])
                    # Update the highest value seen so far
                    if force_value > highest_force:
                        highest_force = force_value
                else:
                    print(f"Warning: No numeric value found in sensor data '{force_data}'")

            except Exception as e:
                print(f"Error reading force data: {e}")
                return None
        else:
            print("Serial port not connected. Cannot read force data.")
            return None

    return highest_force if highest_force != -float('inf') else None


# Function to send taps and measure force
# Function to send taps and measure force
def send_taps(fixed_intensity=4, variable_intensity=4, condition=None):
    """
    Sends two taps to the Arduino: one fixed and one variable, with timestamps.
    Measures the highest force during the tap and logs both timestamps and force values.
    """
    if serial_connected and ser and ser.is_open:
        try:
            # Log current time for the fixed tap
            timestamp_fixed_tap = time.time()
            print(
                f"Sending first tap (Fixed): Fixed tap = {fixed_intensity}, Condition = {condition}, Timestamp = {timestamp_fixed_tap}")

            # First tap: Fixed intensity
            command = f"0{condition}{fixed_intensity}{variable_intensity}"
            ser.write(f'{command}\n'.encode())
            time.sleep(0.1)  # Short delay for first tap

            # Measure highest force during the first tap (e.g., record for 500ms)
            force_fixed_tap = read_highest_force_data(duration=0.5)
            print(f"Highest force during first tap: {force_fixed_tap}")

            # Log current time for the variable tap
            timestamp_variable_tap = time.time()
            print(
                f"Sending second tap (Variable): Variable tap = {variable_intensity}, Condition = {condition}, Timestamp = {timestamp_variable_tap}")

            # Second tap: Variable intensity
            command = f"1{condition}{fixed_intensity}{variable_intensity}"
            ser.write(f'{command}\n'.encode())
            time.sleep(0.1)  # Short delay for second tap

            # Measure highest force during the second tap (e.g., record for 500ms)
            force_variable_tap = read_highest_force_data(duration=0.5)
            print(f"Highest force during second tap: {force_variable_tap}")

            # Check if the CSV file exists
            file_exists = os.path.isfile('tap_timestamps_force_data.csv')

            # Log timestamps and force data to a CSV
            with open('tap_timestamps_force_data.csv', 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)

                # Write header only if file is new
                if not file_exists:
                    csv_writer.writerow(['Condition', 'TapType', 'Intensity', 'Timestamp', 'MaxForce'])

                # Log data for the fixed tap
                csv_writer.writerow([condition, 'Fixed', fixed_intensity, timestamp_fixed_tap, force_fixed_tap])

                # Log data for the variable tap
                csv_writer.writerow([condition, 'Variable', variable_intensity, timestamp_variable_tap, force_variable_tap])

        except Exception as e:
            print(f"Error during serial communication: {e}")
    else:
        print("Serial port not connected. Skipping taps.")



def control_motors(distance, speed, variable_intensity, condition):
    """
    Controls the stepper motor and sends taps based on the condition.
    """
    if condition in range(1, 7):  # Conditions 1 to 6
        # Send motor movement command
        print(f"Condition {condition}: Moving stepper motor for {distance} cm at {speed} cm/s")
        motor_command = f"MOVE {distance} {speed}\n"
        if serial_connected and ser and ser.is_open:
            try:
                ser.write(motor_command.encode())
            except Exception as e:
                print(f"Error sending motor command: {e}")
        else:
            print("Serial port not connected. Skipping motor movement.")
        time.sleep(0.5)  # Delay to let the motor move before sending taps

        # Send taps after motor movement
        send_taps(fixed_intensity=4, variable_intensity=variable_intensity, condition=condition)

        # Introduce a fixed 1-second delay before returning the motor
        fixed_delay = 1.0  # 1 second
        print(f"Condition {condition}: Waiting for {fixed_delay} second before returning motor.")
        time.sleep(fixed_delay)

        # Return the motor to its original position (fast)
        print(f"Condition {condition}: Returning motor to original position at {speed} cm/s")
        motor_command = f"MOVE_RETURN {distance} {speed}\n"
        if serial_connected and ser and ser.is_open:
            try:
                ser.write(motor_command.encode())
            except Exception as e:
                print(f"Error sending return motor command: {e}")
        else:
            print("Serial port not connected. Skipping motor return.")
        time.sleep(0.5)  # Delay after motor return

    elif condition == 7:  # Baseline: No movement, just taps
        print(f"Condition 7: Baseline, no movement, applying taps.")
        send_taps(fixed_intensity=4, variable_intensity=variable_intensity, condition=condition)

    elif condition == 8:  # Condition 8: Special case
        print(f"Condition 8: Moving back 3 cm at slow speed, applying taps.")
        motor_command = f"MOVE_BACK 3 1\n"  # Move back 3 cm at 1 cm/s
        if serial_connected and ser and ser.is_open:
            try:
                ser.write(motor_command.encode())
            except Exception as e:
                print(f"Error sending MOVE_BACK command: {e}")
        else:
            print("Serial port not connected. Skipping MOVE_BACK.")
        time.sleep(0.5)  # Delay before taps

        # Send taps at the back position
        send_taps(fixed_intensity=4, variable_intensity=variable_intensity, condition=condition)

        # Get foot response from the participant
        response = get_foot_response()
        quest_key = f"{condition}_set{current_set_dict[condition]}"
        quest_dict[quest_key].addResponse(1 if response == 'Yes' else 0)

        # After the response, wait for Up Arrow key press instead of Space Bar
        wait_for_up_arrow()

        # Move forward to the wall without waiting for additional response
        print(f"Condition 8: Moving forward to the wall at 2 cm/s.")
        motor_command = f"MOVE_FORWARD 3 2\n"  # Move forward 3 cm at 2 cm/s
        if serial_connected and ser and ser.is_open:
            try:
                ser.write(motor_command.encode())
            except Exception as e:
                print(f"Error sending MOVE_FORWARD command: {e}")
        else:
            print("Serial port not connected. Skipping MOVE_FORWARD.")
        time.sleep(0.5)  # Delay after moving forward

# --------------------------- Main Experiment ---------------------------

if __name__ == "__main__":
    try:
        # Initialize QuestHandlers
        quest_dict = initialize_quest_handlers()

        # Initialize a counter to keep track of current set per condition
        # This helps in assigning SpecificTrial numbers
        current_set_dict = {condition: 1 for condition in range(1, total_conditions + 1)}

        # Initialize serial connection
        ser, serial_connected = initialize_serial()

        # Prompt the participant for their name
        participant_name = input("Please enter the participant's name: ").strip()
        if not participant_name:
            participant_name = "unknown_participant"
            print("No name entered. Using 'unknown_participant' as the name.")

        # Initialize CSV file
        csv_file, csv_writer = initialize_csv(participant_name)

        print("Starting experimental trials...")

        # Generate all trials
        trials = []
        for condition in range(1, total_conditions + 1):
            for set_num in range(1, total_sets_per_condition + 1):
                for trial_num in range(1, trials_per_set + 1):
                    # Determine distance and speed based on condition
                    if condition in [1, 2]:
                        distance = distances[0]  # 0.5 cm
                        speed = speeds[0] if condition == 1 else speeds[1]  # 1 cm/s or 2 cm/s
                    elif condition in [3, 4]:
                        distance = distances[1]  # 1.5 cm
                        speed = speeds[0] if condition == 3 else speeds[1]
                    elif condition in [5, 6]:
                        distance = distances[2]  # 3.0 cm
                        speed = speeds[0] if condition == 5 else speeds[1]
                    elif condition == 7:
                        distance = 0  # Baseline, no movement
                        speed = 0
                    elif condition == 8:
                        distance = 3  # Moving back 3 cm
                        speed = 1  # Slow speed

                    # Assign QuestHandler key
                    quest_key = f"{condition}_set{set_num}"

                    # Append trial details
                    trials.append({
                        'Condition': condition,
                        'Set': set_num,
                        'Distance': distance,
                        'Speed': speed,
                        'QuestKey': quest_key
                    })

        print(f"Total Trials Generated: {len(trials)}")  # Should be 320

        # Shuffle the trials to randomize order
        random.shuffle(trials)
        print("Trials shuffled.")

        # Initialize SpecificTrial counters
        specific_trial_counters = {f"{condition}_set{set_num}": 0
                                   for condition in range(1, total_conditions + 1)
                                   for set_num in range(1, total_sets_per_condition + 1)}

        # Iterate through each trial
        for overall_trial_num, trial in enumerate(trials, start=1):
            condition = trial['Condition']
            set_num = trial['Set']
            distance = trial['Distance']
            speed = trial['Speed']
            quest_key = trial['QuestKey']

            # Get the next intensity from the Quest algorithm
            try:
                variable_intensity = quest_dict[quest_key].next()
            except Exception as e:
                print(f"Error retrieving next Quest value for {quest_key}: {e}")
                variable_intensity = 4  # Default to 4 if error occurs

            # Increment SpecificTrial counter
            specific_trial_counters[quest_key] += 1
            specific_trial_num = specific_trial_counters[quest_key]

            print(f"\nOverall Trial {overall_trial_num}: Condition = {condition}, Set = {set_num}, "
                  f"SpecificTrial = {specific_trial_num}, Distance = {distance} cm, "
                  f"Speed = {speed} cm/s, ReferenceLevel = {variable_intensity}")

            # Initialize trial data dictionary
            trial_data = {
                'SubjectID': participant_name,
                'Condition': f"Condition {condition}",
                'OverallTrial': overall_trial_num,
                'SpecificTrial': specific_trial_num,
                'ProbeLevel': 4,  # Fixed at 4
                'ReferenceLevel': variable_intensity,
                'Response': '',
                'TrialDuration': ''
            }

            # Record the start time of the trial
            trial_start_time = time.time()

            # Control motors and send taps
            control_motors(distance, speed, variable_intensity, condition)

            # Get participant's response (except for Condition 8)
            if condition != 8:
                try:
                    response = get_foot_response()
                    trial_data['Response'] = response
                    # Update Quest algorithm based on response
                    quest_dict[quest_key].addResponse(1 if response == 'Yes' else 0)
                except Exception as e:
                    print(f"Error during response collection: {e}")
                    trial_data['Response'] = 'Error'

            # Record the end time of the trial
            trial_end_time = time.time()
            trial_duration = trial_end_time - trial_start_time
            trial_data['TrialDuration'] = round(trial_duration, 3)  # Rounded to milliseconds

            # Write trial data to CSV
            try:
                csv_writer.writerow(trial_data)
                csv_file.flush()  # Ensure data is written to disk immediately
                print("Trial data written to CSV.")
            except Exception as e:
                print(f"Error writing trial data to CSV: {e}")

        print("\nAll trials completed.")

    except KeyboardInterrupt:
        print("\nExperiment interrupted by user.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the CSV file if it's open
        try:
            if 'csv_file' in locals() and not csv_file.closed:
                csv_file.close()
                print("CSV file closed.")
        except Exception as e:
            print(f"Failed to close CSV file: {e}")

        # Close serial connection if open
        if serial_connected and ser and ser.is_open:
            ser.close()
            print("Serial connection closed.")

        # Quit Pygame
        pygame.quit()
        print("Pygame closed.")

        sys.exit()