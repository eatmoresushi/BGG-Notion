import requests
import xml.etree.ElementTree as ET
import time

BGG_API = "https://www.boardgamegeek.com/xmlapi2"
BGG_LINK_BASE = "https://boardgamegeek.com/boardgame/"
BGG_USERNAME = ""
COLLECTION = "/collection"
NOTION_SECRET = ""
DATABASE_ID = ""
BGG_COLLECTION_FILE = ""
ALL_GAMES_COL = {}


def get_collection():
    # get my collection from bgg
    while True:
        bgg_response = requests.get(
            BGG_API + COLLECTION,
            params={
                "username": BGG_USERNAME,
                "excludesubtype": "boardgameexpansion",
                "stats": 1,
                "own": 1,
            },
        )
        if bgg_response.status_code == 200:
            break
        time.sleep(5)
    BGG_COLLECTION_FILE = "colbgg.xml"
    with open(BGG_COLLECTION_FILE, "w") as f:
        f.write(bgg_response.text)


def parse_xml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    for child in root:
        # content list = [name, image, type, rank, average, my_rating, review, link]
        name = child.find("name").text
        image = child.find("image").text
        types = child.findall("./stats/rating/ranks/rank")
        try:
            rank = int(types[0].get("value"))
        except ValueError:
            rank = -1
        sub_types = []
        for t in types[1:]:
            sub_types.append(t.get("name").replace("games", "").capitalize())
        average = child.find("./stats/rating/average").get("value")
        my_rating = child.find("./stats/rating").get("value")
        try:
            review = child.find("comment").text
        except AttributeError:
            review = ""
        link = BGG_LINK_BASE + child.get("objectid")
        ALL_GAMES_COL[f"{child.get('objectid')}"] = [
            name,  # 0
            image,  # 1
            sub_types,  # 2
            rank,  # 3
            round(float(average), 1),  # 4
            float(my_rating) if my_rating != "N/A" else None,  # 5
            review,  # 6
            link,  # 7
        ]


def add_to_notion():
    notion_headers = {
        "Authorization": f"Bearer {NOTION_SECRET}",
        "Content-Type": "application/json",
        "Notion-Version": "2021-08-16",
    }

    for k in ALL_GAMES_COL:
        notion_data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "title": {"title": [{"text": {"content": ALL_GAMES_COL[k][0]}}]},
                "Img": {
                    "files": [
                        {
                            "type": "external",
                            "name": "cover",
                            "external": {"url": ALL_GAMES_COL[k][1]},
                        }
                    ]
                },
                "Overall Rank": {"number": ALL_GAMES_COL[k][3]},
                "BGG Average": {"number": ALL_GAMES_COL[k][4]},
                "Review": {"rich_text": [{"text": {"content": ALL_GAMES_COL[k][6]}}]},
                "BGG": {"url": ALL_GAMES_COL[k][7]},
            },
        }
        if ALL_GAMES_COL[k][5]:
            notion_data["properties"]["My Rating"] = {"number": ALL_GAMES_COL[k][5]}
        type_list = []
        for i in range(len(ALL_GAMES_COL[k][2])):
            type_list.append({"name": ALL_GAMES_COL[k][2][i]})
        notion_data["properties"]["Type"] = {"multi_select": type_list}
        response = requests.post(
            "https://api.notion.com/v1/pages", headers=notion_headers, json=notion_data
        )


def main():
    NOTION_SECRET = input("Please enter your Notion API secret: ")
    DATABASE_ID = input("Please enter your Notion database ID: ")
    BGG_USERNAME = input("Please enter your BGG username: ")
    BGG_COLLECTION_FILE = input(
        "Please enter your BGG collection file, enter 'n' to download your collection from BGG: "
    )
    if BGG_COLLECTION_FILE == "n":
        get_collection()
    parse_xml(BGG_COLLECTION_FILE)
    add_to_notion()


if __name__ == "__main__":
    main()
