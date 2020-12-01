import json
import pandas as pd
import numpy as np
from dateutil import parser


class sheet_module:

  def __init__(self):
    self.raw_data = None

  def parse_data(self, data):
    print('parse_data', data)

    # create sheet DF
    sheet_data_headers = data[0:1][0]
    sheet_data_rows = data[1:]

    sheet_df = pd.DataFrame(sheet_data_rows, columns=sheet_data_headers)

    # change label to 'day' from whatever label the user gave their date column
    # in order to merge nicely with whoop DF
    potential_labels = ['Day', 'date', 'Date']

    sheet_df.columns = ['day' if col in potential_labels else col for col in sheet_df.columns]

    if 'day' in sheet_df.columns:
      # standardize date formatting
      sheet_df['day'] = sheet_df['day'].apply(lambda r: parser.parse(r).strftime("%Y-%m-%d"))

    # print(sheet_df)
    # print(sheet_df.dtypes)

    for col in list(sheet_df):
      if col == 'day':
        continue
      
      # convert integers and booleans contained in strings
      sheet_df[col] = sheet_df[col].map(self.convert_items)

      # replace empty/NaN values with the column average
      sheet_df.update(sheet_df[col].fillna(value=sheet_df[col].mean(), inplace=True))

      # insert previous day's activities
      new_col_name = col + ' (prev day)'
      sheet_df[new_col_name] = sheet_df[col].copy().shift(1)

    return sheet_df

  def convert_items(self, item):
    if item is None or item == '': return np.NaN

    if self.is_number(item):
      return float(item)
    elif item == 'TRUE' or item == 'true' or item == 'yes':
      return 1
    else:
      return 0

  def is_number(self, s):
    try:
        float(s)
        return True
    except ValueError:
        return False