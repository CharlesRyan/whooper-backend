import requests
import pandas as pd
import numpy as np
import json
from datetime import timedelta, datetime
from dateutil import relativedelta, parser, rrule
from dateutil.rrule import WEEKLY

class whoop_module:

    def __init__(self, auth_code = None, whoop_id = None, start_datetime = None, current_datetime = datetime.utcnow()):
        self.auth_code = 'bearer ' + auth_code
        self.whoop_id = whoop_id
        self.start_datetime = start_datetime
        self.all_data = None
        self.current_datetime=current_datetime

    def make_request(self, url, df = False):
        auth_code = self.auth_code
        headers = { 'authorization': auth_code}
        response = requests.get(url, headers = headers)
        if response.status_code == 200 and len(response.content) > 1:
            if df:
                res = self.flatten_nested_items(response.json())
                d = pd.json_normalize(res)
                return d
            else:
                return response.json()
        else:
            print(response)
            return f"error requesting {url}"

    def authorize(self, user_ini):
        # config = configparser.ConfigParser()
        # config.read(user_ini)
        # username = config['whoop']['username']
        username = 'username'
        # password = config['whoop']['password']
        password = 'password'
        headers = {
                "username": username,
                "password": password,
                "grant_type": "password",
                "issueRefresh": False}
        auth = requests.post("https://api-7.whoop.com/oauth/token", json = headers)

        if auth.status_code == 200:
            content = auth.json()
            user_id = content['user']['id']
            token = content['access_token']
            self.whoop_id = user_id
            self.auth_code = 'bearer ' + token
            self.start_datetime = content['user']['profile']['createdAt']
            print("Authentication successful")

        else:
            print("Authentication failed")

    def get_all_data(self, refetch=True):
        print('getting all whoop data')
        '''
        returns a dataframe of WHOOP metrics for each day 
        In each dataframe, each day is a row and contains strain, recovery, and sleep information
        '''

        if not refetch: 
            self.all_data = pd.read_csv('backend/output/whoop_all_data.csv')

        # presence of start_datetime indicates auth has been run, but auth is only necessary if we're refetching
        if not refetch or self.start_datetime:
            if self.all_data is not None:
                ## All data already pulled
                return self.all_data
            else:
                # refetch data
                start_date = parser.isoparse(self.start_datetime).replace(tzinfo = None)
                end_time = 'T23:59:59.999Z'
                start_time = 'T00:00:00.000Z'
                intervals = rrule.rrule(freq = WEEKLY,interval = 1, until = self.current_datetime, dtstart = start_date)
                date_range = [[d.strftime('%Y-%m-%d') + start_time,
                            (d+relativedelta.relativedelta(weeks = 1)).strftime('%Y-%m-%d') + end_time] for d in intervals]
                all_data = pd.DataFrame()
                for dates in date_range:
                    cycle_url = 'https://api-7.whoop.com/users/{}/cycles?end={}&start={}'.format(self.whoop_id, dates[1], dates[0])
                    data = self.make_request(cycle_url, df = True)
                    all_data = pd.concat([all_data,data])
                all_data.reset_index(drop = True, inplace = True)

                ## fixing the day column so it's not a list
                all_data['days'] = all_data['days'].map(lambda d: d[0])
                all_data.rename(columns = {"days":'day'}, inplace = True)

                ## Putting all time into minutes instead of milliseconds
                sleep_cols = ['sleep.qualityDuration', 'sleep.sleeps.qualityDuration', 'sleep.needBreakdown.baseline', 'sleep.needBreakdown.debt', 'sleep.needBreakdown.naps', 'sleep.needBreakdown.strain', 'sleep.needBreakdown.total', 'sleep.sleeps.inBedDuration', 'sleep.sleeps.latencyDuration', 'sleep.sleeps.lightSleepDuration', 'sleep.sleeps.remSleepDuration', 'sleep.sleeps.wakeDuration', 'sleep.sleeps.slowWaveSleepDuration']
                for sleep_col in sleep_cols:
                    try:
                        all_data[sleep_col] = all_data[sleep_col].astype(float).apply(lambda x: np.nan if np.isnan(x) else x/60000)
                    except:
                        print('issue with', sleep_col)

                ## Making nap variable
                all_data['nap_duration'] = all_data['sleep.naps'].apply(lambda x: x[0]['qualityDuration']/60000 if len(x) == 1 else(
                                                    sum([y['qualityDuration'] for y in x if y['qualityDuration'] is not None])/60000 if len(x)>1 else 0))
                all_data.drop(['sleep.naps'],axis = 1,inplace = True)
                ## dropping duplicates subsetting because of list columns
                all_data.drop_duplicates(subset = ['day','sleep.id'],inplace = True)

                self.all_data = all_data

                ###################### dev only
                # all_data.to_csv('backend/output/whoop_all_data.csv', index=False)
                # print('Whoop all_data sent to csv')
                ###################### dev only

                return all_data
        else:
            print("Authorization data not found")


    def get_summary_data(self, refetch=True):
        '''
            returns only the data points that are useful for calculating activity impact
        '''
        interesting_columns = ['day', 'sleep.qualityDuration', 'sleep.score', 'strain.averageHeartRate', 'strain.score', 'recovery.heartRateVariabilityRmssd', 'recovery.restingHeartRate', 'recovery.score', 'nap_duration']

        all_data = self.get_all_data(refetch)
        summary_data = all_data[interesting_columns].copy()

        return summary_data


    def flatten_nested_items(self, res):
        for day in res:
            sleep_details = day['sleep']['sleeps']
            workout_details = day['strain']['workouts']

            if len(sleep_details) > 0: 
                day['sleep']['sleeps'] = sleep_details[0]

            if len(workout_details) > 0: 
                day['strain']['workouts'] = workout_details[0]

        return res