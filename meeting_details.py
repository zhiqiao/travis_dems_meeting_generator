import bs4
import csv
import re
import sys
import urllib
import urllib2

MEETINGS_URL = "http://www.traviscountydemocrats.org/people/democratic-clubs/"

USAGE_MSG = ("Usage: meeting_details.py fetch"
             " OR "
             " meeting_details.py open <filename>")

GOOGLE_MAPS_PREFIX = "https://maps.google.com/maps?"

HEADERS = ["Org Name", "Website", "Meetings", "Address"]


class InvalidContentException(Exception):
    pass


def GetRawContentFromUrl(url):
    return urllib2.urlopen(url).read()


def ParseRawContent(content):
    """
    Returns:
      A list of lists of string.
    """
    soup = bs4.BeautifulSoup(content)
    results = soup.find_all("div", "box")
    if not results: 
        raise InvalidContentsException(soup.prettify())
    club_div = results[0]
    all_clubs = []
    for p in club_div.find_all("p"):
        all_clubs.append(ParseClubContent(p))
    return all_clubs


def _CleanupString(input_str):
    return input_str.strip().encode("utf-8", "ignore")


def ParseClubContent(club_content):
    content_list = []
    curr = club_content.contents[0]
    # First element should be the club's name (with website, if available)
    content_list.extend(ParseClubName(curr))
    curr = _AdvanceToNextContent(curr)
    content_list.extend(ParseMeetingSchedule(curr))
    curr = _AdvanceToNextContent(curr)
    address_fragments = []
    while curr and curr.find("Contact:") < 0:
        if isinstance(curr, bs4.element.NavigableString):
            # Do not add other tags.
            address_fragments.append(curr)
        else:
            break
        curr = _AdvanceToNextContent(curr)
    content_list.extend(ParseAddress(address_fragments))
    return [_CleanupString(s) for s in content_list]


def _AdvanceToNextContent(curr):
    curr = curr.next_sibling
    # Find next non-empty element, which should be the meeting schedule:
    while (isinstance(curr, bs4.element.Tag)
           and (curr.is_empty_element or not curr.text.strip())):
        curr = curr.next_sibling
    return curr

        
def ParseMeetingSchedule(club_schedule_tag):
    # TODO(zhi):  Parse this into a date/time.
    return ["%s" % club_schedule_tag]


def ParseAddress(addr_fragments):
    return [", ".join([s.replace(" (", "").strip() for s in addr_fragments])]


def AddMapsUrl(addr):
    return "%s%s" % (GOOGLE_MAPS_PREFIX, urllib.urlencode([("q", addr)]))


def ParseClubName(club_name_tag):
    """Parses a tag including the name of the club and possible website link.

    Args:
      club_name_tag:  A bs4.element

    Returns:
      A list of string ["<name>", "<website url>"], where <website url> may be
      an empty string.
    """
    name = ""
    website = ""
    if isinstance(club_name_tag, bs4.element.Tag):
        name = club_name_tag.text
        website = club_name_tag.get("href", "")
    elif isinstance(club_name_tag, bs4.element.NavigableString):
        name = "%s" % club_name_tag
    else:
        # Default treat as string.
        # TODO(zhi):  Do something else here.
        name = "%s" % club_name_tag
    return [name.strip().rstrip(":"), website]


def UsageAndExit():
    print USAGE_MSG
    sys.exit()


def main(argv):
    if len(argv) < 2:
        UsageAndExit()

    cmd = argv[1]
    raw_content = ""

    if cmd == "fetch":
        raw_content = GetRawContentFromUrl(MEETINGS_URL)
    elif cmd == "open":
        if len(argv) < 3:
            UsageAndExit()
        f = open(argv[2], "r")
        raw_content = f.read()
        f.close()
    else:
        UsageAndExit()

    if raw_content:
        rows = ParseRawContent(raw_content)
        output = open("output.csv", "w")
        csv_output = csv.writer(output)
        csv_output.writerow(HEADERS)
        for r in rows:
            csv_output.writerow(r)
        output.close()


if __name__ == '__main__':
    main(sys.argv)
