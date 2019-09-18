import os

def guess_last_frame(input_folder):


    frame_numbers = [int(f[5:10]) for f in os.listdir(input_folder) if len(f) == 14 and f.endswith(".png")]

    last_frame = max(frame_numbers)

    # print(frame_numbers)

    return last_frame
