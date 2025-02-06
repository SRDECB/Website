import streamlit as st

import pandas as pd

import tabula

from io import BytesIO

 

def df_init(path):

    table = tabula.read_pdf(path, pages='all', multiple_tables=True)

    table = table[0]

    df = pd.DataFrame(table)

    df.columns = [f"col{i}" for i, col in enumerate(df.columns)]

    return df

 

def clean_df(df):

    idx = df[df.iloc[:,0] == "Test Values"].index[0]

    series = df.loc[idx, :]

    filtered_columns = {

        col: len(value.split(" "))  

        for col, value in zip(series.index, series) if col != "col0" and len(value.split(" ")) > 1

    }

    for key, value in filtered_columns.items():

        split_columns = df[key].str.split(expand=True, n=value-1)

        split_columns.columns = [f"{key}_{i+1}" for i in range(value)]

        df = df.drop(columns=[key])

        df = pd.concat([df, split_columns], axis=1)

    return df

 

def subtable(df, col1, col2):

    start_idx = df[df.iloc[:,0] == col1].index[0]

    end_idx = df[df.iloc[:,0] == col2].index[0] - 1

    subtable = df.loc[start_idx:end_idx]

    subtable = subtable.reset_index(drop=True)

    subtable.iloc[:, 1:] = subtable.iloc[:, 1:].astype(float)

    fixed_cols = ["col0"]

    sorted_cols = sorted(subtable.columns.difference(fixed_cols), key=lambda col: subtable[col][0])

    subtable = subtable[fixed_cols + sorted_cols]

    return subtable

 

def process_pdf(uploaded_file):

    df = df_init(uploaded_file)

    df = clean_df(df)

    sub_df1 = subtable(df, 'Test Values', 'Reference')

    sub_df2 = subtable(df, 'Reference', 'Difference')

    sub_df3 = sub_df1.copy()

    sub_df3.loc[0, 'col0'] = "Difference"

    sub_df3.loc[1:, 'col1':] = 100 * (sub_df3.loc[1:, 'col1':] - sub_df2.loc[1:, 'col1':]) / sub_df2.loc[1:, 'col1':]

    all_df = pd.concat([sub_df1, sub_df2, sub_df3], axis=0)

    all_df.reset_index(inplace=True, drop=True)

    return all_df

 

st.title("PDF to CSV Converter")

uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])

if uploaded_file is not None:

    df = process_pdf(uploaded_file)

    csv_buffer = BytesIO()

    df.to_csv(csv_buffer, index=False)

    csv_buffer.seek(0)

    st.download_button("Download CSV", csv_buffer, "output.csv", "text/csv")