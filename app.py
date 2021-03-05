#!/usr/bin/env python3
import selenium.webdriver as wd

import etebase
import icalendar as ic
import datetime as dt
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from pydash import _

from credentials import ete_username, ete_password, cookies, gym_id


def add_event(
    title: str, description: str, location: str, start: dt.datetime, end: dt.datetime
):
    """
    Creates a simple event in etesync calendar
    """
    cm = etesync.get_collection_manager()
    collection: etebase.Collection = cm.list(
        "etebase.vevent"
    ).data.__next__()  # get the first calendar
    items = cm.get_item_manager(collection)

    cal = ic.Calendar()
    ev = ic.Event(
        summary=title,
        description=description,
        location=location,
        gensecgen="yes",
        dtstart=ic.vDatetime(start),
        dtend=ic.vDatetime(end),
    )
    cal.subcomponents.append(ev)
    item = items.create({}, cal.to_ical())
    items.batch([item])


def clear_generated():
    """
    Removes all events created with `add_event`
    """
    cm = etesync.get_collection_manager()
    collection: etebase.Collection = cm.list("etebase.vevent").data.__next__()
    items = cm.get_item_manager(collection)

    deleted = []
    for item in items.list().data:

        cal: ic.Calendar = ic.Calendar.from_ical(str(item.content, "utf-8"))
        if cal.subcomponents[0].get("GENSECGEN") == ic.vText("yes"):
            item.delete()
            deleted.append(item)
    items.batch(deleted)


def update_csrf():  # not used for now
    headless = wd.firefox.options.Options()
    headless.add_argument("--headless")
    profile = wd.firefox.firefox_profile.FirefoxProfile()
    browser = wd.Firefox(
        # options=headless,
        firefox_profile=profile
    )
    browser.get("https://my.worldclass.ru/schedule")
    for f in (_(cookies.items()).map(lambda a: {"name": a[0], "value": a[1]})).value():
        print(f)
        browser.add_cookie(f)
    browser.get("https://my.worldclass.ru/")
    return browser.find_element_by_name("_csrf").get_property("value")


def update_csrf_hls():
    rq = requests.get(
        "https://my.worldclass.ru/",
        headers={"Accept": "*/*", "language": "En", "chain": "1"},
        cookies=cookies,
    ).text
    soup = BeautifulSoup(rq, features="html5lib")
    return soup.find("input", {"name": "_csrf"})["value"]


def get_gym_events(s: dt.datetime, e: dt.datetime):
    return requests.post(
        "https://my.worldclass.ru/api/v1/clubs/schedule",
        json={
            "gymList": [gym_id],
            "startDate": s.isoformat(),
            "endDate": e.isoformat(),
            "chain": 1,
        },
        cookies=cookies,
        headers={
            "Accept": "*/*",
            "language": "En",
            "chain": "1",
            "x-csrf-token": csrf,
        },
    ).json()["data"]


def reserve(doc_id: str):
    return (
        requests.post(
            "https://my.worldclass.ru/api/v1/schedule/registration",
            json={"docId": doc_id, "type": "reserve"},
            cookies=cookies,
            headers={
                "Accept": "*/*",
                "language": "En",
                "chain": "1",
                "x-csrf-token": csrf,
                "referrer": f"https://my.worldclass.ru/schedule?event={doc_id}",
            },
        ).status_code
        == 200
    )


def add_workout(event):
    start = dt.datetime.fromisoformat(event["startDate"])
    end = dt.datetime.fromisoformat(event["endDate"])
    name = event["service"]["name"]

    print(
        f"Reserving {name} [{start.date()} {start.time()} - {end.time()}] in WorldClass..."
    )
    reserve(event["docId"])

    print(
        f"Adding {name} [{start.date()} {start.time()} - {end.time()}] to calendar..."
    )
    add_event(
        title=name,
        description=(event["service"]["shortDescription"]),
        location=(event["room"]["name"]),
        start=start,
        end=end,
    )


print("Updating csrf...")
csrf = update_csrf_hls()
print("Logging in to EteSync...")
etesync = etebase.Account.login(etebase.Client("gensec"), ete_username, ete_password)
print("Fetching WorldClass schedule...")
start = dt.datetime.now()
start.replace(hour=0, minute=0, second=0)
event_list = get_gym_events(start, start + dt.timedelta(days=1))

# ===== Write after this line

# Call if you need to dispose of your test events
# clear_generated()

# Call to schedule and add workout to calendar
# add_workout(event)

(
    _(event_list)
    .filter(lambda a: a["canRecord"] and not a["recorded"])
    .filter(lambda a: a["service"]["name"] == "BodyPump")
    .filter(lambda a: dt.datetime.fromisoformat(a["startDate"]).hour < 24)
    .for_each(add_workout)
    .value()
)