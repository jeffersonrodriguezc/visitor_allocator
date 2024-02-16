#import utm
#import math
#import random
import numpy as np
import pandas as pd
import geopandas as gpd
#from shapely import Polygon
import matplotlib.pyplot as plt
from shapely.geometry import Point
from itertools import combinations
#from haversine import haversine, Unit
from sklearn.neighbors import BallTree
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
from scipy.spatial.distance import pdist
from sklearn.cluster import DBSCAN, KMeans
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import MinMaxScaler
#from sklearn.metrics.pairwise import haversine_distances


def compute_product_vol_weight(data, product, 
                               max_year, max_month):
    """
    Esta función calcula el porcentaje del volumen
    para un producto, año y mes. Esto se calcula para 
    cada cliente.
    """
    # seleccionar datos por año, mes y producto
    # la idea es traer la información de volumen
    pivot = data.loc[(data['Año']== max_year)&
                      (data['Mes'] == max_month)&
                      (data['Producto'] == product), 
                      ['Codigocliente', 'Volumen', 'Año', 'Mes', 'Producto']]
    
    # calcular el volumen total
    total_volume = pivot.Volumen.sum()

    # Calcular el porcentaje de cada volumen de compra
    pivot[f'vol_{product}_weight'] = pivot.Volumen/total_volume

    # Ordenar los datos por porcentaje del volumen 
    # Primero los mas representativos
    pivot.sort_values(f'vol_{product}_weight', ascending=False, inplace=True)

    return pivot


def compute_product_rev_weight(data, product, 
                               max_year, max_month):
    """
    Esta función calcula el porcentaje del revenue
    para un producto, año y mes. Esto se calcula para 
    cada cliente.
    """
    # seleccionar datos por año, mes y producto
    # la idea es traer la información de volumen
    pivot = data.loc[(data['Año']== max_year)&
                      (data['Mes'] == max_month)&
                      (data['Producto'] == product), 
                      ['Codigocliente', 'Revenue', 'Año', 'Mes', 'Producto']]
    
    # calcular el volumen total
    total_revenue = pivot.Revenue.sum()

    # Calcular el porcentaje de cada volumen de compra
    pivot[f'rev_{product}_weight'] = pivot.Revenue/total_revenue

    # Ordenar los datos por porcentaje del volumen 
    # Primero los mas representativos
    pivot.sort_values(f'rev_{product}_weight', ascending=False, inplace=True)

    return pivot

def assign_group(value, group_size):
    group_number = (value // group_size) + 1
    return min(group_number, 5)

def compute_important_porf_factor(data, product, 
                                max_year, min_year, max_month):
    """
    """
    # seleccionar datos por año, mes y producto
    # traer la información de portfolio
    # me interesa resaltar los que mas han perdido
    max_year = data.loc[(data['Año']== max_year)&
                      (data['Mes'] == max_month)&
                      (data['Producto'] == product), 
                      ['Codigocliente', 'Portfolio']]    
    
    # crear grupos de acuerdo a la escala 
    min_year = data.loc[(data['Año']== min_year)&
                      (data['Mes'] == max_month)&
                      (data['Producto'] == product), 
                      ['Codigocliente', 'Portfolio']] 
    
    max_year['diff_porf'] = max_year['Portfolio'].astype(int).values - min_year['Portfolio'].astype(int).values
    # los que tienen valores negativos significa que estan perdiendo mas
    # mas que el año pasado
    # me interesa darle mas importancia a aquellos que perdieron
    max_year.loc[max_year.diff_porf>0, 'diff_porf'] = 0

    # Ordenar primero los datos de menor a mayor
    max_year = max_year.sort_values(by="diff_porf")

    num_unique_values = max_year['diff_porf'].unique().shape[0]

    group_size = max(1, (num_unique_values + 4) // 5)  # para segurar que esten en cinco grupos
    max_year['group'] = max_year['diff_porf'].apply(lambda x: assign_group(x, group_size))
    
    return max_year[['Codigocliente', 'group']]


def compute_important_var_factor(data, 
                                 key_var = 'Volumen', 
                                 result_name = 'vol_important_factor',
                                 qcuts = [0, .2, .4, .6, .8, 1], 
                                 bins_labels=[1, 2, 3, 4, 5]):
    """
    Esta función divide los datos por la variable especificada y 
    los bins solicitados. Genera los grupos de importancia
    sobre la variable de entrada.
    """
    # Define los percentiles por los cuales realiza la división
    data[result_name] = pd.qcut(data[key_var],
                                q = qcuts,
                                labels=bins_labels)
    
    print(np.unique(data[result_name].values, return_counts=True))
    
    return data

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

def weighting_3m(ratio, month, max_month):
    """
    Función para realizar la ponderación de la variable 
    Market share, y otras variables que lo requieran.
    Solo los tres ultimos meses.
    """
    diff = max_month - month
    if diff == 0: # quiere decir el último mes
        result = ratio*.5
    elif diff == 1: # quiere decir antepenultimo mes
        result = ratio*0.30
    elif diff == 2: # quiere decir 3 mes anterior
        result = ratio*.20

    
    return result

def reescale_by_month(x, dict_max, dict_min, key):
    month = x[0]
    value = x[1]
    max_val = dict_max[month][key]
    min_val = dict_min[month][key]

    new_value = (value - min_val) / (max_val - min_val)

    # invertir valor para que valores negativos tengan mas prioridad
    return 1 - new_value



def analysis_volumen_ratio(data, product, 
                           max_year, min_year, max_month):
    """
    Esta función realiza el análisis de la variable
    volumen sobre dos años de datos para el producto 
    seleccionado.
    """
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Volumen', 'Año', 'Mes', 'Producto']]

    min_year_data = data.loc[(data['Año']==min_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Volumen', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    min_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    max_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)

    #print(min_year_data.head(10))
    #print(max_year_data.head(10))

    # seleccionar los datos del dataframe final 
    vol_ratio = max_year_data[['Codigocliente', 'Mes', 'Producto']]
    
    # calcular la diferencia con respecto a los del año anterior
    vol_ratio[f'vol_{product}_losses'] = max_year_data.Volumen.values - min_year_data.Volumen.values

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes para d
    vol_ratio[f'vol_{product}_losses_weighted'] = \
        vol_ratio.apply(lambda x: weighting_6m(x[f'vol_{product}_losses'], 
                                                          x.Mes, 
                                                          max_month), axis=1)

    # Encontrar las perdidas mas grandes y las ganancias por cada cliente y mes
    dict_max = vol_ratio.groupby(['Mes']).agg({f'vol_{product}_losses_weighted':'max'})#.reset_index()
    dict_min = vol_ratio.groupby(['Mes']).agg({f'vol_{product}_losses_weighted':'min'})
    #dict_max.set_index('Mes', inplace=True)
    dict_max = dict_max.to_dict('index')
    dict_min = dict_min.to_dict('index')

    #print(dict_max)
    #print(dict_min)
    # reescalar el ratio por mes para que este en el rango de riesgo 
    #vol_ratio[f'vol_{product}_ratio'] = vol_ratio[['Mes',
    #                                               f'vol_{product}_ratio']].apply(lambda x: x[1]/dict_max[x[0]][f'vol_{product}_ratio'],
    #                                                axis=1)

    vol_ratio[f'vol_{product}_ratio_weighted'] = vol_ratio[['Mes',
                                                   f'vol_{product}_losses_weighted']].apply(lambda x: reescale_by_month(x, dict_max, dict_min, 
                                                                                                    key=f'vol_{product}_losses_weighted') ,
                                                                                                    axis=1)   
    
    return vol_ratio


def analysis_volumen_ratio_old(data, product, 
                           max_year, min_year, max_month):
    """
    Esta función realiza el análisis de la variable
    volumen sobre dos años de datos para el producto 
    seleccionado.
    """
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Volumen', 'Año', 'Mes', 'Producto']]

    min_year_data = data.loc[(data['Año']==min_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Volumen', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    min_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    max_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)

    # seleccionar los datos del dataframe final 
    vol_ratio = max_year_data[['Codigocliente', 'Mes', 'Producto']]
    
    # calcular el ratio con respecto a los del año anterior
    vol_ratio[f'vol_{product}_ratio'] = max_year_data.Volumen.values/min_year_data.Volumen.values

    # para aquellos que superen un ratio de 1.0 
    # truncarlos a este valor
    vol_ratio.loc[vol_ratio[f'vol_{product}_ratio']>1, f'vol_{product}_ratio'] = 1.0

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes ...
    vol_ratio[f'vol_{product}_ratio_weighted'] = vol_ratio.apply(lambda x: weighting_6m(x[f'vol_{product}_ratio'], 
                                                                                         x.Mes,
                                                                                         max_month), axis=1)
    
    return vol_ratio


def analysis_revenue_ratio(data, product, 
                           max_year, min_year, max_month):
    """
    Esta función realiza el análisis de la variable
    revenue sobre dos años de datos para el producto 
    seleccionado.
    """
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Revenue', 'Año', 'Mes', 'Producto']]

    min_year_data = data.loc[(data['Año']==min_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Revenue', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    min_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    max_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)

    # seleccionar los datos del dataframe final 
    revenue_ratio = max_year_data[['Codigocliente', 'Mes', 'Producto']]
    
    # calcular el ratio con respecto a los del año anterior
    revenue_ratio[f'rev_{product}_losses'] = max_year_data.Revenue.values - min_year_data.Revenue.values

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes para d
    revenue_ratio[f'rev_{product}_losses_weighted'] = \
        revenue_ratio.apply(lambda x: weighting_6m(x[f'rev_{product}_losses'], 
                                                          x.Mes, 
                                                          max_month), axis=1)

    # Encontrar las perdidas mas grandes y las ganancias por cada cliente y mes
    dict_max = revenue_ratio.groupby(['Mes']).agg({f'rev_{product}_losses_weighted':'max'})#.reset_index()
    dict_min = revenue_ratio.groupby(['Mes']).agg({f'rev_{product}_losses_weighted':'min'})
    #dict_max.set_index('Mes', inplace=True)
    dict_max = dict_max.to_dict('index')
    dict_min = dict_min.to_dict('index')
    
    revenue_ratio[f'rev_{product}_ratio_weighted'] = revenue_ratio[['Mes',
                                                   f'rev_{product}_losses_weighted']].apply(lambda x: reescale_by_month(x, dict_max, dict_min, 
                                                                                                    key=f'rev_{product}_losses_weighted') ,
                                                                                                    axis=1)   

    return revenue_ratio


def analysis_market_share_ratio(data, product, 
                           max_year, max_month):
    """
    Esta función realiza el análisis de la variable
    market share sobre el año mas reciente de datos
    para el producto seleccionado.
    """
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_months_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product)&
                              (data.Mes.isin([max_month, max_month-1, 
                                              max_month-2, max_month-3])),
                              ['Codigocliente', 'Volumen','Market Share', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    max_year_months_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    # desfazar un mes el volumen
    max_year_months_data['Vol_previous'] = max_year_months_data.groupby('Codigocliente')['Volumen'].shift(1)
    # hacer la resta del market share con el mes anterior
    max_year_months_data['Diff_Market_Share'] = max_year_months_data.groupby('Codigocliente')['Market Share'].diff()
    # multiplicar las diferencias del market share con el mes anterior para determinar
    # cuantas cajas de volumen han dejado de comprar
    max_year_months_data[f'mk_{product}_losses'] = max_year_months_data['Diff_Market_Share'] * max_year_months_data['Vol_previous']
    # como se hizo el desface, siempre queda el primer valor como nulo
    # se eliminan
    max_year_months_data.dropna(inplace=True)

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes para d
    max_year_months_data[f'mk_{product}_losses_weighted'] = \
        max_year_months_data.apply(lambda x: weighting_3m(x[f'mk_{product}_losses'], 
                                                          x.Mes, 
                                                          max_month), axis=1)


    final = max_year_months_data.groupby('Codigocliente')[f'mk_{product}_losses_weighted'].sum().to_frame()
    final.reset_index(inplace=True)

    final.rename(columns={f'mk_{product}_losses_weighted':f'mk_{product}_ratio_weighted'}, inplace=True)

    return final


def analysis_portfolio_ratio(data, product, 
                            max_year, min_year, max_month):
    """
    """
    # 1. Computar scores basado en la geo referenciación
    filtered_data = data.loc[(data['Año']==max_year)&
                             (data['Mes']==max_month)&
                             (data['Producto']==product), 
                            ['Codigocliente', 'Portfolio', 'Año', 
                             'Mes', 'Producto', 'Latitud', 'Longitud']]
    
    max_porf = filtered_data.Portfolio.max()
    
    # 1.1 Obtener dataframe con codigo de cliente, portfolio y coordenadas
    unique_customers = filtered_data.groupby('Codigocliente').agg({'Longitud': 'first', 
                                                                   'Latitud': 'first', 
                                                                   'Portfolio':'first'}).reset_index()

    # 1.2 Crear el Geo DataFrame
    crs = {'init': 'epsg:4326'} # Generar la proyección para trabajar con lon y lat
    # Crear los puntos bajo la proyección
    geometry = [Point(x, y) for x, y in zip(unique_customers['Longitud'], unique_customers['Latitud'])]
    # Crear el dataframe para todos los clientes
    gdf = gpd.GeoDataFrame({'Codigocliente': unique_customers['Codigocliente'], 
                            'portfolio': unique_customers['Portfolio'],
                            'Longitud': unique_customers['Longitud'],
                            'Latitud': unique_customers['Latitud'],
                            'geometry': geometry}, crs=crs)

    # 1.3 Scalar las coordenadas junto con el portfolio hacer el clustering
    # Crear el MinMaxScaler 
    min_clients_cluster = 20 # número minimo de clientes por cluster
    scaler = MinMaxScaler()
    coords = gdf[['Latitud', 'Longitud', 'portfolio']].values
    scaled_coords = scaler.fit_transform(coords)
    
    # 1.4 Clustering
    solver = make_high_variable_clusters(method='KMeans', 
                             coords=scaled_coords, 
                             min_clients_cluster=min_clients_cluster, 
                             epsilon=None, metric=None)
    
    # Asignar los primero labels a cada cliente
    gdf['cluster'] = solver.labels_
    
    # 1.5 Calcular metricas por cluster
    metrics = gdf.groupby('cluster').agg({'portfolio':['median', 'count']})
    metrics.columns = metrics.columns.map('_'.join)
    metrics.reset_index(inplace=True)

    # 1.6 Calcular los clusters con zonas densas de alto portfolio
    high_portfolio = int(max_porf*.8) # otra variable para configurar
    high_portfolio_clusters = metrics.loc[(metrics.portfolio_count>=min_clients_cluster//4)&
                                     (metrics.portfolio_median>=high_portfolio)].cluster.values

    # 1.7 Calcular los puntos referentes en cada cluster
    list_centermost = []
    for hpc in high_portfolio_clusters:
        cluster_series = gdf.loc[gdf.cluster==hpc, ['Latitud', 'Longitud']].squeeze()
        list_centermost.append(get_centermost_point(cluster_series.values))

    # 1.8 Crear el geo dataframe para los puntos representativos de cada cluster
    # con la misma proyección
    lats, lons = zip(*list_centermost)
    rep_points = pd.DataFrame({'lon':lons, 'lat':lats})
    rep_points['cluster'] = high_portfolio_clusters
    # Crear Geo Dataframe
    geometry_rep = [Point(x, y) for x, y in zip(rep_points['lon'], rep_points['lat'])]
    gdf_rep = gpd.GeoDataFrame({
                            'cluster': rep_points['cluster'],
                            'Longitud': rep_points['lon'],
                            'Latitud': rep_points['lat'],
                            'geometry': geometry_rep}, crs=crs)

    # 1.9 Eliminar clusters que esten muy cercanos
    # y muy amplios --> TODO
    distances = pdist(gdf_rep[['Longitud', 'Latitud']])
    # basado en el threshold para eliminar esos clusters
    th_dist = np.mean(distances) - 2 * (np.std(distances))
    # Crear las parejas de puntos para calcular las distancias
    pairs = create_row_pairs(gdf_rep[['Longitud', 'Latitud', 'cluster']])
    # Delete clusters
    high_portfolio_clusters, gdf_rep = delete_clusters(gdf_rep, 
                                                       pairs, 
                                                       high_portfolio_clusters,
                                                       th_dist)
    
    # 1.10 Calcular los scores basado en el radio de los clusters
    # para esto debemos proyectar los puntos a un espacio que este
    # en metros .. Para colombia pueden ser los codigos 17, 18 o 19
    gdf_rep = gdf_rep.to_crs(epsg=32618)
    gdf = gdf.to_crs(epsg=32618)
    gdf_rep.reset_index(drop=True, inplace=True)

    # Calcular el maximo valor del portfolio para las zonas densas
    # resultado un diccionario con el codigo del cluster 
    # y su valor medio de portfolio
    max_portfolio_dict = gdf.loc[gdf.cluster.isin(high_portfolio_clusters)]\
                                .groupby('cluster').agg({'portfolio':'median'})\
                                .to_dict()['portfolio']

    gdf, circle_coors = compute_score_circles(gdf, gdf_rep, max_portfolio_dict, r_meters=200)

    # 1.11 Asignar cluster y score para los puntos que quedaron 
    # por fuera de las zonas
    #result_df = assign_cluster_to_missing_scores(customers_gdf=gdf, centroids_gdf=gdf_rep)
    result_df = assign_minus1_cluster(customers_gdf=gdf, centroids_gdf=gdf_rep) # asigna un cluster -1 a los que no tienen cluster

    # Actualizar los datos que ya tenian cluster con los que no
    gdf = gdf.merge(result_df[['Codigocliente', 'new_cluster']], 
                    on='Codigocliente',  how='left', validate='1:1')
    # Combinar, dejar solo una columna
    gdf['new_cluster'] = gdf['new_cluster_x'].combine_first(gdf['new_cluster_y'])
    # Eliminar las columnas innecesarias
    gdf = gdf.drop(['new_cluster_x', 'new_cluster_y'], axis=1)

    # Generar score a los registros faltantes
    #missing_scores = gdf.loc[gdf.score.isna()].apply(lambda x: generate_score(max_portfolio_dict[int(x.new_cluster)], 
    #                                                                          x.portfolio), axis=1)
    # Actualizar scores
    #gdf.loc[gdf.score.isna(), 'score'] = missing_scores
    gdf.loc[gdf.score.isna(), 'score'] = 0

    ############################################################
    # Ahora computar los scores basado en el analisis temporal
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Portfolio', 'Año', 'Mes', 'Producto']]

    min_year_data = data.loc[(data['Año']==min_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Portfolio', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    min_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    max_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)

    # seleccionar los datos del dataframe final 
    porf_ratio = max_year_data[['Codigocliente', 'Mes', 'Producto']]
    
    # calcular el ratio con respecto a los del año anterior
    porf_ratio[f'porf_{product}_ratio'] = max_year_data.Portfolio.values/min_year_data.Portfolio.values

    # para aquellos que superen un ratio de 1.0 
    # truncarlos a este valor
    #porf_ratio.loc[porf_ratio[f'porf_{product}_ratio']>1, f'porf_{product}_ratio'] = 1.0

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes ...
    porf_ratio[f'porf_{product}_ratio_weighted'] = porf_ratio.apply(lambda x: weighting_6m(x[f'porf_{product}_ratio'], 
                                                                                         x.Mes,
                                                                                         max_month), axis=1)
    
    # Encontrar las perdidas mas grandes y las ganancias por cada cliente y mes
    dict_max = porf_ratio.groupby(['Mes']).agg({f'porf_{product}_ratio_weighted':'max'})#.reset_index()
    dict_min = porf_ratio.groupby(['Mes']).agg({f'porf_{product}_ratio_weighted':'min'})
    #dict_max.set_index('Mes', inplace=True)
    dict_max = dict_max.to_dict('index')
    dict_min = dict_min.to_dict('index')
    
    porf_ratio[f'porf_{product}_ratio_weighted'] = porf_ratio[['Mes',
                                                   f'porf_{product}_ratio_weighted']].apply(lambda x: reescale_by_month(x, dict_max, dict_min, 
                                                                                                    key=f'porf_{product}_ratio_weighted') ,
                                                                                                    axis=1)   

    return gdf, porf_ratio


def analysis_mixpremium_ratio(data, product, 
                            max_year, min_year, max_month):
    """
    """
    # 1. Computar scores basado en la geo referenciación
    filtered_data = data.loc[(data['Año']==max_year)&
                             (data['Mes']==max_month)&
                             (data['Producto']==product), 
                            ['Codigocliente', 'Mix Premium', 'Año', 
                             'Mes', 'Producto', 'Latitud', 'Longitud']]
    
    # 1.1 Obtener dataframe con codigo de cliente, mix premium y coordenadas
    unique_customers = filtered_data.groupby('Codigocliente').agg({'Longitud': 'first', 
                                                                   'Latitud': 'first', 
                                                                   'Mix Premium':'first'}).reset_index()

    # 1.2 Crear el Geo DataFrame
    crs = {'init': 'epsg:4326'} # Generar la proyección para trabajar con lon y lat
    # Crear los puntos bajo la proyección
    geometry = [Point(x, y) for x, y in zip(unique_customers['Longitud'], unique_customers['Latitud'])]
    # Crear el dataframe para todos los clientes
    gdf = gpd.GeoDataFrame({'Codigocliente': unique_customers['Codigocliente'], 
                            'mix premium': unique_customers['Mix Premium'],
                            'Longitud': unique_customers['Longitud'],
                            'Latitud': unique_customers['Latitud'],
                            'geometry': geometry}, crs=crs)

    # 1.3 Scalar las coordenadas (mix premium ya esta escalada) hacer el clustering
    # Crear el MinMaxScaler 
    min_clients_cluster = 20 # número minimo de clientes por cluster
    scaler = MinMaxScaler()
    coords = gdf[['Latitud', 'Longitud']].values
    scaled_coords = scaler.fit_transform(coords)

    mixp = gdf['mix premium'].values
    mixp = mixp.reshape((mixp.shape[0],1))
    scaled_coords = np.hstack((scaled_coords, mixp))
    
    # 1.4 Clustering
    solver = make_high_variable_clusters(method='KMeans', 
                             coords=scaled_coords, 
                             min_clients_cluster=min_clients_cluster, 
                             epsilon=None, metric=None)
    
    # Asignar los primero labels a cada cliente
    gdf['cluster'] = solver.labels_
    
    # 1.5 Calcular metricas por cluster
    metrics = gdf.groupby('cluster').agg({'mix premium':['median', 'count']})
    metrics.columns = metrics.columns.map('_'.join)
    metrics.reset_index(inplace=True)

    # 1.6 Calcular los clusters con zonas densas de alto mix premium
    sorted_clusters_mixp = sorted(metrics['mix premium_median'].unique())
    len_mixp = len(sorted_clusters_mixp)

    ## seleccione el 25% de los clusters mas grandes in mix premium
    high_mixp = sorted(metrics['mix premium_median'].unique())[-int(len_mixp*0.25):][0]
    high_mixp_clusters = metrics.loc[(metrics['mix premium_count']>=min_clients_cluster//3)&
                            (metrics['mix premium_median']>=high_mixp)].cluster.values 

    # 1.7 Calcular los puntos referentes en cada cluster
    list_centermost = []
    for hpc in high_mixp_clusters:
        cluster_series = gdf.loc[gdf.cluster==hpc, ['Latitud', 'Longitud']].squeeze()
        list_centermost.append(get_centermost_point(cluster_series.values))

    # 1.8 Crear el geo dataframe para los puntos representativos de cada cluster
    # con la misma proyección
    lats, lons = zip(*list_centermost)
    rep_points = pd.DataFrame({'lon':lons, 'lat':lats})
    rep_points['cluster'] = high_mixp_clusters
    # Crear Geo Dataframe
    geometry_rep = [Point(x, y) for x, y in zip(rep_points['lon'], rep_points['lat'])]
    gdf_rep = gpd.GeoDataFrame({
                            'cluster': rep_points['cluster'],
                            'Longitud': rep_points['lon'],
                            'Latitud': rep_points['lat'],
                            'geometry': geometry_rep}, crs=crs)

    # 1.9 Eliminar clusters que esten muy cercanos
    # y muy amplios --> TODO
    distances = pdist(gdf_rep[['Longitud', 'Latitud']])
    # basado en el threshold para eliminar esos clusters
    th_dist = np.mean(distances) - 2 * (np.std(distances))
    # Crear las parejas de puntos para calcular las distancias
    pairs = create_row_pairs(gdf_rep[['Longitud', 'Latitud', 'cluster']])
    # Delete clusters
    high_mixp_clusters, gdf_rep = delete_clusters(gdf_rep, 
                                                       pairs, 
                                                       high_mixp_clusters,
                                                       th_dist)
    
    # 1.10 Calcular los scores basado en el radio de los clusters
    # para esto debemos proyectar los puntos a un espacio que este
    # en metros .. Para colombia pueden ser los codigos 17, 18 o 19
    gdf_rep = gdf_rep.to_crs(epsg=32618)
    gdf = gdf.to_crs(epsg=32618)
    gdf_rep.reset_index(drop=True, inplace=True)

    # Calcular el maximo valor del mixp para las zonas densas
    # resultado un diccionario con el codigo del cluster 
    # y su valor medio de mix premium
    max_mixp_dict = gdf.loc[gdf.cluster.isin(high_mixp_clusters)]\
                                .groupby('cluster').agg({'mix premium':'median'})\
                                .to_dict()['mix premium']

    gdf, circle_coors = compute_score_circles_mixp(gdf, gdf_rep, 
                                                   max_mixp_dict, r_meters=200)

    # 1.11 Asignar cluster y score para los puntos que quedaron 
    # por fuera de las zonas
    #result_df = assign_cluster_to_missing_scores(customers_gdf=gdf, centroids_gdf=gdf_rep)
    result_df = assign_minus1_cluster(customers_gdf=gdf, centroids_gdf=gdf_rep)

    # Actualizar los datos que ya tenian cluster con los que no
    gdf = gdf.merge(result_df[['Codigocliente', 'new_cluster']], 
                    on='Codigocliente',  how='left', validate='1:1')
    # Combinar, dejar solo una columna
    gdf['new_cluster'] = gdf['new_cluster_x'].combine_first(gdf['new_cluster_y'])
    # Eliminar las columnas innecesarias
    gdf = gdf.drop(['new_cluster_x', 'new_cluster_y'], axis=1)

    # Generar score a los registros faltantes
    #missing_scores = gdf.loc[gdf.score.isna()].apply(lambda x: generate_score(max_mixp_dict[int(x.new_cluster)], 
    #                                                                          x['mix premium']), axis=1)

    # Actualizar scores
    #gdf.loc[gdf.score.isna(), 'score'] = missing_scores
    gdf.loc[gdf.score.isna(), 'score'] = 0

    ############################################################
    # Ahora computar los scores basado en el analisis temporal
    # Seleccionar los datos para el producto, la variable 
    # y los años 
    max_year_data = data.loc[(data['Año']==max_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Mix Premium', 'Año', 'Mes', 'Producto']]

    min_year_data = data.loc[(data['Año']==min_year)&
                              (data['Producto']==product), 
                              ['Codigocliente', 'Mix Premium', 'Año', 'Mes', 'Producto']]
    
    # Ordenar los datos por codigo cliente y mes
    min_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)
    max_year_data.sort_values(by=['Codigocliente', 'Mes'], inplace=True)

    # seleccionar los datos del dataframe final 
    mixp_ratio = max_year_data[['Codigocliente', 'Mes', 'Producto']]
    
    # calcular el ratio con respecto a los del año anterior
    mixp_ratio[f'mixp_{product}_ratio'] = max_year_data['Mix Premium'].values/min_year_data['Mix Premium'].values

    # para aquellos que superen un ratio de 1.0 
    # truncarlos a este valor
    #mixp_ratio.loc[mixp_ratio[f'mixp_{product}_ratio']>1, f'mixp_{product}_ratio'] = 1.0

    # finalmente realizar la ponderación de acuerdo el peso dado a 
    # cada mes ...
    mixp_ratio[f'mixp_{product}_ratio_weighted'] = mixp_ratio.apply(lambda x: weighting_6m(x[f'mixp_{product}_ratio'], 
                                                                                         x.Mes,
                                                                                         max_month), axis=1)

    
        # Encontrar las perdidas mas grandes y las ganancias por cada cliente y mes
    dict_max = mixp_ratio.groupby(['Mes']).agg({f'mixp_{product}_ratio_weighted':'max'})#.reset_index()
    dict_min = mixp_ratio.groupby(['Mes']).agg({f'mixp_{product}_ratio_weighted':'min'})
    #dict_max.set_index('Mes', inplace=True)
    dict_max = dict_max.to_dict('index')
    dict_min = dict_min.to_dict('index')
    
    mixp_ratio[f'mixp_{product}_ratio_weighted'] = mixp_ratio[['Mes',
                                                   f'mixp_{product}_ratio_weighted']].apply(lambda x: reescale_by_month(x, dict_max, dict_min, 
                                                                                                    key=f'mixp_{product}_ratio_weighted') ,
                                                                                                    axis=1)   

    
    
    return gdf, mixp_ratio    


def compute_score_circles_mixp(gdf, gdf_rep, 
                               max_mixp_dict, r_meters=250):
    """
    """
    circle_coors = []
    gdf['score'] = np.nan
    gdf['new_cluster'] = np.nan

    for enum, important_cl in enumerate(gdf_rep.cluster.values):
        circle = gdf_rep.loc[gdf_rep.cluster==important_cl].geometry.buffer(r_meters, 16)

        # Get circle coords
        x = circle.exterior.get_coordinates().x
        y = circle.exterior.get_coordinates().y
        circle_coors.append([x,y])

        # Check if there is a previous maximum portfolio for this cluster
        max_mixp = max_mixp_dict.get(important_cl, 0)

        # Iterate over each record in the circle
        for record_index, record in gdf.iterrows():
            if circle[enum].contains(record['geometry']):
                if np.isnan(gdf.loc[record_index, 'score']):
                    # Calculate the score based on the portfolio's distance from the maximum portfolio
                    score = generate_score(max_mixp, record['mix premium'])    

                    # Assign the score to the 'score' column in the GeoDataFrame
                    gdf.loc[record_index, 'score'] = score
                    gdf.loc[record_index, 'new_cluster'] = important_cl
        
    return gdf, circle_coors


def make_high_variable_clusters(method, coords, min_clients_cluster, epsilon, metric):
    """
    """
    if method == 'DBSCAN':
        solver = DBSCAN(eps=epsilon, min_samples=min_clients_cluster, 
                    algorithm='ball_tree', metric=metric).fit(coords)
    else:
        solver = KMeans(int(len(coords)//min_clients_cluster), random_state=9).fit(coords)
        
    return solver


def get_centermost_point(cluster):
    """
    """
    # Crea el poligono y trae el centroide
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)

    # Calcula el punto mas cercano al cluster
    centermost_point = min(cluster, key=lambda point: great_circle(point, centroid).m)

    return tuple(centermost_point)


def create_row_pairs(df):
    """
    """
    # Obtener todas las combinaciones de los indices 
    # sin repetir
    indices_combinations = combinations(df.index, 2)

    # Crear pares de filas usando las combinaciones
    row_pairs = [(df.loc[i][['Longitud', 'Latitud']].values, 
                  df.loc[j][['Longitud', 'Latitud']].values, 
                  df.loc[i]['cluster'], 
                  df.loc[j]['cluster']) for i, j in indices_combinations]

    # Convertir la lista en un dataframe
    pairs_df = pd.DataFrame(row_pairs, columns=['point1', 'point2', 'cluster1', 'cluster2'])

    return pairs_df


def delete_clusters(gdf_rep, pairs, high_variable_clusters, th_dist):
    """
    """
    clusters_to_delete = []
    for ind, row in pairs.iterrows():
        dist = euclidean(row.point1, row.point2)
        if dist <= th_dist:
            # TODO: una idea seria eliminar el que este menos denso
            clusters_to_delete.append(row.cluster2)

    # obtener los unicos indixes
    clusters_to_delete = set(clusters_to_delete)
    # Actualizar la lista de los clusters con alto portfolio
    high_variable_clusters = list(set(high_variable_clusters).difference(clusters_to_delete))
    # Actualizar el dataframe con los puntos representativos
    gdf_rep = gdf_rep[~gdf_rep['cluster'].isin(clusters_to_delete)]
    
    return high_variable_clusters, gdf_rep


def generate_score(max_portfolio, portfolio):
    """
    """
    # Calculate the score based on the portfolio's distance from the maximum portfolio
    distance_from_max = abs(max_portfolio - portfolio)
    score = distance_from_max / max_portfolio
    
    if portfolio > max_portfolio:
        score = 0.0
    
    return score


def compute_score_circles(gdf, gdf_rep, max_portfolio_dict, r_meters=250):
    """
    """
    circle_coors = []
    gdf['score'] = np.nan
    gdf['new_cluster'] = np.nan

    for enum, important_cl in enumerate(gdf_rep.cluster.values):
        # Calcular un circulo de radio "r_meters"
        # el 16 significa que tan circular es el circulo :D
        circle = gdf_rep.loc[gdf_rep.cluster==important_cl]\
                        .geometry.buffer(r_meters, 16)

        # Obtener las coordenadas de cada circulo
        x = circle.exterior.get_coordinates().x
        y = circle.exterior.get_coordinates().y
        circle_coors.append([x,y])

        # Obtiene el max valor de portfolio para el cluster
        max_portfolio = max_portfolio_dict.get(important_cl, 0)

        # Itera sobre cada punto
        for record_index, record in gdf.iterrows():
            # Valida si el punto esta dentro de la circunferencia
            if circle[enum].contains(record['geometry']):
                # Valida si ya tiene score
                # TODO: Validar a cual cluster esta mas cerca
                if np.isnan(gdf.loc[record_index, 'score']):
                    # Calcula el score basado en la diferencia del portfolio
                    # de cada cliente y el maximo para el cluster
                    score = generate_score(max_portfolio, record['portfolio'])    

                    # Asigna el score a la columna
                    gdf.loc[record_index, 'score'] = score
                    # El nuevo cluster indica la reasignación
                    gdf.loc[record_index, 'new_cluster'] = important_cl

                # Actualiza el max valor del portfolio en caso
                # de que exista un punto aislado con mas portfolio
                #max_portfolio = max(max_portfolio, record['portfolio'])

        #max_portfolio_dict[important_cl] = max_portfolio 
        
    return gdf, circle_coors


def assign_cluster_to_missing_scores(customers_gdf, centroids_gdf):
    """
    """
    # Ensure both GeoDataFrames have a consistent CRS (Coordinate Reference System)
    #customers_gdf = customers_gdf.to_crs(centroids_gdf.crs)

    # Extract coordinates and cluster IDs
    customer_coords = customers_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist()
    centroids_coords = centroids_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist()
    cluster_ids = centroids_gdf['cluster'].tolist()

    # Build a BallTree for efficient nearest neighbor search
    tree = BallTree(centroids_coords)

    # Find the nearest centroid for each point without a score
    missing_score_points = customers_gdf[customers_gdf['score'].isna()]
    missing_score_coords = missing_score_points.geometry.apply(lambda geom: (geom.x, geom.y)).tolist()
    
    distances, indices = tree.query(missing_score_coords, k=1)
    
    # Assign the cluster ID of the nearest centroid to points without a score
    missing_score_points['new_cluster'] = [cluster_ids[idx[0]] for idx in indices]

    return missing_score_points

def assign_minus1_cluster(customers_gdf, centroids_gdf):
    """
    """
    # Find the nearest centroid for each point without a score
    missing_score_points = customers_gdf[customers_gdf['score'].isna()]
    
    # Assign the cluster ID of the nearest centroid to points without a score
    missing_score_points['new_cluster'] = -1

    return missing_score_points


def compute_risk(data_ratio, key_column):
    """
    Esta función calcula el score de riesgo.
    Entre mayor significa que tiene mayor prioridad.
    Es el ultimo paso de la suma ponderada.
    A esta funcion hay que pasarle solo los meses del año actual
    """
    # Aplicó suma porque ya todos los ratios estan ponderados por mes.
    # al suma estaria haciendo el promedio ponderado.
    # luego lo resto a 1 para llevarlo al sentido de score de prioridad.
    final_data_ratio = data_ratio.groupby(['Codigocliente']).agg({key_column:'sum'}).reset_index()
    final_data_ratio[f'{key_column}_risk'] = 1 - final_data_ratio[key_column]

    return final_data_ratio

def compute_risk_minmax(data_ratio, key_column):
    """
    Esta función calcula el score de riesgo normalizado
    para la variable mk
    """

    # encontrar los valores minimos y maximos para hacer el reescalado
    min_val = data_ratio[key_column].min()
    max_val = data_ratio[key_column].max()

    #print(min_val)
    #print(max_val)

    # hacer el reescalado de las perdidas teniendo en cuenta 
    # las ganancias y las perdidas
    # se hace un reescaladado invertido
    data_ratio[f'{key_column}_risk'] = (data_ratio[key_column] - max_val) / (min_val - max_val)
    
    
    #print(max_year_months_data[['Codigocliente', 'Mes','Volumen', 'Market Share','Diff_Market_Share', f'mk_{product}_losses',
    #                             f'mk_{product}_losses_weighted']].head(40))
    #print(final.head(30))
    #quit()

    return data_ratio

def compute_risk_way2(data_ratio, key_column):
    """
    Esta función calcula el score de riesgo.
    Entre mayor significa que tiene mayor prioridad.
    Es el ultimo paso de la suma ponderada.
    A esta funcion hay que pasarle solo los meses del año actual
    """
    # Aplicó suma porque ya todos los ratios estan ponderados por mes.
    # al suma estaria haciendo el promedio ponderado.
    # luego lo resto a 1 para llevarlo al sentido de score de prioridad.
    final_data_ratio = data_ratio.groupby(['Codigocliente']).agg({key_column:'sum'}).reset_index()
    # finalmente reescalar contra el maximo mes
    max_client = final_data_ratio[key_column].max()
    final_data_ratio[f'{key_column}_risk'] = final_data_ratio[key_column].apply(lambda x: x/max_client)  

    return final_data_ratio


def fx_integration_IF(data, risk_col_name, if_col_name):
    """
    Esta función integra el valor de prioridad de la variable
    para cada cliente con su respectivo factor de importancia
    """
    # la formula es tomar el valor de priodidad que esta en
    # rango de 0-1 y lo eleva a 1/(p-0.5)
    # primero hay que convertir el campo de factor de importancia
    # de categorical a entero, para poder hacer la operación
    result = data[risk_col_name]**(1/(data[if_col_name].astype(int)-0.5))
    
    return result.values

# definir una función para corroborar el volumen de ventas en 0
def has_zero_sales(group):
    #print(group['Volumen'])
    return (group['Volumen'] == 0).all()