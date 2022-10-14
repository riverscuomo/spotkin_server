import random


def getFact():
    # get the random fact
    with open(
        r"spotnik/data/data/randomfacts.txt",
        "r+",
        encoding="utf-8",
    ) as file:
        randomFactList = file.readlines()
        randomFactString = random.choice(randomFactList).strip()

        r"^\d{1,3}\."
    return randomFactString


# fact = getFact()
# print(fact)

# user_playlist_change_details(
#     user, playlist_id, name=None, public=None, collaborative=None, description=None
# )
