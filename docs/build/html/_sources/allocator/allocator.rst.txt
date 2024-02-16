.. Visitor allocator documentation master file, created by
   sphinx-quickstart on Tue Feb  6 14:01:40 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Algoritmo de asignación
=============================================

Descripción General
^^^^^^^^^^^^^^^^^^^^

El módulo ``allocator.py`` implementa un algoritmo de asignación diseñado para distribuir un número máximo de visitas entre 
varios clientes, basándose en el score de prioridad asociado a cada cliente. 

Aplicación de Reglas Predefinidas para Asignación de Visitas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Al inicio del proceso de asignación, el algoritmo aplica una serie de reglas predefinidas que determinan el número de visitas 
a asignar a ciertos clientes basándose en criterios específicos. Estas reglas tienen como objetivo garantizar que los clientes 
más relevantes o aquellos que requieren atención especial reciban un número adecuado de visitas, 
según lo definido por el usuario a través de la interfaz.

Reglas de Asignación Basadas en Importancia y Coberturas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Reglas de Importancia:** Se asigna un número fijo de visitas a los clientes que representan un porcentaje (\(X\%\)) específico del volumen total o revenue, identificando así a los clientes más importantes. Esto asegura que los recursos se concentren en mantener y potenciar las relaciones con los contribuyentes clave al éxito del negocio.

- **Reglas de Coberturas:** Para clientes que no han realizado compras en una cantidad definida de meses, el algoritmo asigna visitas con el fin de reactivar su interacción y compra. Esta regla busca garantizar una cobertura mínima y mantener la base de clientes activa.


Esta fase inicial del proceso de asignación destaca la importancia de priorizar estratégicamente el enfoque de las visitas, 
asegurando que los clientes clave reciban la atención necesaria, al tiempo que se mantiene una base de clientes activa y comprometida.

Nota: Mientras se aplican las reglas se hacen validaciones para evaluar si el número máximo de visitas son suficientes para cubrir 
todos los clientes que cumplen las reglas. Una vez asignada las visitas el algoritmo actualiza la cantidad máxima de visitas y 
continua con la lógica de asignación la cual  incluye los siguientes elementos:

La estrategia de asignación de visitas a clientes se fundamenta en dos principios esenciales, detallados a continuación:

Formación de Grupos y Asignación de Visitas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Se establecen inicialmente cuatro grupos numerados del 1 al 4. 
A cada cliente se le asigna un número de visitas al mes \(v\) que corresponde al número de su grupo, 
definido matemáticamente como:

.. math::

   v_i = g_i

donde \(v_i\) es el número de visitas asignadas al cliente \(i\), y \(g_i\) es el grupo al que ha sido asignado el cliente \(i\).

Determinación de Grupos mediante Percentiles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Los clientes se ordenan según su puntuación de prioridad \(s\) y se dividen inicialmente en grupos utilizando percentiles. 
La asignación en grupos se realiza de la siguiente manera:

.. math::

   g_i = 
   \begin{cases} 
   1 & \text{si } s_i \leq P_{25} \\
   2 & \text{si } P_{25} < s_i \leq P_{50} \\
   3 & \text{si } P_{50} < s_i \leq P_{75} \\
   4 & \text{si } s_i > P_{75}
   \end{cases}

donde \(s_i\) es la puntuación de prioridad del cliente \(i\), y \(P_{25}\), \(P_{50}\), \(P_{75}\) son los percentiles 25, 50 y 75, respectivamente, del conjunto total de puntuaciones.

Nota: La metodología permite ajustar el número de grupos modificando los rangos de percentiles, ofreciendo flexibilidad 
para adaptarse a diferentes estrategias o limitaciones operativas. Por ejemplo, para crear dos grupos, 
se utilizarían los percentiles 50% y 100%, enfocando la división en torno a la mediana de las puntuaciones.
Este enfoque matemático garantiza que la asignación inicial de visitas refleje las prioridades establecidas por las puntuaciones 
de los clientes, permitiendo ajustes en la cantidad de grupos según sea necesario. Sin embargo, estos grupos son consecutivos y 
para definir el numero de visitas de cada grupo se deberá realizar una modificación a la interfaz o ingresar manualmente estas
asignaciones en el código.

Optimización de las Asignaciones de Visitas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Una vez asignadas las visitas por grupos, es probable que el total de visitas asignadas exceda el número máximo de visitas 
disponibles, especificado por el usuario. Para abordar este desafío, el algoritmo entra en una fase de iteración diseñada 
para ajustar dinámicamente las asignaciones iniciales al límite de visitas máximas.

Proceso de Reducción de Visitas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

El objetivo es calcular, de manera aproximada, cuántas visitas se deben redistribuir desde cada grupo para no superar 
el total de visitas máximas permitidas. Este cálculo se basa en la proporción de visitas excedentes en relación al total de visitas 
inicialmente asignadas, aplicando la siguiente fórmula matemática:

.. math::

   v_{\text{mover}, g} = v_{g} \times \left( \frac{v_{\text{excedentes}}}{v_{\text{total, inicial}}} \right)

donde:

- :math:`v_{\text{mover}, g}` es el número de visitas a redistribuir para el grupo \(g\).
- :math:`v_{g}` es el total de visitas asignadas al grupo \(g\).
- :math:`v_{\text{excedentes}}` es el total de visitas que exceden el límite máximo permitido.
- :math:`v_{\text{total, inicial}}` es el total de visitas inicialmente asignadas a todos los grupos.

Redistribución Equilibrada
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Para garantizar una redistribución equilibrada y evitar concentrar la reducción en un solo grupo, el algoritmo recalcula 
en cada iteración cuántos clientes deben ser movidos de un grupo a otro. Específicamente, se mueven clientes del grupo 4 al 3, 
del 3 al 2, y del 2 al 1, teniendo en cuenta el número de visitas a mover por grupo derivado de la fórmula anterior.

Criterio de Selección de Clientes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Priorizando una optimización justa, se seleccionan primero para mover aquellos clientes que están cerca del límite inferior 
de su grupo actual, según el ordenamiento basado en el score de prioridad. Esta estrategia asegura que los ajustes 
se centren en los clientes cuya reasignación al grupo inmediatamente inferior impactará mínimamente en la distribución 
general de las prioridades.

Este enfoque iterativo y matemáticamente fundamentado permite al algoritmo ajustar de manera efectiva y equitativa las asignaciones 
de visitas a la capacidad máxima disponible, respetando al mismo tiempo la estructura de prioridades establecida inicialmente.

Distribución de Visitas en Caso de Excedente
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

En la situación donde el total de visitas disponibles supera la suma de visitas inicialmente asignadas a los clientes, 
el algoritmo implementa una estrategia para distribuir el excedente de manera equitativa entre los grupos 1, 2 y 3. 
Este proceso asegura un uso óptimo de los recursos adicionales, maximizando el alcance y la efectividad de las visitas sin 
sobrepasar el límite máximo de capacidad.

.. math::

    v_{\text{adicional}} = \frac{v_{\text{disponibles}} - v_{\text{total, asignadas}}}{3}

donde:

- :math:`v_{\text{adicional}}` representa el número de visitas adicionales que se distribuirán por grupo.
- :math:`v_{\text{disponibles}}` es el total de visitas disponibles tras considerar las asignaciones iniciales y las reglas aplicadas.
- :math:`v_{\text{total, asignadas}}` es el número total de visitas ya asignadas a todos los grupos.

Procedimiento de Distribución Equitativa
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Las visitas adicionales se reparten de manera que cada uno de los grupos 1, 2 y 3 reciba una cantidad igual de estas visitas extra. 
Se seleccionan los clientes más cercanos al límite superior de cada grupo, basándose en su puntuación de prioridad, 
para recibir las visitas adicionales. Esta metodología no solo promueve una distribución justa de los recursos, 
sino que también refuerza la estrategia de maximizar el impacto de las visitas concentrándose en aquellos clientes con mayor 
potencial según su clasificación de prioridad.
