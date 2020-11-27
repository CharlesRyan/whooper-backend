import json
import pandas as pd
import numpy as np


class sheet_module:

  def __init__(self):
    self.raw_data = None

  def parse_data(self, raw_data):
    parsed_data = [json.loads(x) for x in raw_data]
    print('parsed_data', parsed_data)

    '''
    # date parsing, only needed for whoop integration
    for idx, entry in enumerate(parsed_data):
      # first item in values is list of column headers
      if idx > 0:
        # transform gsheet date to whoop format (2020-06-04) so the datasets can be joined based on date
        # first item in entry is the date
        date_parts = entry[0].split('/')
        # add 0 to single digit numbers
        day = f'0{date_parts[1]}' if len(date_parts[1]) == 1 else date_parts[1]
        month = f'0{date_parts[0]}' if len(date_parts[0]) == 1 else date_parts[0]

        year = '2020' if '2021' not in entry else '2021'
        entry[0] = f'{year}-{month}-{day}'
    '''

    # create gsheet DF
    gsheet_data_headers = parsed_data[0:1][0]
    gsheet_data_rows = parsed_data[1:]

    gsheet_df = pd.DataFrame(gsheet_data_rows, columns=gsheet_data_headers)

    # print(gsheet_df)
    # print(gsheet_df.dtypes)

    for col in list(gsheet_df):
      if col == 'day':
        continue
      
      # convert integers and booleans contained in strings
      gsheet_df[col] = gsheet_df[col].map(self.convert_items)

      # replace empty values with the column average
      gsheet_df.update(gsheet_df[col].fillna(value=gsheet_df[col].mean(), inplace=True))

      # insert previous day's activities
      new_col_name = col + ' (prev day)'
      gsheet_df[new_col_name] = gsheet_df[col].copy().shift(1)

    return gsheet_df

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