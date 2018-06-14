def coord_to_nesw(lon, lat):
    # Lon
    lon_dir = "E"
    if lon < 0:
        lon = abs(lon)
        lon_dir = "W"
    lon_degs = int(lon)
    rem = (lon - lon_degs) * 60
    lon_mins = int(rem)
    lon_secs = (rem - lon_mins) * 60
    full_lon = "{:0>2.0f}°{:0>2.0f}'{:0>5.2f}\"{}".format(lon_degs,
                                                          lon_mins,
                                                          lon_secs,
                                                          lon_dir,
                                                          )
    # Lat
    lat_dir = "N"
    if lat < 0:
        lat = abs(lat)
        lat_dir = "S"
    lat_degs = int(lat)
    rem = (lat - lat_degs) * 60
    lat_mins = int(rem)
    lat_secs = (rem - lat_mins) * 60
    full_lat = "{:0>2.0f}°{:0>2.0f}'{:0>7.4f}\"{}".format(lat_degs,
                                                          lat_mins,
                                                          lat_secs,
                                                          lat_dir,
                                                          )
    return "{} {}".format(full_lon, full_lat)


def nesw_to_coord(nesw):
    nesw = nesw.replace(" ", "")
    N = ""
    E = ""
    S = ""
    W = ""
    buffer = ""
    for c in nesw:
        if c == "N":
            N = buffer
            buffer = ""
        elif c == "E":
            E = buffer
            buffer = ""
        elif c == "S":
            S = buffer
            buffer = ""
        elif c == "W":
            W = buffer
            buffer = ""
        else:
            buffer += c
    assert ("" in (N, S)) and ("" in (E, W))

    if S == "":
        lat_dir = "N"
        lat_str = N
    else:
        lat_dir = "S"
        lat_str = S
    if W == "":
        lon_dir = "E"
        lon_str = E
    else:
        lon_dir = "W"
        lon_str = W

    lon_degs, lon_mins, lon_secs = multi_split(lon_str, ("°", "'", '"'))
    lon = round(sum([float(lon_degs), float(lon_mins) / 60, float(lon_secs) / 3600]), 10)
    lat_degs, lat_mins, lat_secs = multi_split(lat_str, ("°", "'", '"'))
    lat = round(sum([float(lat_degs), float(lat_mins) / 60, float(lat_secs) / 3600]), 10)
    assert (lon >= 0.0) and (lat >= 0.0)

    if lon_dir == "W":
        lon = lon.__neg__()
    else:
        pass
    if lat_dir == "S":
        lat = lat.__neg__()
    else:
        pass

    return lon, lat


def multi_split(text, seps=(",",)):
    output = [text]
    for s in seps:
        new_output = []
        for o in output:
            res = o.split(s)
            for r in res:
                new_output.append(r)
        output = new_output
    for i in range(output.count("")):
        output.remove("")
    return output



