prod = True
# prod = False

if prod: 
  # ensures zipped dependencies landed safely in AWS
  try:
    import unzip_requirements
  except ImportError:
    pass

import json
import pandas as pd

if prod: 
  from function.modules.whoop_module import whoop_module
  from function.modules.sheet_module import sheet_module

if not prod: 
  from modules.whoop_module import whoop_module
  from modules.sheet_module import sheet_module
  from test_event import test_event

class Main:

  def __init__(self, event):
    self.sheet_data = None
    self.whoop_login = None
    self.whoop_df = None

    if 'sheet' in event and event['sheet'] is not None:
      self.sheet_data = event['sheet']
    elif 'body' in event:
      event_body = json.loads(event['body'])
      if 'sheet' in event_body:
        self.sheet_data = event_body['sheet']


    if 'whoop' in event and event['whoop'] is not None:
      self.whoop_login = event['whoop']
    elif 'body' in event:
      event_body = json.loads(event['body'])
      if 'whoop' in event_body:
        self.whoop_login = event_body['whoop']


    if self.sheet_data is not None:
      print('sheet data:', self.sheet_data)
      self.__parse_sheet_data()

    if self.whoop_login is not None:
      print('event has whoop data')
      self.__get_whoop_data()


  def __get_whoop_data(self):
    print('getting whoop data')
    whoop = whoop_module(self.whoop_login['token'], self.whoop_login['id'], self.whoop_login['createdAt'])
    self.whoop_df = whoop.get_summary_data()
    print('got whoop data')
    # self.whoop_df whoop.get_all_data()


  def __parse_sheet_data(self):
    print('parsing')

    sheet = sheet_module()
    self.sheet_df = sheet.parse_data(self.sheet_data)
    print('sheet df created')


  def analyze(self):
    print('analyzing')
    # 
    # pd.set_option("display.max_rows", None, "display.max_columns", None)
    # pd.set_option("display.max_rows", None)
    # 

    if hasattr(self, 'whoop_df') and self.whoop_df is not None:
      print('merging whoop and sheet DFs')
      # mish sheet data and whoop data together based on matching the day column
      all_data = pd.merge(self.whoop_df, self.sheet_df, on='day')
    else:
      print('just using sheet DF')
      all_data = self.sheet_df

    # alphabetically sort columns
    all_data.sort_index(axis=1, inplace=True)

    correlations = all_data.corr()

    return correlations.to_json()


  # dev
  def sheet_output(self):
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    print('----------------------')
    print(self.sheet_df)
    # print(self.sheet_df.corr())
    # print(self.sheet_df.dtypes)

def lambda_handler(event, context):
  print('raw event: ', event)

  # try:
  main = Main(event)
  # except:
  #   print('main failed, sending 422')
  #   return {
  #         'statusCode': 422,
  #         'body': json.dumps('Invalid request')
  #     }

  correlations = main.analyze()

  return_data = {
    'correlations': correlations
  }

  if main.whoop_df is not None:
    return_data['whoop_raw_data'] = main.whoop_df.to_json()

  return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            "Access-Control-Allow-Credentials" : json.dumps(True)
        },
        'body': json.dumps(return_data)
    }

# local api mimicing
if not prod:
  rtnVal = lambda_handler(test_event, None)
  print(rtnVal)
