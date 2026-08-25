# host/

Código de la **interfaz gráfica**: recibe los pares *(ángulo, distancia)* y dibuja la pantalla PPI
—el barrido circular con las trazas que se desvanecen—.

Todavía vacío: qué va acá depende de la [decisión de arquitectura](../docs/alternativas.md).

- **Opción A** → programa de escritorio en Python: `pyserial` para leer el puerto, y PyQt, `pygame`
  o `matplotlib` para dibujar.
- **Opción B** → el mismo programa, pero corriendo en la Raspberry y leyendo directamente de la
  capa de adquisición, sin puerto serie de por medio.
- **Opción C** → servidor (FastAPI o Flask) que lee el puerto serie y empuja los datos por WebSocket
  a una página que dibuja sobre un `canvas`.

Sea cual sea, conviene que la interfaz pueda alimentarse de un **archivo de barridos grabados**
además del hardware en vivo: permite trabajar en el dibujo sin tener el radar armado, y hace que
los errores sean reproducibles.

Si se usa Python, el entorno virtual **no va adentro del repositorio**: se crea aparte y se anota
en el registro de entornos del laboratorio.
