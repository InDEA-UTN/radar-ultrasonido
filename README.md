# Radar de ultrasonido

Radar de barrido: un sensor de ultrasonido **HC-SR04** montado sobre un **micro servo SG90** barre
un sector de 180°, mide la distancia a los obstáculos en cada ángulo y una interfaz gráfica dibuja
el resultado en una pantalla tipo PPI (el clásico barrido circular con la traza que se va
desvaneciendo).

Proyecto del laboratorio **InDEA** (Investigación y Desarrollo en Electrónica Aplicada), UTN
Facultad Regional Mendoza.

- **Responsable:** Gonzalo Luna
- **Director:** Javier Velez
- **Estado:** Fase 0 — evaluando la arquitectura (ver abajo)

## El proyecto tiene dos mitades

1. **Adquisición** — disparar el sensor, medir el tiempo de vuelo del eco, mover el servo un paso y
   repetir, entregando pares *(ángulo, distancia)* a un ritmo parejo.
2. **Interfaz** — recibir esos pares y dibujarlos en tiempo real.

Casi todas las decisiones del proyecto salen de dónde se pone cada mitad.

## Decisión pendiente: la arquitectura

Hay tres formas razonables de repartir esas dos mitades entre el hardware disponible, y **elegir
entre ellas es la primera tarea del proyecto**, no algo que venga resuelto de fábrica:

| | Adquisición | Interfaz |
|---|---|---|
| **A** | Arduino Uno | Programa de escritorio en la PC, por USB serie |
| **B** | Raspberry Pi 3B+ por GPIO | Programa corriendo en la misma Raspberry |
| **C** | Arduino Uno | Servidor web en la Raspberry, se ve desde cualquier navegador de la red |

Las tres están descritas en detalle —con sus ventajas, sus riesgos y el experimento que permite
decidir con datos y no con opinión— en **[`docs/alternativas.md`](docs/alternativas.md)**.

Cuando la decisión esté tomada, se escribe en ese mismo archivo (con el motivo) y se actualiza el
estado de este README. Hasta entonces, el resto de la documentación habla en condicional.

## Organización del repositorio

| Ruta | Contenido |
|------|-----------|
| [`docs/alternativas.md`](docs/alternativas.md) | Las tres arquitecturas, los criterios de decisión y el experimento para elegir. |
| [`docs/plan.md`](docs/plan.md) | Las fases del proyecto y en cuál estamos. |
| [`docs/protocolo.md`](docs/protocolo.md) | Propuesta de formato de los datos entre la adquisición y la interfaz. |
| [`hardware/`](hardware/) | Componentes, lista de compras, conexionado y soporte mecánico. |
| [`firmware/`](firmware/) | Código de la parte que mide (Arduino o Raspberry, según la arquitectura). |
| [`host/`](host/) | Código de la interfaz gráfica. |

## Cómo se trabaja acá

`main` está protegido: los cambios entran por **pull request**. El flujo de trabajo habitual es
crear una rama, subirla, abrir el pull request y pedir revisión a Javier.

```bash
git switch -c descripcion-corta-del-cambio
# ... trabajar, git add, git commit ...
git push -u origin descripcion-corta-del-cambio
gh pr create      # o abrirlo desde la web de GitHub
```

La documentación del proyecto se escribe **en español**, expandiendo las siglas la primera vez que
aparecen.

## Licencia

[MIT](LICENSE). El material es de uso libre citando al laboratorio.
