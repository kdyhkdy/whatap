import time,datetime
import re
import subprocess
import pandas as pd
import numpy as np


class ResponseMonitoringMiddleware:
    METHOD = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
    def __init__(self,get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)

        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)

        response.data.iloc[-1,7]= round((time.time() - start_time)*1000, 4)
        response.data.to_csv(response.file_name, index=False)

        return response


    def process_response(self, request, response):
        inner_start_time = time.time()
        request_info ={}
        cpu_info = subprocess.getoutput("top | head ")
        kor_datetime = datetime.datetime.now()+datetime.timedelta(hours=9)
        file_id = str(kor_datetime.year) \
                  + str(kor_datetime.month).zfill(2) \
                  + str(kor_datetime.day).zfill(2) \
                  + str(kor_datetime.hour).zfill(2)
        file_name = "~/request_log({0}).csv".format(file_id)
        cpu_usage = round(sum([float(x) for x in re.findall(
            r'(\d+\.\d*)'
            ,cpu_info[cpu_info.find('CPU') : cpu_info.find('SharedLibs')]
        )[:2]]),2)
        mem_usage = subprocess.getoutput("ps -A -o %mem | awk '{ mem += $1} END {print mem}'")

        request_info['TIMESTAMP'] = time.time()
        request_info['DATETIME'] = kor_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        request_info['METHOD'] = request.method
        request_info['PATH'] = request.path_info
        request_info['STATUS_CODE'] = response.status_code
        request_info['CPU_USAGE'] = cpu_usage
        request_info['MEM_USAGE'] = float(mem_usage)
        request_info['LATENCY'] = None

        req_arr = np.array(
            [[
                request_info.get('TIMESTAMP'),
                request_info.get('DATETIME'),
                request_info.get('METHOD'),
                request_info.get('PATH'),
                request_info.get('STATUS_CODE'),
                request_info.get('CPU_USAGE'),
                request_info.get('MEM_USAGE'),
                time.time() - inner_start_time
            ]]
        )

        try:
            csv_data = pd.read_csv(file_name, sep=",")
        except FileNotFoundError as e:
            csv_data = None

        if csv_data is None or csv_data.empty:
            df_request = pd.DataFrame(
                req_arr
                ,columns=[
                    'TIMESTAMP','DATETIME','METHOD'
                    ,'PATH','STATUS_CODE'
                    ,'CPU_USAGE','MEM_USAGE','LATENCY'
                ]
            )
            df_request.to_csv(file_name, index=False)
        else:
            df_request = csv_data.append(request_info,ignore_index=True)

        response.data = df_request
        response.file_name = file_name

        return response