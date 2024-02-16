.. Visitor allocator documentation master file, created by
   sphinx-quickstart on Tue Feb  6 14:01:40 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Interfaz de usuario
=============================================

Descripción General
-------------------

El módulo ``app_gui.py`` implementa la interfaz gráfica de usuario (GUI) para la aplicación, utilizando ``tkinter`` como framework de GUI. Está diseñado para ofrecer múltiples vistas dentro de una ventana principal, permitiendo al usuario interactuar con diferentes funcionalidades de la aplicación.

Dependencias
------------

Este módulo depende de:

- ``tkinter`` para la creación de la GUI.
- ``pandas`` para el manejo de datos.
- ``os``, ``sys`` para operaciones relacionadas con el sistema operativo.
- Módulos internos para análisis de datos y utilidades.

Clases Principales
------------------

MultiViewApp
^^^^^^^^^^^^

Responsable de construir la ventana principal de la aplicación y gestionar las vistas múltiples.

**Métodos**:

- ``__init__``: Constructor de la clase, inicializa la ventana principal.
- ``initialize_attributes``: Inicializa atributos utilizados a lo largo de la aplicación.
- ``show_view1``, ``show_view2``: Métodos para mostrar diferentes vistas dentro de la GUI.
- ``clear_right_pane``: Limpia el panel derecho cuando se cambia entre vistas.
- ``load_data``: Carga datos para ser utilizados en la aplicación.
- ``execute_procedure``: Ejecuta un procedimiento o análisis de datos.
- ``download_results``: Permite al usuario descargar los resultados del análisis.
- ``restart``: Reinicia la aplicación o ciertas vistas a su estado inicial.
- ``update_variable``, ``update_variable_view2``: Actualiza variables basadas en la interacción del usuario.
- ``on_radio_select``: Gestiona eventos de selección de botones de radio.
- ``print_variables``: Imprime variables de depuración o información relevante.
- ``create_radio_button``: Crea botones de radio para la selección del usuario.

Funciones Principales
---------------------

run_app
^^^^^^^

Función principal para iniciar la GUI de la aplicación.

Uso
---

Para ejecutar la aplicación GUI:

.. code-block:: python

    if __name__ == "__main__":
        run_app()

Ejemplos de Interfaz de Usuario
-------------------------------

La GUI permite al usuario navegar entre diferentes vistas para realizar análisis de datos, cargar y descargar datos, y ajustar configuraciones específicas del análisis.
