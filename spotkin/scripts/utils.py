# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i: i + n]


def log(message: str):
    if not isinstance(message, str):
        message = str(message)
    with open("log.txt", "a") as file:
        file.write("=============================================\n")
        file.write(message + "\n")
        print(message)

        # file.write("=============================================\n")
