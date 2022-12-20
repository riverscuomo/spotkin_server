import os, random, base64

def getImage():
    # get random image cover
    imgDir = "spotnik/data/images/"
    randomImage = random.choice(os.listdir(imgDir))

    with open(imgDir + randomImage, "rb") as img_file:
        my_string = base64.b64encode(img_file.read())
    
    return my_string.decode('utf-8')

def update_cover(spotify, job):
    if job['randomize_cover']:
        
        image = getImage()
        spotify.playlist_upload_cover_image(
            job["playlist_id"], image_b64=image
        )
