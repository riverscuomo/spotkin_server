import argparse
import pygsheets  # pip3 install pygsheets


SHEET_URL = "https://docs.google.com/spreadsheets/d/1z5MejG6EKg8rf8vYKeFhw9XT_3PxkDFOrPSEKT_jYqI/edit#gid=1936655481"
SHEET_TITLE = "Spotify Controller"


def copy_sheet(service_file, gmail):
	gc = pygsheets.authorize(service_file=service_file)

	template_sh = gc.open_by_url(SHEET_URL)
	copied_sh = gc.create(title=SHEET_TITLE, template=template_sh)

	# optionally remove "validation" worksheet
	val_wks = [wks for wks in copied_sh.worksheets() if wks.title == "validation"]
	if (val_wks):
	    copied_sh.del_worksheet(val_wks[0])

	copied_sh.share(gmail)
	print('shared sheet "%s" to %s' % (SHEET_TITLE, gmail))
	return


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='copy sheet')
	parser.add_argument('service_file', type=str, help='path to auth service file')
	parser.add_argument('gmail', type=str, help='gmail to share to')
	args = parser.parse_args()

	copy_sheet(args.service_file, args.gmail)
