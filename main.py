import polars as pl
import polars_capitol as cap
import streamlit as st
from govinfo import GovInfo

from constants import (
    API_KEY,
    COLLECTIONS,
    CURRENT_CONGRESS,
    PAGE_SIZE,
    TITLE,
    TOMORROW,
    YESTERDAY,
)
from helpers import timestamp_from_date

st.set_page_config(page_title=TITLE, layout="wide")


# Report starts here
st.title(TITLE)

collection_selection = st.selectbox("Choose a GPO collection", COLLECTIONS.keys())
collection = COLLECTIONS[collection_selection]
congress = st.selectbox("Choose Congress", reversed(range(1, CURRENT_CONGRESS + 1)))
start_date = st.date_input("Start date", YESTERDAY, format="YYYY-MM-DD")
end_date = st.date_input("End date", TOMORROW, format="YYYY-MM-DD")

start_timestamp = timestamp_from_date(start_date)  # type: ignore
end_timestamp = timestamp_from_date(end_date)  # type: ignore
govinfo = GovInfo(api_key=API_KEY)


@st.cache_data
def get_dataframe(collection, start_timestamp, end_timestamp, congress, page_size):
    data = govinfo.collection(
        collection,
        start_timestamp,
        end_timestamp,
        congress=congress,
        page_size=page_size,
    )
    df = pl.DataFrame(data)

    return df


df = get_dataframe(collection, start_timestamp, end_timestamp, congress, PAGE_SIZE)

st.header(collection_selection)

if len(df) > 0:
    df = df.with_columns(
        pl.concat_str([pl.col("package_link"), pl.lit("?api_key=DEMO_KEY")])
    )

    if collection in ["bills", "cprt", "crpt"]:
        s = pl.col("package_id").str.split(by="-").list.get(1, null_on_oob=True)
        expr = cap.cdg_url(s)
        df = df.with_columns(cdg_url=expr).select(
            [
                "package_id",
                "congress",
                "doc_class",
                "last_modified",
                "title",
                "package_link",
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
            "package_link": st.column_config.LinkColumn(),
            "cdg_url": st.column_config.LinkColumn(),
        },
    )
st.subheader(f"Total: {len(df)}")

if collection in ["cprt", "crpt", "chrg"]:
    if "doc_class" in df.columns:
        house = len(df.filter(pl.col("doc_class").str.starts_with("H")))
        senate = len(df.filter(pl.col("doc_class").str.starts_with("S")))
        joint = len(df.filter(pl.col("doc_class").str.starts_with("J")))

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
