import datetime

def generateUserId():
    ct = datetime.datetime.now()
    ct = str(ct).split(" ")
    date, time = ct[0], ct[1]
    date = "".join(date.split("-"))
    time = time.split(":")
    sec = time[-1].split(".")
    time.pop(2)
    time = "".join(time)
    sec = "".join(sec)
    date += (time + sec)

    return date