# ensures zipped dependencies landed safely in AWS
try:
  import unzip_requirements
except ImportError:
  pass

import json
import pandas as pd

from modules.whoop_module import whoop_module
from modules.sheet_module import sheet_module

class Main:

  def __init__(self, event):
    ########## dev
    # self.CRED_PATH = 'backend/creds.ini'
    # self.whoop_df = self.__get_whoop_data()
    # self.sheet_df = self.get_sheet_data()
    ########## dev


    # only for passing in data directly, local use
    # self.sheet_data = event
    # self.__parse_sheet_data()
    #######

    ## api use
    parsedEvent = json.loads(event)
    if parsedEvent['requestContext']['http']['method'] != 'POST' or parsedEvent['body'] is None or len(parsedEvent['body']) == 0:
      raise ValueError
    else:
      self.sheet_data = json.loads(parsedEvent['body'])
      self.__parse_sheet_data()


  def __get_whoop_data(self):
    whoop = whoop_module()
    refetch = False
    # refetch = True
    if refetch: whoop.authorize(self.CRED_PATH)

    return whoop.get_summary_data(refetch)
    # return whoop.get_all_data(refetch)


  def __parse_sheet_data(self):

    ############# dev
    # with open('backend/sample_data/gsheet.json') as f:
    #   self.raw_data = json.load(f)
    ############# dev

    sheet = sheet_module()
    self.sheet_df = sheet.parse_data(self.sheet_data)


  def analyze(self):
    # 
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    # pd.set_option("display.max_rows", None)
    # 

    if hasattr(self, 'whoop_df') and self.whoop_df is not None:
      # mish sheet data and whoop_data together based on matching the day column
      all_data = pd.merge(self.whoop_df, self.sheet_df, on='day')
    else:
      all_data = self.sheet_df

    # all_data.to_csv('backend/output/merged_data.csv', index=False)
    # print('Output sent to csv')

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


############# dev
  def sheet_output(self):
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    print('----------------------')
    print(self.sheet_df)
    # print(self.sheet_df.corr())
    # print(self.sheet_df.dtypes)
############# dev

############# dev
# whoop = False
whoop = True
sheet = True

# passing data in directly
# with open('backend/sample_data/gsheet.json') as f:
#   raw_data = json.load(f)

# main = Main(raw_data)
# if whoop and sheet: main.analyze()
# if sheet and not whoop: main.sheet_output()
############# dev

def lambda_handler(event, context):
  try:
    main = Main(event)
  except:
    return {
          'statusCode': 422,
          'body': json.dumps('Invalid request')
      }

  analysis = main.analyze()

  return {
        'statusCode': 200,
        'body': json.dumps(analysis)
    }

############# dev
# api mimicing
# with open("backend/sample_data/test_event.json", 'r') as content:
#   test_event = content.read()

# rtnVal = lambda_handler(test_event, None)
# print(rtnVal)
############# dev