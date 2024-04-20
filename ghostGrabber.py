import time
import sys

track_abbrs = {0x24:"LC", 0x22:"PB",  0x21:"BP", 0x32:"DDD",
               0x28:"MB", 0x25:"MaC", 0x23:"DC", 0x2A:"WS",
               0x33:"SL", 0x29:"MuC", 0x26:"YC", 0x2D:"DKM",
               0x2B:"WC", 0x2C:"DDJ", 0x2F:"BC", 0x31:"RR"}

track_names = {"LC":"Luigi Circuit",   "PB":"Peach Beach",       "BP":"Baby Park",       "DDD":"Dry Dry Desert",
               "MB":"Mushroom Bridge", "MaC":"Mario Circuit",    "DC":"Daisy Cruiser",   "WS":"Waluigi Stadium",
               "SL":"Sherbet Land",    "MuC":"Mushroom City",    "YC":"Yoshi Circuit",   "DKM":"DK Mountain",
               "WC":"Wario Colosseum", "DDJ":"Dino Dino Jungle", "BC":"Bowser's Castle", "RR":"Rainbow Road"}

laps_dict   = {"BP":7, "WC":2}

region_dict = {"GM4E":"NTSC-U", "GM4J":"NTSC-J", "GM4P":"PAL"}

def grabGhost(filename) -> list[str]:
    """Takes an open ghost file and "grabs" it, returning a new filename and an output message"""

    ghost = open(filename, 'rb')

    def readInt(size):
        return int.from_bytes(ghost.read(size),"big")

    def readStr(size):
        return ghost.read(size).decode()


    ghost.seek(0x00) # Region Code
    region = region_dict.get(readStr(4), "")
    if not region:
        return null, "`Invalid game`"


    ghost.seek(0x28) # Date, stored as seconds since 1 Jan 2000
    timestamp = readInt(4) + 946684800
    date = time.strftime('%Y-%m-%d', time.gmtime(timestamp))


    ghost.seek(0x1483) # Track ID
    track_abbr = track_abbrs[readInt(1)]
    track = track_names[track_abbr]


    ghost.seek(0x1488) # Course time in ms
    course_time_ms = readInt(4)
    milliseconds = str(course_time_ms % 1000).zfill(3)
    seconds = str(int(course_time_ms/1000) % 60).zfill(2)
    minutes = str(int(course_time_ms/60000))
    message_time = minutes + ":" + seconds + "." + milliseconds
    file_time = minutes + "_" + seconds + "_" + milliseconds


    ghost.seek(0x1484) # Initials in ASCII
    initials = ghost.read(3).decode()


    ghost.seek(0x1490) # Splits in ms
    laps = laps_dict.get(track_abbr,3)
    lap_totals = [readInt(4)/1000 for __ in range(laps-1)]
    lap_totals.append(course_time_ms/1000)

    splits = [0 for __ in range(laps)]

    for i, t in reversed(list(enumerate(lap_totals))):
        if i > 0:
            splits[i] = (t - lap_totals[i-1])
        else:
            splits[i] = lap_totals[i]

    split_str = " / ".join(format(x,".3f") for x in splits)


    ghost.seek(0x148C) # Number of inputs
    total_inputs = (readInt(4) - 180) # Ignore 3-second countdown

    # Generator function for ghost controller inputs
    def input_generator(total_inputs):
        num = 0
        ghost.seek(0x1610) # Start of input data
        while num < total_inputs:
            yield num, readInt(2)
            num += 1

    # 2-byte input data format: 0x0   Analog stick Y (3 bits)
    #                           0x0.3 Analog stick X (5 bits)
    #                           0x1   Face buttons: Start,Z,R,L,Y,X,B,A (8 bits)

    XY_frames = [frame for frame, inputVal in input_generator(total_inputs) if inputVal & 0x000C]

    # Assumes shrooms are used first frame where X/Y pressed and next frame more than 1/3 second after
    shroom_times = [XY_frames[0]/60, next(frame/60 for frame in XY_frames if frame > (XY_frames[0] + 20))]

    shrooms = [0 for __ in range(laps)]
    for t in shroom_times:
        shroom_lap = 0
        while lap_totals[shroom_lap] < t:
            shroom_lap += 1
        shrooms[shroom_lap] += 1

    shrooms = "-".join(str(x) for x in shrooms)

    # Create filename string
    new_filename = track_abbr + "-" + date  + "-" + file_time + ".gci"

    # Create message string
    message = ["`========== Ghost Grabbed! ==========`"]

    message.append("`" + region.ljust(36-len(date)) + date + "`")
    message.append("`" + track.ljust(36) + "`")
    message.append("`" + initials.ljust(36-len(shrooms)) + shrooms + "`")

    if track_abbr == "BP":
        split_str2 = " / ".join(format(x,".3f") for x in splits[0:4])
        split_str = " / ".join(format(x,".3f") for x in splits[4:7])
        message.append("`" + split_str2.rjust(36) + "`")

    message.append("`" + message_time.ljust(36-len(split_str)) + split_str + "`")
    message.append("`====================================`")

    message = "\n".join(message)

    ghost.close()

    return new_filename, message

def changeRegion(filename, regionID):
    """Changes the region of a ghost file"""

    rdict = {"U":b'GM4E', "J":b'GM4J', "P":b'GM4P'}

    gameID = rdict.get(regionID)
    if gameID:
        ghost = open(filename, 'r+b')
        ghost.seek(0)
        ghost.write(gameID)
        ghost.close()
    return

if __name__ == '__main__':
    __, message = grabGhost(sys.argv[1])
    print(message)
