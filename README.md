# jira-tasks-handler

Hola! estas usando un programa python para actualizar los estados de tus tareas.

# Pre requisitios

- Python 3.X o superior.
- VPN activada.

# Modo de Uso

### Imicio Programa

Para usar el programa abrir la terminal en la carpeta del repositorio y ejecutar:

`python jira_class.py`

Primero evaluará las credenciales en el archivo de configuración `creds.json`. Si el archivo no contiene las credenciales, solicitará via prompt los datos de usuario JIRA.

### Ingreso de Tarea

Una vez validada la data de conexión, solicitará vía prompt la llave de la tarea JIRA a modificar. por ejemplo:

`JET-513`

si es una tarea válida, mostrará el contenido de la tarea, si no, indicará que no es una tarea válida y consultará si se desea proseguir.

### Cambio de estado de una Tarea

si es una tarea válida, indicará las transiciones posibles de modificación. por ejemplo

`id:  11  :  To Do`
`id:  21  :  In Progress`

y luego consultará por la opción escogida. 

Para cambiar una transición se debe ingresar el id de ésta, por ejemplo, si se desea cambiar a la transición <<In Progress>> se debe ingresar el id: 21, tal como se especifica en la lista del ejemplo.

Si el cambio de transición es exitoso se indicará por medio de un mensaje, por el contrario, si existe algún problema, se indicará el error.

### Files

- creds.json : Archivo json que contiene las credenciales de JIRA, es opcional, y el objetivo es no ingresar los datos en cada ejecución del programa.

    - "user_jira": dato de nombre usuario de Jira, usado normalmente para conectarse a la plataforma.
    - "pass_jira": dato de password de usuario de Jira, usado normalmente para conectarse a la plataforma.

- miro_to_jira.py : Archivo con código de ejecución.

### IMPORTANTE

- Antes de utilizar el programa asegurarse que las credenciales son las correctas.
- Si las credenciales son incorrectas, no permitirá la conexión y la reiterada re-ejecución del programa con credenciales incorrectas podría bloquear el usuario.
- Cuando se cambia una transición, también asigna como dueño de la tarea al usuario conectado, por lo que si modifica una tarea no asignada al usuario, se reasignará.