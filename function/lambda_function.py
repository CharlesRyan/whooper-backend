# prod = True
prod = False

# ensures zipped dependencies landed safely in AWS
if prod: 
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

    if 'body' in event and event['body'] is not None and len(event['body']) != 0:
      self.sheet_data = event['body']
    elif 'multiValueQueryStringParameters' in event and 'data[]' in event['multiValueQueryStringParameters'] is not None and len(event['multiValueQueryStringParameters']['data[]']) != 0:
      print('has params')
      event_params = event['multiValueQueryStringParameters']
      self.sheet_data = event_params['data[]']

      if 'whoop' in event_params:
        self.whoop_login = json.loads(event_params['whoop'][0])
        self.__get_whoop_data()


    print('sheet data:', self.sheet_data)

    if self.sheet_data is None:
      raise ValueError
    else:
      self.__parse_sheet_data()


  def __get_whoop_data(self):
    whoop = whoop_module(self.whoop_login['token'], self.whoop_login['id'], self.whoop_login['createdAt'])
    self.whoop_df = whoop.get_summary_data()
    # self.whoop_df whoop.get_all_data(refetch)


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

    # may need to change hasattr to 'x in y'
    if hasattr(self, 'whoop_df') and self.whoop_df is not None:
      # mish sheet data and whoop_data together based on matching the day column
      all_data = pd.merge(self.whoop_df, self.sheet_df, on='day')
    else:
      all_data = self.sheet_df

    # alphabetically sort columns
    all_data.sort_index(axis=1, inplace=True)

    correlations = all_data.corr()

    # correlations.to_json('backend/output/correlations.json')
    # print('Corr output sent to json')
    # correlations.to_csv('backend/output/correlations.csv')
    # print('Corr output sent to csv')

    # print(self.whoop_df)
    # print(all_data.head())
    # print(all_data)
    # print(all_data.corr())
    # print(all_data.dtypes)

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

  analysis = main.analyze()

  return {
        'statusCode': 200,
        'body': json.dumps(analysis)
    }

# local api mimicing
if not prod:
  rtnVal = lambda_handler(test_event, None)
  print(rtnVal)
