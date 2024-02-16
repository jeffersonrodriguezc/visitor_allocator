import numpy as np
import pandas as pd
from tkinter import messagebox

def distribute_visits(df, score_name, parameters, codes_rule_2=None):
    """
    Este algoritmo distribuye un total de visitas maximo
    en todos los clientes teniendo en cuenta su score
    de prioridad
    """
    total_capacity = int(parameters['total_visits_0'])
    # Primero que todo aplicar la primera regla si esta activa
    if parameters['regla_1'] == 'si':
        # Para aplicar esta regla es necesario tener o
        # var_product_weight o rev_product_weight
        # alguna de las dos pero en ese orden de prioridad
        key_name = ''
        key_names = []
        volumen_flag = False
        for enum, var in enumerate([parameters['variable_1'], 
                    parameters['variable_2'],
                    parameters['variable_3']]):
            
            if var == 'Volumen':
                key_name = f'vol_{parameters[f"product_{enum+1}"]}_weight'
                key_names.append(key_name)
                volumen_flag = True

            elif var == 'Revenue' and volumen_flag == False:
                key_name = f'rev_{parameters[f"product_{enum+1}"]}_weight'
                key_names.append(key_name)
            else:
                pass

        if len(key_names) > 1:
            key_name = sorted(key_names)[-1]
        else:
            key_name = sorted(key_names)[0]
        # Ahora ordenarlos por el key_name, cacular la suma acumulativa
        # y seleccionar los que representan el volumen especificado y 
        # se le aplica la periodicidad de visitas especificada
        if key_name != '':
            #print(key_name)
            df.sort_values(key_name, inplace=True, ascending=False) 
            df['cumsum'] = df[key_name].cumsum()
            #print(df['cumsum'])
            # Seleccionar los clientes que aportan el porcentaje indicado
            df_cc = df.loc[df['cumsum']<=float(int(parameters['Regla_1_var_X2'])/100)]
            #print('regla 1',df_cc.shape)
            # colocar el numero de visitas por defecto para estos clientes
            if parameters['Regla_1_var_X1'] == 'Semanal':
                cc_visits = 4
            elif parameters['Regla_1_var_X1'] == 'Trisemanal':
                cc_visits = 3
            elif parameters['Regla_1_var_X1'] == 'Quincenal':
                cc_visits = 2
            elif parameters['Regla_1_var_X1'] == 'Mensual':
                cc_visits = 1

            # Asignar las visitas
            df_cc['num_visits_month'] = cc_visits
            # colocar que es por regla 1
            df_cc['notes'] = 'Definido por Regla 1'
            # Calcular cuantas visitas fueron asignadas
            total_visitas_asignadas = cc_visits*df_cc.shape[0]
            # Filtrar los clientes resultantes para asignarles visitas
            df = df.loc[~df['Codigocliente'].isin(df_cc['Codigocliente'])]
    
            # actualizar el numero de visitas restante
            total_capacity = total_capacity -  total_visitas_asignadas
    
    
    # Aplicar regla 2 de coberturas
    if parameters['regla_2'] == 'si':

        if parameters['Regla_2_var_X1'] == 'Semanal':
            cc_visits = 4
        elif parameters['Regla_2_var_X1'] == 'Trisemanal':
            cc_visits = 3
        elif parameters['Regla_2_var_X1'] == 'Quincenal':
            cc_visits = 2
        elif parameters['Regla_2_var_X1'] == 'Mensual':
            cc_visits = 1

        total_visitas_asignadas = cc_visits*codes_rule_2.shape[0]
        
        # actualizar el numero de visitas restante
        total_capacity = total_capacity -  total_visitas_asignadas

        # filtrar los clientes
        df_cc_2 = df.loc[df['Codigocliente'].isin(codes_rule_2)]
        df_cc_2['notes'] =  'Definido por Regla 2'
        df_cc_2['num_visits_month'] = cc_visits

        df = df.loc[~df['Codigocliente'].isin(codes_rule_2)]
        #print(codes_rule_2)

    
    if total_capacity <= 0:
        return False
    
    # Ordenar los datos de menor a mayor basado en el score
    df_sorted = df.sort_values(by=score_name)

    # Determinar el numero de grupos 
    # Uno para cada frecuencia de visita
    # Relacionados esto con la tercera regla
    # por defecto dejaremos 1 y 4 
    if parameters['regla_3'] == 'si':
        num_groups = int(parameters['Regla_3_var_X2'])
    else:
        num_groups = 4

    # Calcular el percentil para definir los grupos iniciales
    amplitud = 100//num_groups
    percentiles = [(i * amplitud)/100 for i in range(num_groups+1)]
    
    # Asignar cada cliente a un grupo basado en su percentil
    df_sorted['group'] = pd.qcut(df_sorted[score_name], percentiles, labels=False) + 1
    # Asignar las visitas iniciales
    df_sorted['num_visits'] = df_sorted['group']
    # Solo para comparar en el archivo final
    df_sorted['num_visits_initial'] = df_sorted['group']
    
    # Calcular cuantas visitas se necesitarian inicialmente
    # para cubrir la asignación inicial
    initial_total_capacity = df_sorted['num_visits'].sum()
    # Calculo aproximado de cuantas visitas debo mover de cada grupo
    # para llegar hasta mi capacidad maxima de visitas
    total_visits_to_move = initial_total_capacity - total_capacity
    #print('total visits to move',total_visits_to_move)
    #print('initial_total_capacity', initial_total_capacity)
    #print('total_capacity', total_capacity)

    move_from_each_group = df_sorted.groupby('group')['num_visits'].sum() * (total_visits_to_move / initial_total_capacity)

    # Redondear al entero mas cercano
    move_from_each_group = move_from_each_group.round().astype(int)
    #print('move_from_each_group', move_from_each_group)
    # Iterar hasta que se logre llegar al maximo de visitas por mes
    #print(initial_total_capacity > total_capacity)
    while initial_total_capacity > total_capacity:
        #print(initial_total_capacity)
        # Ir calculando el desface que se tiene entre el numero
        # de visitas que estaría gastando y el maximo de visitas que tengo
        total_visits_to_move = initial_total_capacity - total_capacity
        
        # Iterar sobre cada grupo del percentil
        # Menos el percentil 1 (no puedo tener clientes sin visitar)
        # TODO: aqui deberia ir incorporado la regla
        for group_num in range(num_groups, 1, -1):
            #print('group_num',group_num)
            # Calcular el numero de clientes a mover de cada grupo   
            # Será el valor del numero de clientes que tengo en caso de 
            # que la divisón me de mas de lo que tengo en ese grupo        
            num_customers_to_move = min(move_from_each_group[group_num]//group_num, 
                                        len(df_sorted[df_sorted['num_visits'] == group_num]))
            
            #print('num_customers_to_move', num_customers_to_move)
            
            # Esto es para evitar perder visitas al final 
            # Es decir ser lo mas cercano al maximo de visitas al mes
            if (num_customers_to_move * group_num) > total_visits_to_move:
                # Recalcular los clientes que voy a mover
                # Se necesita hacer el redondeo hacia arriba 
                num_customers_to_move = int(np.ceil(total_visits_to_move/group_num))
            
            # Ahora seleccionar los clientes con el score mas bajo para ese grupo
            # Recordar que esto se puede ya que estan ordenados
            ccustomers = df_sorted.loc[df_sorted['num_visits'] == group_num, 'Codigocliente'].values[:num_customers_to_move]
            
            # Actualizar el numero de visitas de los clientes seleccionados
            df_sorted.loc[df_sorted['Codigocliente'].isin(ccustomers), 'num_visits'] -= 1

            # Mover los clientes al grupo del percentil anterior
            df_sorted.loc[df_sorted['Codigocliente'].isin(ccustomers), 'group'] = group_num - 1

            # Actualizar las nuevas visitas que estaria gastando
            initial_total_capacity = df_sorted['num_visits'].sum()
            
            # Ordenar los datos de nuevo para seguir asegurando
            # Seleccionar los mas bajos de cada grupo
            df_sorted = df_sorted.sort_values(by=score_name)

            visits_groups = df_sorted['num_visits'].unique()
            # esto pasa cuando ni colocando uno a todos los clientes soy capaz
            # de cumplir la capacidad maxima
            total_visits_to_move = initial_total_capacity - total_capacity
            if len(visits_groups) == 1 and total_visits_to_move>0:
                # break the while loop
                visits_to_increment = initial_total_capacity - total_capacity
                messagebox.showwarning('Total visitas insuficiente', f"Sugerimos incrementar el número de visitas en almenos {total_visits_to_move} visitas")
                initial_total_capacity = 0

        # Seguir iterando si el total de la capacidad todavia no se cumple

    # En caso de que hayan mas visitas que las ideale se distribuyen
    # equitativamente
    if total_visits_to_move < 0:
        df_sorted = df_sorted.sort_values(by=score_name)
        # repartir las visitas en los grupos 1,2 y 3 equitativamente
        visits_per_group = abs(total_visits_to_move)//3
        # traer ese numero de personas por grupo y sumarles 1 
        # traer los mas cercanos al limite
        for group in [1, 2, 3]:
            top_clients = df_sorted[df_sorted['num_visits'] == group].nlargest(visits_per_group, 
                                                                               score_name)['Codigocliente']
            
            # Y luego aumentar su numero de visitas en uno
            df_sorted.loc[df_sorted['Codigocliente'].isin(top_clients), 'num_visits'] += 1

    # Finalmente eliminar la columna temporal 'group'
    df_sorted = df_sorted.drop('group', axis=1)
    df_sorted.rename(columns={'num_visits':'num_visits_month'}, inplace=True)

    if parameters['regla_1'] == 'si' and parameters['regla_2'] == 'si':
        return pd.concat([df_sorted, df_cc, df_cc_2])
    
    elif parameters['regla_1'] == 'si' and parameters['regla_2'] == 'no':
        return pd.concat([df_sorted, df_cc])
    
    elif parameters['regla_1'] == 'no' and parameters['regla_2'] == 'si':
        return pd.concat([df_sorted, df_cc_2])
    
    else:
        return df_sorted 