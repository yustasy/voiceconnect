# импортируем flack и запускаем Web сервер
from flask import Flask, abort, request, jsonify, render_template
import os
import time
import requests
import re
from pprint import pprint
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning  		# отключаем предупреждение о не
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)			# достоверных сертификатах


#Задаем константы

CMS_BASE='https://195.218.166.254:19443/api/v1/'                                                        # Задаем основные параметры (например IP)
CMS_HEADERS = {'Content-type': 'application/json', 'authorization': "Basic YWRtaW46QzFzY28xMjM="}    # Задаем логин-пароль (берем из postman)
CospaceID = "1ce8cca1-1747-457a-801a-ea297a41f91b"
# Здесь мы задаем номера абонентов
Party = ['huddle_space_-_cisco_room_kit_mini']
#Party = ['1000', '1001', '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009', '1011', '1014', '1017']
Domain = "@nikpetre-sandbox-9.room.ciscospark.com"  # это доменная часть - будет прибавляться ко всем номерам (В случае если будет вызов по ip - сделать пустым и писать вместо номеров ip-шники)

# Здесь мы задаем слово из имени конференции или иное вхождение (например владелец) по которому будем ее искать
Name = "sergyuts"

def autoconnect(action) :		# Определяем функцию, которую будет удобно вызывать для подключения / отключения всех абонентов списка

    coSpaces = requests.get(CMS_BASE + 'coSpaces' + '?filter=' + Name, verify=False, headers=CMS_HEADERS)

    if coSpaces.status_code == 200:
        pprint("это то, что выдал request.get:" + coSpaces.text)

    SpacesNumber = int(''.join(re.findall(r'<coSpaces total="(\d+)', coSpaces.text)))
    if SpacesNumber == 0:
        print("Конференций не найдено")
        time.sleep(5)
        quit()

    elif SpacesNumber == 1:
        id = ''.join(re.findall(r'<coSpace id="(\w+\-\w+\-\w+\-\w+\-\w+)', coSpaces.text))
        print(id)

    # Узнаем есть ли открытая медиа сессия

    Call = requests.get(CMS_BASE + 'calls' + '?coSpaceFilter=' + id, verify=False, headers=CMS_HEADERS)

    if int(''.join(re.findall(r'<calls total="(\d+)', Call.text))) == 0:  # Медиа сессии нет - и ее нужно открыть
        pprint("Нет активной сессии - создаем объект Call")
        response = requests.post(CMS_BASE + 'calls', data={'coSpace': id, 'name': 'autodial', 'allowAllMuteSelf': 'true','allowAllPresentationContribution': 'true', 'joinAudioMuteOverride': 'true'}, verify=False, headers=CMS_HEADERS)
        time.sleep(1)
        Call = requests.get(CMS_BASE + 'calls' + '?coSpaceFilter=' + id, verify=False, headers=CMS_HEADERS)
        CallID = ''.join(re.findall(r'<call id="(\w+\-\w+\-\w+\-\w+\-\w+)', Call.text))
    else:
        pprint("Медиа сессия уже существует")
        CallID = ''.join(re.findall(r'<call id="(\w+\-\w+\-\w+\-\w+\-\w+)', Call.text))

    pprint("Это ID медиасессии с которой мы работаем: " + CallID)

    pprint(action)
    if str(action) == "1":     # подключаем абонентов из списка
        for element in Party :
            pprint ("подключаем абонента")
            pprint (element)   #   отслеживаем работу скрипта
            connect = requests.get(CMS_BASE + 'calllegs?filter=' + element, verify=False, headers=CMS_HEADERS)	# проверяем не подключен ли он уже к серверу?
            if ''.join(re.findall(r'callLegs total="(\d)', connect.text)) == '0' :
                requests.post(CMS_BASE + 'calls/' + CallID + '/calllegs', data="remoteParty=" + element + Domain, verify=False, headers=CMS_HEADERS)  # 	операция подключения
                response = "You are conecting to conference"
            else :
                print("Абонент уже подключен - отмена")
                response = "You are already connected, cancel"
    if str(action) == "2":      # отключаем абонентов из списка
        for element in Party:
            pprint("отключаем абонента")
            pprint (element)
            connect = requests.get(CMS_BASE + 'calllegs?filter=' + element, verify=False, headers=CMS_HEADERS)
            if ''.join(re.findall(r'callLegs total="(\d)', connect.text)) != '0':
                calllegidcurrent = ''.join(re.findall(r'callLeg id="(\w+\-\w+\-\w+\-\w+\-\w+)', connect.text))
                pprint(calllegidcurrent)
                requests.delete(CMS_BASE + 'calllegs/' + calllegidcurrent, verify=False, headers=CMS_HEADERS)
                response = "You are disconecting from conference"
            else :
                print("Абонент не подключен - отмена")
                response = "You are not connected, cansel"
    return response

def getspace(qwery):
    space = requests.get(CMS_BASE + 'cospaces?filter=' + qwery, verify=False, headers=CMS_HEADERS)	# получаем информацию о space
    space.encoding = 'utf-8'  # задаем кодировку
    if space.status_code == 200:
        pprint("это то, что выдал request.get:" + space.text)
        number = ''.join(re.findall(r'coSpaces total="(\d)', space.text))
        if number != '0':
                ID = ''.join(re.findall(r'coSpace id="(\w+\-\w+\-\w+\-\w+\-\w+)', space.text))
                NAME = ''.join(re.findall(r'<name>(.*)</name>', space.text))
                URI = ''.join(re.findall(r'<uri>(.*)</uri>', space.text))
                CallID = ''.join(re.findall(r'<callId>(.*)</callId>', space.text))
                response = "You have " + number + " " + " coSpaces with ID " + ID + " with name " + NAME + " and SIP URI " + URI + " and with Number " + CallID
        else :
                response = "You have no coSpaces configured"

    return response

def getcall():
    calls = requests.get(CMS_BASE + 'calls', verify=False, headers=CMS_HEADERS)	# получаем информацию о space
    calls.encoding = 'utf-8'  # задаем кодировку
    if calls.status_code == 200:
        pprint("это то, что выдал request.get:" + calls.text)
        call = ''.join(re.findall(r'<calls total="(\w+)"', calls.text))
        print(call)
        response = "You have " + str(call) + " conference active"
        return response

server = Flask(__name__)

@server.route('/get_conference_detail', methods=['POST'])
def conference():
    data = request.get_json(silent=True)
    pprint(data)
    if 'state' in data['queryResult']['parameters']:
        conferenceaction = data['queryResult']['parameters']['state']
        print("Это требуемый параметр:")
        print(conferenceaction)
        if conferenceaction == 'my':
            print("it is my!")
            response = getspace('sergyuts')
        elif conferenceaction == 'active':
            print("it is active!")
            response = getcall()
    if 'action' in data['queryResult']['parameters']:
        conferenceaction = data['queryResult']['parameters']['action']
        if conferenceaction == 'connect':
            print("it is connect!")
            response = autoconnect(1)
        elif conferenceaction == 'disconnect':
            print("it is disconnect!")
            response = autoconnect(2)
        reply = {
        "fulfillmentText": response
        }
        return jsonify(reply)

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000, debug=True)
