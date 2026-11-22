FUNERARIA LA PAZ - PROYECTO ACADEMICO

1. Instala Python 3.
2. Abre CMD o PowerShell dentro de esta carpeta.
3. Ejecuta:
   python -m pip install -r requirements.txt
4. Luego ejecuta:
   python app.py
5. Abre en el navegador:
   http://127.0.0.1:5000

USUARIOS FICTICIOS DE PRUEBA
Administrador
Usuario: admin
Contrasena: Admin123!

Empleado
Usuario: empleado
Contrasena: Empleado123!

PRUEBAS SUGERIDAS
- Entra a Contacto y envia una solicitud ficticia.
- Inicia sesion como empleado: puede ver solicitudes, pero no administrar servicios.
- Inicia sesion como admin: puede ver solicitudes y crear/editar/eliminar servicios.
- Prueba /admin/servicios con el empleado para observar el control de autorizacion.

NOTA DE SEGURIDAD
Esta es una demostracion local academica. En produccion se debe usar HTTPS, una SECRET_KEY segura desde variables de entorno, cookies Secure y proteccion CSRF completa.
