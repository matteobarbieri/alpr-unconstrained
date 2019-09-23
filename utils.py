import os


def guess_last_frame(input_folder):

    frame_numbers = [
        int(f[5:10]) for f in os.listdir(input_folder)
        if len(f) == 14 and f.endswith(".png")]

    last_frame = max(frame_numbers)

    # print(frame_numbers)

    return last_frame


def area(a, b):  # returns None if rectangles don't intersect

    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    # dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    # dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)

    dx = min(ax + aw, bx + bw) - max(ax, bx)
    dy = min(ay + ah, by + bh) - max(ay, by)

    if dx >= 0 and dy >= 0:
        return dx * dy


def iterative_levenshtein(s, t):
    """
        iterative_levenshtein(s, t) -> ldist
        ldist is the Levenshtein distance between the strings
        s and t.
        For all i and j, dist[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    rows = len(s)+1
    cols = len(t)+1
    dist = [[0 for x in range(cols)] for x in range(rows)]
    # source prefixes can be transformed into empty strings
    # by deletions:
    for i in range(1, rows):
        dist[i][0] = i
    # target prefixes can be created from an empty source string
    # by inserting the characters
    for i in range(1, cols):
        dist[0][i] = i

    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0
            else:
                cost = 1
            dist[row][col] = min(dist[row-1][col] + 1,       # deletion
                                 dist[row][col-1] + 1,       # insertion
                                 dist[row-1][col-1] + cost)  # substitution

    return dist[row][col]


def compute_center_coordinates(bb):
    """
    Computes the coordinates of the center of a rectangular region

    bb = [x, y, w, h]
    """

    cx = bb[0] + bb[2]/2
    cy = bb[1] + bb[3]/2

    return cx, cy
