import json
import requests
import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sbn
import numpy as np
import base64
import html

class Jira():
    url_api_2 : str
    token : str
    project_id : int
    user : str
    

    def __init__(self, projectid = None, user = None, passw = None):
        data = load_data()
        self.url_api_2 = "http://jira.bch.bancodechile.cl:8080/rest/api/2/"
        self.project_id = projectid
        self.user = user
        self.set_token(passw)
        
    def set_token(self, passw):
        self.token = self.encode_creds(self.user, passw)

    def encode_creds(self,user, passw):
        encode_str = "{}:{}".format(user, passw)
        return "Basic {}".format(encode_auth(encode_str))
        
    

    def request_to_jira(self, uri, payload = None, method = 'POST', query = {"":""}):
        url = "{}{}".format(self.url_api_2, uri)
        headers = {'Content-Type':'application/json', 'Authorization': self.token}
        results = ""
        response = ""
        if payload:
            payload = json.dumps(payload, indent = 4)  
            
        try:
            response = requests.request(method, url, data=payload, headers=headers, params=query)
            results = ""
            if response.text:
                results = json.loads(response.text)
            
            return results, response.status_code

        except json.decoder.JSONDecodeError as e:
            #print('Error al decode json', e)
            return [], response.status_code

        except requests.exceptions.HTTPError as e:
            print('Error', e)
            return [], response.status_code

        except requests.exceptions.RequestException as e:
            
            print('Error: ', e)
            return [], response.status_code
        

    def validate_user(self):
        uri = "user"
        query = {"username":self.user}
        data, status = self.request_to_jira(uri, method = 'GET', query = query)
        return status

    def prepare_body_search(self, issueid, expand = ["changelog"]):
        jql = 'key = {}'.format(issueid)
        fields = ["id","key","resolution","assignee","issuetype",
        "status","progress", "project", "resolutiondate", "summary", 
        "created", "updated", "customfield_10005","customfield_10002", 
        "aggregateprogress", "self", "labels"]
        body = {}
        body['jql'] = jql
        body['fields'] = fields
        body['expand'] = expand
        return body

class IssueStatus():
    id = None
    key = None
    name = None

    def __init__(self,statusid,statuskey,statusname):
        self.id = statusid
        self.key = statuskey
        self.name = statusname

    def __str__(self):
        return "(status id:{}, status key:{}, status name:{})".format(self.id,self.key,self.name)
        

class IssueJira(Jira):

    issue_id = None
    status_all = []
    summary = None
    project = None
    labels = None
    story_points = None
    assignee = None
    status_name = None
    status_id = None
    sprints = []
    transitions = []

    def __init__(self, projectid=None, issueid=None, jira = None):
        super().__init__(projectid=projectid)
        self.issue_id = issueid
        self.token = jira.token
        self.set_data()
        self.set_transitions()
        
    
    def add_comment_to_issue(self, comment):
        uri = "issue/{}/comment".format(self.issue_id)
        payload = {"body":comment}
        return self.request_to_jira(uri, payload, 'POST')
        

    def transition_issue(self, to_id):
        uri = "issue/{}/transitions".format(self.issue_id)
        transition = {"id":to_id}
        payload = {"transition":transition}
        query = {"expand":"transitions.fields"}
        return self.request_to_jira(uri, payload, 'POST', query)
        

    def set_transitions(self):
        uri = "issue/{}/transitions".format(self.issue_id)
        query = {"expand":"transitions.fields"}
        data = self.request_to_jira(uri, method='GET', query = query)
        self.transitions = []
        if "transitions" in data[0]:
            for transition in data[0]['transitions']:
                issueid = transition["id"]
                issuename = transition["name"]
                issuekey = transition["to"]["id"]
                issue = IssueStatus(issueid,issuekey,issuename)
                self.transitions.append(issue)

    def get_other_status(self):
        return list(filter(lambda x: x.key != self.status_id, self.transitions))

    def validate_new_transition(self, trans_op):
        o_trans = list(map(lambda x: x.id,self.get_other_status()))
        return str(trans_op) in o_trans
    
    def change_transition(self, new_trans):
        print('changing transition')
        uri = "issue/{}/transitions".format(self.issue_id)
        query = {"expand":"transitions.fields"}
        transition = {"id":new_trans}
        payload = {"transition":transition}
        data,status = self.request_to_jira(uri, payload=payload,method='POST', query = query)
        if status == 204:
            return True
        else:
            return False

    def set_data(self):
        body = self.prepare_body_search(self.issue_id)
        data, status = self.request_to_jira('search',body)
        if status == 200:
            if 'issues' in data:
                issue = data['issues'][0]['fields']
                if 'assignee' in issue:
                    self.assignee = issue['assignee']
                if 'summary' in issue:
                    self.summary = issue['summary']
                if 'status' in issue:
                    self.status_name = issue['status']['name']
                    self.status_id = issue['status']['id']
                if 'customfield_10002' in issue:
                    self.story_points = issue['customfield_10002']
                if 'customfield_10005' in issue:
                    if issue['customfield_10005'] is not None:
                        self.set_sprints(issue['customfield_10005'])
        else:
            print('error al consultar {}'.format(self.issue_id))

    def set_sprints(self, sprints):
        for sprint in sprints:
            if (sprint.find('id') > 0):
                sprint = sprint[sprint.find('id'):]
                idx_coma = sprint.find(',')
                id = sprint[3 : idx_coma]
                self.sprints.append(id)

    def __str__(self):
        cadena = "issue id:{}, summary:{}, assignee:{}, status name:{}, story points:{}, project id:{}, sprint:{}".format(self.issue_id,\
            self.summary, self.assignee, self.status_name, self.status_id, self.story_points, self.project_id, self.sprints)
        return cadena
    
def load_data():
    with open('creds.json', 'r') as j:
        data = json.load(j)
        return data

def encode_auth(str):
    sample_string = "{}".format(str)
    sample_string_bytes = sample_string.encode("ascii")
    
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string


def ingresar_nueva_transicion(jiraTask):
    print('transiciones disponibles:')
    transiciones = jiraTask.get_other_status()
    for trans in transiciones:
        print('id: ', trans.id,' : ' ,trans.name)
    seguir = True
    while seguir:
        print('ingrese key de transicion de destino:')
        trans_op = input()
        if jiraTask.validate_new_transition(trans_op):
            print('validación ok')
            return trans_op
        else:
            print('la transición ingresada no es válidad, desea reintentar s/n')
            op = str(input())
            if op.replace(" ", "").lower() != 's':
                seguir = False
                return False

def menu_cambiar_estado_tarea(jira):
    seguir = True

    while seguir:
        print('ingrese Jira key de tarea: ')
        taskid = input()
        print('obteniendo datos de tarea {}'.format(taskid))
        jiraTask = IssueJira(jira.project_id,taskid,jira)
        
        print(jiraTask)
        transiciones = jiraTask.get_other_status()
        new_trans = ingresar_nueva_transicion(jiraTask)
        if new_trans != False:
            print('vamos a cambiar la transicion')
            if jiraTask.change_transition(new_trans):
                print('Cambio de transicion OK')
            else:
                print('se detecto error en transicion.')
        
        print('desea seguir con otra tarea? s/n:')
        seguir = True if str(input()).lower() == 's' else False 


def validar_user_jira(user, passw):
    jira = Jira()
    jira.user = user
    jira.set_token(passw)
    print('validando usuario {}'.format(jira.user))
    status = jira.validate_user()
    if status != 200:
        print('Credenciales Invalidas: ', status)
        return False, jira
    else:
        print('Usuario OK!')
        return True, jira

def autologin():
    creds = load_data()
    if creds['user_jira']:
        if creds['pass_jira']:
            return str(creds['user_jira']), str(creds['pass_jira'])
    return None, None
            
            

def input_login():
    user, passw = autologin()
    if user and passw:
        return user, passw
    else:
        print('Credenciales en archivo de configuración no encontradas.')
        print('ingrese datos de cuenta de Jira <<username:password>>')
        inp = input().split(':')
        if len(inp) > 0:
            user = str(inp[0])
            passw = str(inp[1])
        else:
            return None, None
    return user, passw


def menu_validar_usuario():
    stay = True
    jira = Jira()
    creds = load_data()
    validate = False
    while stay:
        try:
            
            user, passw = input_login()
            if user and passw:
                validate, jira = validar_user_jira(user,passw)
            else:
                raise Exception()
            if validate:
                return True, jira
            else:
                raise Exception()
        except Exception as e:
            print('problemas en validar usuario, quiere reintentar s/n ?')
            q1 = input()
            if str.lower(q1) != 's':
                stay = False
        

    return False, jira

def main():
    print('¡Bienvenido a miro to jira app!:')  
    print('buscando credenciales en archivo creds.json')
    print()

    validar, jira = menu_validar_usuario()
    
    if validar:
        menu_cambiar_estado_tarea(jira)

    print('Saliendo. press <Enter>')
    input()


if __name__ == "__main__":
    print("Python version")
    print (sys.version)
    print("Version info.")
    print (sys.version_info)
    
    main()