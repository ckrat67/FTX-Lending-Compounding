# Made by TYX 080521; Lending compounder automated
import time
import hmac
import requests
import math  # to truncate lendable amount
from threading import Timer
import datetime as dt
import os


class RepeatedTimer(object):
	def __init__(self, interval, function, *args, **kwargs):
		self._timer     = None
		self.interval   = interval
		self.function   = function
		self.args       = args
		self.kwargs     = kwargs
		self.is_running = False
		self.start()

	def _run(self):
		self.is_running = False
		self.start()
		self.function(*self.args, **self.kwargs)

	def start(self):
		if not self.is_running:
			self._timer = Timer(self.interval, self._run)
			self._timer.start()
			self.is_running = True

	def stop(self):
		self._timer.cancel()
		self.is_running = False


def selector(coin_name: str, api_output):
	selected = 0
	for i in api_output.json()['result']:
		if i['coin'] == coin_name:
			selected = i
			break 
	if not selected:
		print('No such coin.')
	return selected


def authenticator(api_call: str, method: str, ftxkey: str, apisecret: str):
	ts = int(time.time() * 1000)

	requesting = requests.Request(method, string)
	prepared = requesting.prepare()

	signature_payload = f'{ts}{prepared.method}{prepared.path_url}'
	signature_payload = signature_payload.encode()
	signature = hmac.new(apisecret.encode(), signature_payload, 'sha256').hexdigest()

	prepared.headers['FTX-KEY'] = ftxkey
	prepared.headers['FTX-SIGN'] = signature
	prepared.headers['FTX-TS'] = str(ts)
	s = requests.Session()
	res = s.send(prepared)
	return res


def authenticator_post_lend(api_call: str, method: str, coin_name: str, size: float, ftxkey: str, apisecret: str):
	ts = int(time.time() * 1000)
	body = {
		"coin": coin_name,
		"size": size,
		"rate": 1e-6
	}
	requesting = requests.Request(method, api_call, json=body)
	prepared = requesting.prepare()

	signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
	print(prepared.body)
	if prepared.body:
		signature_payload += prepared.body
	signature_payload = signature_payload
	# print(signature_payload)
	signature = hmac.new(apisecret.encode(), signature_payload, 'sha256').hexdigest()

	prepared.headers['FTX-KEY'] = ftxkey
	prepared.headers['FTX-SIGN'] = signature
	prepared.headers['FTX-TS'] = str(ts)
	s = requests.Session()
	res = s.send(prepared)
	return res


def truncate(number, digits) -> float:
	stepper = 10.0 ** digits
	return math.trunc(stepper * number) / stepper


def change_lending(string, string_lending, ftxkey, apisecret):
	res = authenticator(string, 'GET', ftxkey, apisecret)
	print(f'Status code: {res.status_code}')  # status code
	if res.status_code != 200:
		print(f'Something has gone wrong. {res.text}')
		# os.system('pause')

	selected = selector('USD', res)
	print(selected)
	lendable = selected['lendable']
	# print(lendable)  # debugging
	# print(type(lendable))  # float

	new_lending = truncate(lendable, 6)
	results =  authenticator_post_lend(string_lending, 'POST', 'USD', new_lending, ftxkey, apisecret)
	print(results)
	print(results.text)
	if not results.json()['success']:
		print('An error occurred. Please check.')
	elif results.json()['success']:
		print('Success! Compounded interest.')
		print("Interest last compounded at time: ", dt.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
		print('\n')



if __name__ == '__main__':
	print('Created by TYXu')
	print('This function deals with lending for USD on FTX. Look into script for changes.')
	APIinfofilename = 'API_keys.txt'
	APIinfo = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', APIinfofilename), 'r').readlines()

	for n in APIinfo:
		keys = n.rstrip().split(':')
		if keys[0] == 'FTX_KEY':
			FTX_KEY = keys[1]
		elif keys[0] == 'API_SECRET':
			API_SECRET = keys[1]

	string ='https://ftx.com/api/spot_margin/lending_info'  # get lending history
	string_lending = 'https://ftx.com/api/spot_margin/offers'  # for POSTing

	try:
		change_lending(string, string_lending, FTX_KEY, API_SECRET)
		r_t_lending = RepeatedTimer(3600, change_lending, string, string_lending, FTX_KEY, API_SECRET)
		# r_t_lending = RepeatedTimer(1, print, "world")  # testing
	except Exception as ex:
		print(ex)

