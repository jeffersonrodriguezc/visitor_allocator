.. Visitor allocator documentation master file, created by
   sphinx-quickstart on Tue Feb  6 14:01:40 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Análisis de variables
======================

En general este análisis se concibe como un motor analítico para evaluar y priorizar áreas de intervención dentro de distintas 
zonas geográficas, basándose en datos provenientes de los datos Excel cargados. Este proceso de análisis se realiza de manera individualizada 
para cada zona, aplicando una serie de reglas y cálculos específicos destinados a identificar oportunidades y desafíos dentro de cada zona para la asignación de visitas.
Inicialmente, el análisis prepara los datos limpiando y normalizando las columnas, así como rellenando los valores faltantes para los meses con un valor de 0. 
Posteriormente, se segmenta el conjunto de datos por zona, aplicando análisis específicos que incluyen la evaluación del volumen de ventas, cuota de mercado, ingresos, 
Portafolio, Mix Premium y variables categóricas, indicadores críticos para cada producto seleccionado. 
Estos análisis se complementan con el cálculo de puntuaciones de prioridad para cada cliente en cada variable, 
las cuales se ajustan según parámetros definidos por el usuario, como pesos específicos para cada variable analizada. 
Además, el análisis integra reglas adicionales para la cobertura y gestión de clientes basándose en su actividad reciente, 
y finalmente, consolida y prioriza los resultados para orientar en el proceso de asignación de visitas. 

A continuación se describe el proceso de análisis de todas las variables del aplicativo.

1. Variable Volumen
--------------------

El análisis de esta variable se realiza de la siguiente manera:

1. Análisis temporal de la variable Volumen con respecto al año anterior.  

   .. function:: analysis.utils.analysis_volumen_ratio(data, product, max_year, min_year, max_month)

      Este análisis está diseñado para ayudar a analizar las tendencias de volumen de un producto específico a lo largo del tiempo, 
      comparando los datos entre dos años diferentes. Su objetivo es identificar cambios significativos en el volumen de ventas, 
      como pérdidas o ganancias, y proporcionar una vista detallada de cómo estos cambios varían por cliente y mes. 
      Esto puede ser especialmente útil para la toma de decisiones estratégicas en marketing y ventas.

      Los pasos en el análisis son los siguiente:
      
      1.1. Resta los 6 últimos meses del año actual de cada cliente con respecto a mismos últimos meses del año inmediatamente anterior. Con esta operación se busca encontrar pérdidas o ganancias de los clientes en cada mes.
      
      1.2. Al valor resultante de cada mes se le aplica un ponderado de pesos para darle más relevancia a los valores de los últimos meses. En la versión actual la distribución de estos pesos es:
      
         - Mes 6 (mes más reciente o último mes): Un peso del 50%  
         - Mes 5: Un peso del 25%  
         - Mes 4: Un peso del 10%  
         - Mes 3: Un peso del 5%  
         - Mes 2: Un peso del 5%  
         - Mes 1: Un peso del 5%  

      Estos valores pueden ser cambiados en el código modificando la función:

      .. function:: analysis.utils.weighting_6m(ratio, month, max_month)

         .. code-block:: python

            def weighting_6m(ratio, month, max_month):
               """
               Función para realizar la ponderación de la variable 
               volumen.
               """
               diff = max_month - month
               if diff == 0: # quiere decir el último mes
                  result = ratio*.5
               elif diff == 1: # quiere decir penultimo mes
                  result = ratio*0.25
               elif diff == 2: # quiere decir antepenultimo
                  result = ratio*.10
               else: # opción para el resto de meses
                  result = ratio*.05
               
               return result
      
      1.3. Finalmente la pérdida o ganancia ponderada de cada mes se reescala usando los valores
      máximos y mínimos entre todos los valores de los clientes para ese mes. Importante: En esta operación
      se invirte el resultado para que valores negativos (pérdidas) indiquen altas prioridades (cerca a 1).

      La ecuación de reescalado min-max aplicada de manera independiente para los valores de cada mes es la siguiente:

      .. math::

         x_{\text{norm}, m} = 1 - (\frac{x_{m} - x_{\text{min}, m}}{x_{\text{max}, m} - x_{\text{min}, m}})

      Donde:

      - :math:`x_{\text{norm}, m}` es el valor normalizado para el mes :math:`m`.
      - :math:`x_{m}` es el valor original que se está normalizando para el mes :math:`m`.
      - :math:`x_{\text{min}, m}` es el valor mínimo observado en el conjunto de datos de los clientes para el mes :math:`m`.
      - :math:`x_{\text{max}, m}` es el valor máximo observado en el conjunto de datos de los clientes para el mes :math:`m`.
      - :math:`m` es el mes específico para el cual se realiza la normalización, variando de 1 a 6 en este contexto.


2. Construcción score de prioridad para cada cliente.

   Una vez se tienen las pérdidas o ganancias ponderadas reescaladas se procede a realizar la respectiva suma. El Resultado
   se normaliza contra el valor máximo generando un valor entre 0 y 1. Donde 0 indica que el cliente tiene poca prioridad 
   ya que tuvo ganancia altas y 1 indica alta prioridad por altas pérdidas.

2. Variable Revenue
--------------------

   Debido a que la variable Revenue es de la misma naturaleza que la variable Volumen, se le aplica exactamente el mismo
   análisis descrito en la variable Volumen.

   Todo el análisis puede ser consultado en la función llamada:

   .. function:: analysis.utils.analysis_revenue_ratio(data, product, max_year, min_year, max_month)
      
      Este análisis está diseñado para ayudar a analizar las tendencias del Revenue de un producto específico a lo largo del tiempo, 
      comparando los datos entre dos años diferentes.

      
3. Variable Market Share
-------------------------

El análisis de esta variable se realiza de la siguiente manera:

1. Análisis temporal de la variable Market Share con respecto a los meses anteriores.  

   .. function:: analysis.utils.analysis_market_share_ratio(data, product, max_year, max_month)

      Este análisis temporal esta diseñado para analizar cómo la cuota de mercado de un producto específico ha variado en 
      el transcurso de los últimos cuatro meses del año más reciente disponible en el conjunto de datos. 
      Este análisis se realiza seleccionando los datos pertinentes al producto y al período de tiempo especificados, 
      calculando luego el cambio en la cuota de mercado mes a mes para cada cliente. A través de este proceso, 
      identifica no solo las variaciones en la cuota de mercado, sino también estima el impacto de estas variaciones en términos de volumen
      de ventas perdido, ajustando los cálculos por medio de un factor de ponderación para cada mes. Este análisis proporciona una
      visión detallada y cuantifica la tendencia de compra de los clientes permitiendo entender mejor el rendimiento de los productos
      en el mercado. A continuación se presenta el paso a paso detallado: 

      1.1. Se realiza la diferencia de la cuota o el valor de Market Share con respecto a los meses anteriores del año actual. En este análisis se
      contempló tres operaciones lo que involucra los últimos 4 meses.

      1.2. Las diferencias de la cuota de mercado se multiplican con la variable Volumen del mes anterior para ese mismo producto.
      Esto lo que permite es obtener el valor pérdido en términos de volumen.

      1.3. Las cuotas pérdidas en volumen se ponderan para darle más importancia a los meses más recientes.
         
         - Diferencia mes 4-3 (mes más reciente o último mes): Un peso del 50%  
         - Diferencia mes 3-2: Un peso del 30%
         - Diferencia mes 2-1: Un peso del 20%

      Estos valores pueden ser cambiados en el código modificando la función:

      .. function:: analysis.utils.weighting_3m(ratio, month, max_month)

         .. code-block:: python

            def weighting_3m(ratio, month, max_month):
               """
               Función para realizar la ponderación de la variable 
               Market share, y otras variables que lo requieran.
               Solo los tres ultimos meses.
               """
               diff = max_month - month
               if diff == 0: # quiere decir la último diferencia
                  result = ratio*.5
               elif diff == 1: # quiere decir la penultima diferencia
                  result = ratio*0.30
               elif diff == 2: # quiere decir la antepenultima diferencia
                  result = ratio*.20

               return result

2. Calculo final del score de prioridad:

   Finalmente los pérdidas en volumen ponderadas calculadas en el paso anterior se suman para cada cliente y se aplica el 
   correspondiente reescalado con respecto al valor máximo y mínimo entre todos los clientes. Aquí es importante tener en 
   cuenta que el reescalado se realiza de tal manera que el nuevo mínimo 0 indique poca prioridad (poca pérdida en Market share)
   y un valor de 1 alta priodidad (Mucha pérdida en el market share durante los últimos meses)


4. Variable Portfolio
----------------------

El análisis de la variable 'Portfolio' se desarrolla a través de un enfoque multifacético que evalúa tanto la distribución geográfica 
como la evolución temporal del portafolio del producto. Este proceso comienza con la georreferenciación de los datos de clientes, 
agrupándolos en clusters según la proximidad geográfica y el valor de su portafolio, lo que permite identificar zonas de alta 
concentración de valor. Paralelamente, se realiza una comparación del portafolio entre dos puntos temporales 
(últimos meses de año actual con los mismo meses del año anterior) para detectar cambios significativos a lo largo del tiempo. 
Este análisis temporal se complementa con una evaluación de los cambios en la densidad geográfica del portafolio, 
integrando estos datos para generar un puntaje comprensivo que refleje tanto la importancia actual del portafolio en términos 
de distribución geográfica como su evolución y potencial de crecimiento o declive. Este enfoque holístico permite identificar áreas 
críticas para la optimización de estrategias de ventas, adaptándose a las dinámicas del mercado y enfocando esfuerzos en regiones 
o segmentos de clientes con mayor potencial de impacto en el rendimiento global del portafolio.


.. function:: analysis.utils.analysis_portfolio_ratio(data, product, max_year, min_year, max_month)

   A continuación se presenta el paso a paso detallado:

   1. Análisis Geográfico:
      El análisis geográfico del portafolio de productos comienza con la georreferenciación de los clientes, 
      utilizando sus coordenadas para mapear su ubicación. A partir de esta información, se emplean técnicas de clustering, 
      específicamente el algoritmo K-Means, para agrupar a los clientes en función de su proximidad física y el valor de su portafolio. 
      Este proceso no solo identifica regiones con alta densidad de clientes valiosos sino que también destaca zonas de interés estratégico
      basadas en la concentración de valor del portafolio. A través de un proceso de ajuste de los clusters, se garantiza que cada grupo 
      tenga una cantidad representativa de clientes, y se refina la distribución para destacar áreas de alto valor, eliminando 
      superposiciones y optimizando la asignación de recursos usando  técnicas de análisis espacial para evaluar la distancia y distribución
      entre los clusters. Por lo tanto:

      1.1. Creación de clusters unsado K-means con un mínimo de clientes de 20 usando coordenadas y valor de portafolio.
      Este parametro puede ser modificado en la línea 403 de la función aquí explicada.

      .. code-block:: python

         min_clients_cluster = 20 # número minimo de clientes por cluster

      1.2. De los cluster creados se seleccionan aquellos que cumplen con las siguientes dos condiciones:

         - Que la mediana del valor del portafolio del cluster sea mayor o igual al 80% del valor max de portafolio
         - Que almenos 1/4 (en este caso 5 clientes) del total de clientes en este cluster tengan portfolio arriba de este valor.

         Estos valores pueden ser modificados en las lineas 423 a la 425 de la función que se esta describiendo.

         .. code-block:: python

            high_portfolio = int(max_porf*.8) # porcentaje para considerar portafolios altos
            high_portfolio_clusters = metrics.loc[(metrics.portfolio_count>=min_clients_cluster//4)&
                                          (metrics.portfolio_median>=high_portfolio)].cluster.values   

      1.3. Después de seleccionar los clusters con alto portencial se hace un proceso de filtrado para eliminar cluster que esten
      muy cercanos y se sobrelapen entre si. 

      1.4. Paso seguido es basado en estos clusteres finales, se encuentra el punto referente de cada cluster (cliente mas central)
      y con respecto a ese cliente se trazan circunferencias de radio de 200 metros. Proceso para generar los scores. El valor del radio
      puede ser modificado en la linea 473:

      .. code-block:: python
         
         gdf, circle_coors = compute_score_circles(gdf, gdf_rep, max_portfolio_dict, r_meters=200)   

      1.5. Finalmente se hace un calculo de score de "oportunidad" es decir aquellos clientes que queden dentro de la circunferencias
      se les calcula un valor (entre 0 y 1) que indica si tiene una oportunidad de crecimiento respecto al valor medio de portafolio del cluster.
      Suponga que el cluster tiene un valor de portafolio de 10 y un cliente dentro del círculo tiene un valor de portafolio de 3 entonces
      el score será de 0.7 (un valor alto).

      1.6. Opcional: Es posible calcular score a los clientes que quedan fuera de las circunferencias. Asignandoles el cluster más cercano.
      (Actualmente tienen un score de 0). Puede activar este comportamiento descomentando las lineas 489 y 492:

      .. code-block:: python

         # Generar score a los registros faltantes
         #missing_scores = gdf.loc[gdf.score.isna()].apply(lambda x: generate_score(max_portfolio_dict[int(x.new_cluster)], 
         #                                                                          x.portfolio), axis=1)
         # Actualizar scores
         #gdf.loc[gdf.score.isna(), 'score'] = missing_scores         
      

   2. Análisis Temporal:
      Debido a la naturaleza de esta variable, el análisis temporal se realiza de la misma manera que la variable Volumen y Revenue.

   El score de prioridad final se calcula mediante el promedio del score de georreferenciación y el score de análisis temporal.
   Es decir cada análisis tiene un peso del 50%.

5. Variable Mix Premium
------------------------

   Debido a que la variable Mix Premium es de la misma naturaleza que la variable Portafolio, se le aplica exactamente el mismo
   análisis descrito en la variable Portafolio.

   .. note:: Los cluster altos en mix Premium son los que tienen mas del 75%

   Todo el análisis puede ser consultado en la función llamada:

   .. function:: analysis.utils.analysis_mixpremium_ratio(data, product, max_year, min_year, max_month)
      
      Este análisis está diseñado para ayudar a analizar las tendencias de Mix Premium de un producto específico a lo largo del tiempo, 
      comparando los datos entre dos años diferentes.

      El score de prioridad final se calcula mediante el promedio del score de georreferenciación y el score de análisis temporal.
      Es decir cada análisis tiene un peso del 50%.

   NOTA:
   El análisis de esta variable solo se diferencia en un pequeño detalle del análisis de la variable portafolio.
   Como esta variable esta en un rango de 0-1 a diferencia que la variable portafolio que tiene un rango de número enteros, no hay
   que hacer una normalización de la variable en el proceso de clustering mientras que la variable portafolio si hay que 
   normalizarla a valores entre 0-1 para que este en la misma escala de las demás variables del proceso de clustering. Es decir, 
   en este análisis hay un paso menos en el proceso.

6. Integración de Scores de prioridad
-------------------------------------
   Finalmente todos los scores de cada una de las variables seleccionadas se integran en un promedio ponderado por los pesos 
   asignados desde la interfaz. Asi cada cliente tendrá un único score que incorpora los análisis anteriormente descritos.

.. math::

    \bar{x} = \frac{\sum_{i=1}^{n} w_i x_i}{\sum_{i=1}^{n} w_i}

Donde:

- :math:`\bar{x}` es el promedio ponderado.
- :math:`x_i` representa el score de priodidad para la variable i.
- :math:`w_i` es el peso de cada término, ingresado por el usuario a través de la interfaz.
- :math:`n` es el número total de variables (máximo 3).

7. Variables Categóricas
-------------------------

La inclusión y tratamiento de variables categóricas en el análisis de datos permite ponderar puntajes de prioridad a distintos 
clientes con base en ciertos criterios o características categóricas, como por ejemplo el nivel de digitalización entre otros. 
La lógica implementada permite modificar dinámicamente el peso de las puntuaciones totales según la categoría específica 
a la que pertenece cada cliente. 

7.1. Variable Nivel de Digitalización 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Este análisis incluye la posibilidad de ponderar los scores de los clientes a través de la variable nivel de digitalización.
Para tal caso, se debe seleccionar una sub variable de la variable categorica nivel de digitalización (Alta, Baja o Media) y a esta opción asignarle un
peso. Recuerde que de manera estándar todas las opciones para el nivel de digitalización tienen un peso de 1. Asi que para darle
mayor importancia deberá asignar un peso mayor que 1. La ponderación se hace de la siguiente manera:

- Multiplicar los scores por el peso correspondiente
- Re escalar con respecto a los valores máximos, así los clientes multiplicados con peso mayor a 1 se les asigna más prioridad.


