# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


def log(message):
    print("=============================================")
    print(message)
    # print("=============================================")
