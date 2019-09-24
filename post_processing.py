import numpy as np

from utils import (area, iterative_levenshtein, compute_center_coordinates)


def process_annotations(annotations_history, i, window, keep_invalid=False):
    """
    Process annotation for a given frame trying to correct wrong/missing data

    Parameters
    ----------

    annotations : dict
        Dictionary containing detections already pruned from duplicates
    """

    # Create a list of all cars and plates detected _in current frame_
    cars = list()
    plates = list()

    for car in annotations_history[i]['cars']:

        # print(car)
        car_cp = dict(car)

        # Empty list of plates
        car_cp['plates'] = list()
        cars.append(car_cp)

        # Update the list of plates
        plates.extend(car['plates'])

    plates = recover_missing_plates(
        annotations_history, i, plates, window, 3)

    # print("After recover_missing_plates:")
    # print("# of plates: {}".format(len(plates)))
    # for p in plates:
        # print(p['plate_text'])

    if not keep_invalid:
        # Remove invalid plates
        plates = remove_invalid_plates(plates)

    # print("After remove_invalid_plates:")
    # print("# of plates: {}".format(len(plates)))
    # for p in plates:
        # print(p['plate_text'])

    # Remove duplicate plates (i.e., those overlapping) by keeping those more
    # likely to be correct
    plates_unique = remove_duplicate_plates(plates, annotations_history)

    # Finally asociate plate to vehicle
    cars = associate_plate_to_vehicle(cars, plates_unique)

    return {'cars': cars}


def choose_best_alternative(current_plate, new_plate_code,
                            plates_past, plates_future):
    """
    current plate is a full plate dict, new_plate_code is just a string
    """

    # If current plate is not valid, return the other one
    if not current_plate['valid_plate']:
        return new_plate_code

    old_plate_code = current_plate['plate_text']

    # If both are valid, return the one that has appeared most frequently
    n_old = 0
    if old_plate_code in plates_past:
        n_old += len(plates_past[old_plate_code]['bb'])
    if old_plate_code in plates_future:
        n_old += len(plates_future[old_plate_code]['bb'])

    n_new = 0
    if new_plate_code in plates_past:
        n_new += len(plates_past[new_plate_code]['bb'])
    if new_plate_code in plates_future:
        n_new += len(plates_future[new_plate_code]['bb'])

    if n_old > n_new:
        return old_plate_code
    else:
        return new_plate_code


def recover_missing_plates(annotations_history, i, plates, window,  # noqa
                           min_occurrences):
    """
    Use the previous and following N frames to recover plates in current frame
    """

    plates_past = dict()
    plates_future = dict()

    # past
    for i in range(i-window, i):
        for car in annotations_history[i]['cars']:
            for plate in car['plates']:

                if not plate['valid_plate']:
                    continue

                pt = plate['plate_text']

                if pt in plates_past:
                    plates_past[pt]['seen_at'].append(i)
                    plates_past[pt]['bb'][i] = plate['bounding_box']
                else:
                    plates_past[pt] = dict()
                    plates_past[pt]['seen_at'] = [i]
                    plates_past[pt]['bb'] = {}  # bounding boxes
                    plates_past[pt]['bb'][i] = plate['bounding_box']

    # future
    for i in range(i+1, i+1+window):
        for car in annotations_history[i]['cars']:
            for plate in car['plates']:

                if not plate['valid_plate']:
                    continue

                pt = plate['plate_text']

                if pt in plates_future:
                    plates_future[pt]['seen_at'].append(i)
                    plates_future[pt]['bb'][i] = plate['bounding_box']
                else:
                    plates_future[pt] = dict()
                    plates_future[pt]['seen_at'] = [i]
                    plates_future[pt]['bb'] = {}  # bounding boxes
                    plates_future[pt]['bb'][i] = plate['bounding_box']

    # Find plates with a valid code that appear before AND after current frame
    common_plate_codes = set(plates_future).intersection(set(plates_past))

    # TODO DEBUG
    # print("Plates at current frame:")
    # # print(plates)
    # print([p['plate_text'] for p in plates])

    # print("License plates found in surrounding frames.")
    # print(common_plate_codes)

    plates_recovered = 0
    plates_fixed = 0

    for plate_code in common_plate_codes:
        # In order to be added it must not be already present in current
        # license plates and have appeared a minimum number of times in
        # previous and future frames.

        # Find the index of the license plate in the list of the ones found in
        # current frame that most resembles the one found in both future and
        # past frames.
        mspi = most_similar_plate(plate_code, plates)

        # If in the past there is a better version of the plate, replace the
        # code of the one in the current frame (XXX experimental)
        # This assumes that only valid plates are present in the lists of those
        # retrieved from future and past.
        if mspi is not None:

            # TODO debug remove
            # print("Replacing {} with {}".format(
                # plates[mspi]['plate_text'], plate_code))

            best_plate_alternative = choose_best_alternative(
                plates[mspi], plate_code, plates_past, plates_future)

            # plates[mspi]['plate_text'] = plate_code
            plates[mspi]['plate_text'] = best_plate_alternative

            if best_plate_alternative == plate_code:
                plates_fixed += 1

            # Plate is now valid, since it has been replaced with a code that
            # we know is valid!
            plates[mspi]['valid_plate'] = True
            continue

        # If no match with a plate from current frame is found, this means
        # (probably) that for some reason it is not visible in current frame.
        # However, it may be possible to estimate its current position if it
        # had appeared a given number of times in past/it will appear in future
        # frames.
        if (
                len(plates_past[plate_code]['bb']) >= min_occurrences and
                len(plates_future[plate_code]['bb']) >= min_occurrences):

            # Retrieve the last frame in which the plate was seen in previous
            # frames and the first in which it was seen in future ones.
            i_past = max(plates_past[plate_code]['seen_at'])
            i_future = min(plates_future[plate_code]['seen_at'])

            # Retrieve the bounding boxes for those instants
            bb_past = plates_past[plate_code]['bb'][i_past]
            bb_future = plates_future[plate_code]['bb'][i_future]

            # compute temporal displacement
            dt = i_future - i_past

            xc_past, yc_past = compute_center_coordinates(bb_past)
            xc_future, yc_future = compute_center_coordinates(bb_future)

            dx = (xc_future - xc_past)
            dy = (yc_future - yc_past)

            # Approximate bounding box at current frame
            bb_current = list(bb_past)  # Start from last seen bounding box
            bb_current[0] += (i_past - i)*(dx/dt)
            bb_current[1] += (i_past - i)*(dy/dt)

            # Create the entry for the reconstructed plate
            new_plate = {
                'bounding_box': bb_current,
                'valid_plate': True,
                'plate_text': plate_code,
            }

            plates.append(new_plate)

            plates_recovered += 1

    print("Recovered {} plates".format(plates_recovered))
    # print("Fixed {} plates".format(plates_fixed))

    return plates


def remove_invalid_plates(plates):
    """
    Simply return only pates whose code is valid.
    """

    return [p for p in plates if p['valid_plate']]


def remove_duplicate_plates(plates, annotations_history):

    excluded_plates_indexes = list()
    unique_plates_list = list()

    for i in range(len(plates)):

        # If it has been already excluded, skip
        if i in excluded_plates_indexes:
            continue

        p1 = plates[i]

        for j in range(i+1, len(plates)):

            p2 = plates[j]

            # Handle collision
            if area(p1['bounding_box'], p2['bounding_box']) is not None:

                # If they're the same skip the other one
                if p1['plate_text'] == p2['plate_text']:
                    excluded_plates_indexes.append(j)

                if p1['valid_plate'] and not p2['valid_plate']:
                    # If the first one is valid and the second one isn't,
                    # remove the second one.
                    excluded_plates_indexes.append(j)
                elif not p1['valid_plate'] and p2['valid_plate']:
                    # If the first one is NOT valid and the second one is
                    # valid, break the inner loop, thus preventing the first
                    # one to be added (it's the else part of the loop).
                    break
                else:
                    # Choose the one that appeared more frequently in the past
                    # TODO
                    excluded_plates_indexes.append(j)
        else:

            unique_plates_list.append(p1)

    return unique_plates_list


def associate_plate_to_vehicle(cars, plates):
    """
    Associate each plate to the closest available vehicle.

    Also check that the bounding box of the license plate is inside the
    bounding box of the car it is assigned to.
    """

    # Keep track of indexes of cars that have already been assigned
    unavailable_cars_indexes = list()

    for p in plates:
        min_dist = np.inf

        px, py = compute_center_coordinates(p['bounding_box'])

        for ic, car in enumerate(cars):

            # Skip vehicles that have already been assigned a plate
            if ic in unavailable_cars_indexes:
                continue

            # Compute coordinates of the center of the vehicle's bb
            cx, cy = compute_center_coordinates(car['bounding_box'])

            dist = (cx - px)**2 + (cy - py)**2
            if dist < min_dist:
                min_dist = dist
                min_dist_car_index = ic

        # If a suitable car has been found AND there is an overlap between the
        # bounding boux of the license plate and the one of the closest car, do
        # proceed to assign that license plate to that car.
        if (min_dist != np.inf and
            area(p['bounding_box'],
                 cars[min_dist_car_index]['bounding_box']) is not None):

            # Assign plate to the closest available car
            cars[min_dist_car_index]['plates'] = [p]

            # Mark car as unavailable
            unavailable_cars_indexes.append(min_dist_car_index)

    return cars


def most_similar_plate(target_plate, plate_list, max_distance=2):
    """
    Given a target license plate and a list of candidate plates, find the one
    from the list which is at a distance of at most D from the target plate.

    Returns the index of the most similar plate

    Parameters
    ----------

    target_plate : str

    plate_list : list
        Each item is a dictionary
    """

    min_distance = np.inf
    mspi = None

    # TODO catch errors properly
    try:
        for i, p in enumerate(plate_list):
            ld = iterative_levenshtein(target_plate, p['plate_text'])

            if ld <= max_distance and ld < min_distance:
                min_distance = ld
                mspi = i
    except:  # noqa
        pass

    return mspi
