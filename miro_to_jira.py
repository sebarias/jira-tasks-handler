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

test_data = ''
class Miro():

    url : str
    bearer : str
    board_id : str
    issues : []
    

    def __init__(self,boardid = None):
        data = load_data()
        self.url = data['url_miro']
        self.bearer = data['bearer_miro']
        if boardid == None:
            self.board_id = data['board_miro_id']
        else:
            self.board_id = boardid
        self.def_size_indicator = data['def_size_indicator']
        self.colors_task_type = data['colors_task_type']
        self.def_size = data['def_size']
        
    def request_to_miro(self,uri):
        url = "{}{}".format(self.url, uri)
        headers = {'authorization': self.bearer}
        response = requests.request("GET", url, headers=headers)
        results = json.loads(response.text)
        return results 

    def get_story_data(self, data):
        arr = data.split(':')
        if len(arr) > 1:
            title = arr[1]
            task_type = arr[0]
            arr2 = title.split('#')
            if len(arr2) > 1:
                title = arr2[0]
                size = arr2[1]
                return task_type, title, size
            else:
                return task_type, title, None
        else:
            return None, None, None   

    def get_data_from_miro(self,story=True):
        """
        Obtener data de Miro
        
        Input
        ----------
        boardId = Id del board de Miro
        
        Output
        ----------
        Array con la información de Miro en formato para Jira
        """
        
        resource = "boards/{}/widgets/".format(self.board_id)
        response = self.request_to_miro(resource)
        miro_data = response["data"]  
        #print(len(miro_data))
        strs = []
        task = []
        stories = []
        child = ''
        for d in miro_data:
            #print(d)
            if d['type'] == 'frame':
                print(d)
                s_type, s_title, s_size = self.get_story_data(d['title'])
                if not s_size:
                    s_size = 3
                if s_type:
                    story = {'name':s_title,'tasks':d['children'], 'size':s_size, 'type':s_type}
                
                stories.append(story)
            if d['type'] == 'sticker':
                #print(d['text'], d['style']['backgroundColor'])
                postit = cleanhtml(d['text'])
                postit = postit.replace('\xa0','')
                postit = postit.split(self.def_size_indicator)
                name = postit[0]
                id_ = d['id']
                size = '3'
                #print(d['style']['backgroundColor'],d['text'] )
                type_ = self.colors_task_type[d['style']['backgroundColor']]
                if len(postit) > 1:
                    size = postit[1].replace(":","").replace(" ","").upper()
                else:
                    size = self.def_size
                task.append({'name':name, 'size':size, 'id':id_, 'label':type_ , 'type':'task'})
                #child = d['children']
        for story in stories:
            sub_tasks = []
            print('story: ', story)
            if 'tasks' in story:
                tasks = story['tasks']
                for child in tasks:
                    sub_task = next((item for item in task if item["id"] == child), None)
                    sub_tasks.append(sub_task)
                story['tasks'] = sub_tasks
            else:
                story['tasks'] = []
        print('cantidad tareas: ',len(task))              
        print(task)
        print('cantidad de historias: ', len(stories))
        print(stories)
        if story:
            return stories
        else:
            return task

        def to_jira(self, data):
            return None

class Jira():
    url_api_2 : str
    token : str
    project_id : int
    colors_task_type : dict
    key : str
    

    def __init__(self, projectid = None, key = None):
        data = load_data()
        self.url_api_2 = data['url_jira_api_2']
        encode_str = "{}:{}".format(data['user_jira'], data['pass_jira'])
        encode_str = encode_auth(encode_str)
        self.token = "Basic {}".format(encode_str)
        self.def_size_indicator = data['def_size_indicator']
        self.colors_task_type = data['colors_task_type']
        if not projectid:
            self.project_id = data['project_id']
        else:
            self.project_id = projectid
        if key:
            self.key = key

    def convert_to_story(self, task):
        issuetype = {'HU':'10001', 'TK':'3', 'SP':'10402'}
        #issuetype = {"id":"3"}
        sp = task['size']
        print('sp:', sp)
        summary = task["name"].strip()
        project = {"id":self.project_id}
        fields = {}
        fields['project'] = project
        fields['summary'] = summary
        type_ = issuetype[task['type']]
        fields['issuetype'] = {'id':type_}
        #size
        fields['customfield_10002'] = int(sp)
        return {"fields": fields}

    def prepare_data(self, data):
        """
        Convertir a formato Jira

        Input
        ----------
        data = data
        
        Output
        ----------
        Array con la información de Miro en formato para Jira
        """
        issues = []
        issuetype = {"id":"3"}
        for task in data:
            issues.append(self.convert_to_jira(task))
        print(issues)
        return issues
    
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
    

    def request_to_jira(self, uri, payload, isJson = True):
        url = "{}{}".format(self.url_api_2, uri)
        headers = {'Content-Type':'application/json', 'Authorization': self.token}
        querystring = {"":""}
        if isJson == False:
            payload = json.dumps(payload, indent = 4)  
            print(payload)
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        
        results = json.loads(response.text)
        return results


    def crea_hu_en_jira(self, issues):
        uri = "issue/bulk"
        payload = json.dumps({"issueUpdates":issues})
        print(payload)
        rs = self.request_to_jira(uri, payload)
        return rs
        
    
    def create_issue(self, issue):
        uri = "issue"
        payload = json.dumps(issue)
        print(payload)
        rs = self.request_to_jira(uri, payload)
        return rs
        

    def upload_jira_data(self,stories):
        for story in stories:
            hu = self.convert_to_story(story)
            #create story
            rs = self.create_issue(hu)
            #rs = test_data['create_story_rs']
            print('rs: ', rs)
            key = self.get_key_from_jira_issue(rs)
            subtasks = self.get_subtask_jira_format(story['tasks'],key)
            print(subtasks)
            print('upload de tareas a parent key:', key)
            print('presione enter para seguir')
            input()
            rs = self.crea_hu_en_jira(subtasks)
            print('rs: ', rs)
            print('presione enter para continuar')
            input()
    
    def get_key_from_jira_issue(self, issue):
        key = ''
        if 'key' in issue:
            return issue['key']
        return None

    def get_subtask_jira_format(self,tasks, parent_jira_id):
        issues = []
        subttask_type = "5"
        for t in tasks:
            if t is None:
                continue
            labels = []
            summary = t["name"]
            issuetype = {"id":subttask_type}
            labels.append(t["label"])
            estimate = t["size"].lower() + 'h'
            time_tracking = {"originalEstimate":estimate, "remainingEstimate": estimate}
            project = {"id":self.project_id}
            parent = {"id": parent_jira_id}
            fields = {"project":project, 
                    "parent":parent, 
                    "summary": summary, 
                    "issuetype": issuetype, 
                    "labels": labels}
            issues.append({"fields": fields})
        return issues
    
    
def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = html.unescape(cleantext)
    return cleantext

def load_data(file_name=''):
    if not file_name:
        file_name = 'config'
    file_name = file_name + '.json'
    with open(file_name, 'r') as j:
        data = json.load(j)
        return data

def encode_auth(str):
    sample_string = "{}".format(str)
    sample_string_bytes = sample_string.encode("ascii")
    
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string

def create_dic_issuestypes(x):
    dic = {}
    dic['name'] = x['name']
    dic['id'] = x['id']
    dic['size']: x['size']
    dic['label'] = x['label']
    dic['type'] = x['type']
    return dic

def create_df_issuetypes(data):
    """
    crea un dataframe con los tipos de issues que existen en Jira
    """
    #data = request_to_jira_get('issuetype')
    issue_types = list(map(create_dic_issuestypes, data))
    df = pd.DataFrame(issue_types) 
    return df

def get_issue_jira_format(tasks, project_jira):
    """
    Convertir a formato Jira

    Input
    ----------
    boardId = Id del board de Miro
    
    Output
    ----------
    Array con la información de Miro en formato para Jira
    """
    issues = []
    issuetype = {"id":"3"}
    for task in tasks:
        sp = task['size']
        print('sp:', sp)
        summary = task["name"].strip()
        project = {"id":project_jira}
        fields = {}
        fields['project'] = project
        fields['summary'] = summary
        fields['issuetype'] = issuetype
        fields['customfield_10002'] = int(sp)
        issues.append({"fields": fields})
        
    print(issues)
    return issues

def create_dic_issuestypes(x):
    dic = {}
    dic['name'] = x['name']
    dic['id'] = x['id']
    dic['description']: x['description']
    dic['url'] = x['self']
    dic['subtask'] = x['subtask']
    return dic

def create_df_issuetypes(data):
    """
    crea un dataframe con los tipos de issues que existen en Jira
    """
    df = pd.DataFrame(data) 
    return df

def mostrar_menu(saldo = 0):
    saldo_global = saldo
    print('¡Bienvenido a miro to happy jira!. Escoja una opción:')
    print('-' * 20)
    print('1) Obtener data Miro')
    print('2) Preparar data para Jira')
    print('3) Mostrar data en Data Frame')
    print('4) Total de Tareas a Insertar')
    print('5) Cargar Data en Jira')
    print('6) Info Issue')
    print('7) Terminar')
    print()

def main():
    #tbbt_proy = 19803
    #board_id = 'o9J_krUi7fI='
    miro = Miro()
    jira = Jira()
    stories = None
    issues = None
    rs = None
    #create_df_issuetypes(data)
    #issues = get_issue_jira_format(data, 19803)
    opt_menu = ""
    while opt_menu != '7':
        mostrar_menu() # Se llama a la función
        opt_menu = input()

        if opt_menu == '1':
            miro.issues = miro.get_data_from_miro()
            print('Data Cargada, size: {}'.format(len(miro.issues)))
        elif opt_menu == '2':
            issues = jira.prepare_data(miro.issues)
            print('Data para Jira Preparada. \n')
        elif opt_menu == '3':
            df = create_df_issuetypes(stories)
            print(df)
            
        elif opt_menu == '4':
            print('Total de tareas a insertar, es: {}\n'.format(len(stories)))

        elif opt_menu == '5':
            if not (issues is None):
                print('ingrese cantidad de elementos a enviar.\n')
                num1 = input()
                if num1:
                    num1 = int(num1)
                    rs = jira.crea_hu_en_jira(issues[:num1])
                    print(rs)
                else:
                    rs = jira.crea_hu_en_jira(issues)
                    print(rs)
                print(num1)
                #rs = jira.crea_hu_en_jira(issues[:num1])
                #print(rs)
            else:
                print('primero hay que cargar datos de Miro...')
        elif opt_menu == '6':
            print('ingrese issue id.\n')
            num1 = str(input())
            jira.get_info_issue(num1)

        elif opt_menu == '7':
            print('Saliendo')
        elif opt_menu == '8':
            jira.upload_jira_data(miro.issues)
        else:
            print('Opción inválida\n')
    print()

if __name__ == "__main__":
    print("Python version")
    print (sys.version)
    print("Version info.")
    print (sys.version_info)
    test_data = load_data('test_data')
    main()