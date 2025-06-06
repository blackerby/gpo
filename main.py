from datetime import date, datetime, timedelta, timezone
import os

import polars as pl
import polars_capitol as cap
import httpx
import streamlit as st


BASE_URL = "https://api.govinfo.gov/collections"
PAGE_SIZE = 1000
OFFSET_MARK = "*"
TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)
CURRENT_CONGRESS = (date.today().year - 1789) // 2 + 1
COLLECTIONS = {
    "Bills": "bills",
    "Public Laws": "plaw",
    "Committee Reports": "crpt",
    "Committee Prints": "cprt",
    "Congressional Hearings": "chrg",
}
API_KEY = os.environ.get("GPO_API_KEY", "DEMO_KEY")
HEADERS = {"X-Api-Key": API_KEY}
TITLE = "New/Updated Data from GPO"

st.set_page_config(page_title=TITLE, layout="wide")


def timestamp_from_date(date: date) -> str:
    return (
        datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)  # type: ignore
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


# Report starts here
st.title(TITLE)

collection_selection = st.selectbox("Choose a GPO collection", COLLECTIONS.keys())
collection = COLLECTIONS[collection_selection]

congress = st.selectbox("Choose Congress", reversed(range(1, CURRENT_CONGRESS + 1)))

start_date = st.date_input("Start date", YESTERDAY, format="YYYY-MM-DD")
start_timestamp = timestamp_from_date(start_date)  # type: ignore
end_date = st.date_input("End date", TOMORROW, format="YYYY-MM-DD")
end_timestamp = timestamp_from_date(end_date)  # type: ignore

url = f"{BASE_URL}/{collection}/{start_timestamp}/{end_timestamp}?congress={congress}&pageSize={PAGE_SIZE}&offsetMark={OFFSET_MARK}"


@st.cache_data
def get_data(url):
    response = httpx.get(url, headers=HEADERS)
    data = response.json()

    packages = data["packages"]

    while next_page := data["nextPage"]:
        response = httpx.get(next_page, headers=HEADERS)
        data = response.json()
        packages.extend(data["packages"])

    return packages


packages = get_data(url)
df = pl.DataFrame(packages)
st.header(collection_selection)
if len(df) > 0:
    df = df.with_columns(
        pl.concat_str([pl.col("packageLink"), pl.lit("?api_key=DEMO_KEY")])
    )

    if collection in ["bills", "cprt", "crpt"]:
        s = pl.col("packageId").str.split(by="-").list.get(1, null_on_oob=True)
        expr = cap.cdg_url(s)
        df = df.with_columns(cdg_url=expr).select(
            [
                "packageId",
                "congress",
                "docClass",
                "lastModified",
                "title",
                "packageLink",
                "cdg_url",
            ]
        )

        if collection == "bills":
            version = cap.version(s)
            df = df.with_columns(version=version)

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "packageLink": st.column_config.LinkColumn(),
            "cdg_url": st.column_config.LinkColumn(),
        },
    )
st.subheader(f"Total: {len(df)}")

if collection in ["cprt", "crpt", "chrg"]:
    if "docClass" in df.columns:
        house = len(df.filter(pl.col("docClass").str.starts_with("H")))
        senate = len(df.filter(pl.col("docClass").str.starts_with("S")))
        joint = len(df.filter(pl.col("docClass").str.starts_with("J")))

        st.markdown(f"""
            |Type|Count|
            |---------|-----------|
            |House    |{house}    |
            |Senate   |{senate}   |
            |Joint    |{joint}|
        """)

if collection == "bills":
    if "version" in df.columns:
        st.dataframe(df.group_by("version").len())
