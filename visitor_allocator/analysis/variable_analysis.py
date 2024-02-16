import warnings
import pandas as pd
warnings.filterwarnings("ignore")
from tkinter import messagebox

import visitor_allocator.analysis.utils as analysis_fun
from visitor_allocator.allocator.allocator import distribute_visits 
#import analysis.utils as analysis_fun
#from allocator.allocator import distribute_visits 


def run_analysis(excel_data, parameters):
    """
    Esta funcion principal ejecuta todo el analisis sobre cada zona.
    Para cada zona aplica el mismo analisis de manera independiente.
    """
    # Eliminar espacios en blanco de las columnas
    excel_data.columns = excel_data.columns.str.strip()
    #print(excel_data.columns)

    # Llenar los valores faltantes con 0
    excel_data.fillna(0, inplace=True)

    # realizar todo el procedimiento por cada zona
    zonas_list = []
    for zona, data in excel_data.groupby('Zona'):        
        # calcular el año y mes maximos y minimos
        min_year = data['Año'].min()
        max_year = data['Año'].max()
        max_month = data.loc[data['Año']==max_year, 'Mes'].max()
        min_month = data.loc[data['Año']==max_year, 'Mes'].min()

        # Aplicar regla 2 de coberturas
        if parameters['regla_2'] == 'si':
            # La regla de coberturas se aplica a todos los clientes
            # que tengan mas de x meses sin ventas en aguasabor y aguavitam

            # Filtrar por las aguas
            product_filter = data['Producto'].isin(['Aguasabor', 'Agua Vitam'])
            filtered_df = data[product_filter]

            # Filtrar por el año mas reciente
            filtered_df = filtered_df[filtered_df['Año'] == max_year]

            # Identificar los x ultimos meses
            last_months = [max_month - i for i in range(int(parameters['Regla_2_var_X2']))]

            # para saber si hay un mes negativo
            for nm in last_months:
                if nm <= 0:
                    messagebox.showerror("Error","Número de meses seleccionado en la regla 2 es inválido")

            # Filtrar los datos por los ultimos dos meses
            filtered_df = filtered_df[filtered_df['Mes'].isin(last_months)]

            # Agrupar por 'Codigocliente' y 'Producto', y aplicar la funcion
            grouped = filtered_df.groupby(['Codigocliente', 'Producto']).filter(analysis_fun.has_zero_sales)

            # Obtener los 'Codigocliente'
            unique_clients_with_zero_sales = grouped['Codigocliente'].unique()
            #print(unique_clients_with_zero_sales)

        # Obtener la información única para clientes 
        customers = data.groupby('Codigocliente').agg({'Region': 'first',
                                                      'Gerencia':'first',
                                                      'Zona':'first', 
                                                      'Territorio':'first', 
                                                      'Barrio':'first'}).reset_index()
        # un bucle de 3 porque son 3 productos 
        # y variables los que se seleccionan        
        priority_scores = []
        for i in range(3):
            # extraer las variables
            product = parameters[f'product_{i+1}']
            variable = parameters[f'variable_{i+1}']
            weight = int(parameters[f'peso_{i+1}'][:2])/100

            # TODO: Realizar test de pruebas sobre las 
            # variables seleccionadas

            # Hacer analisis de la varible volumen
            if variable == 'Volumen':
                # computar primero el porcentaje de volumen
                # de venta de cada cliente para el producto del 
                # año y mes más reciente .. ojo que esto se puede
                # cambiar tambien para que tenga en cuenta mas de
                # un mes.
                vol_result = analysis_fun.compute_product_vol_weight(data, 
                                            product, 
                                            max_year, 
                                            max_month)

                
                # Ahora se calcula el ratio para el volumen de este producto seleccionado
                # este ratio ya se devuelve con los pesos para cada mes
                vol_ratio = analysis_fun.analysis_volumen_ratio(data, product, 
                                                    max_year, min_year, max_month)
                
                # Ahora calcular el riesgo final
                # 4. Ahora calcular el riesgo final .. 
                # falta reescalar
                final_vol_ratio = analysis_fun.compute_risk_way2(vol_ratio,
                                                        f'vol_{product}_ratio_weighted') 
                
                col2merge = ['Codigocliente', f'vol_{product}_weight']
                final_vol_ratio = final_vol_ratio.merge(vol_result[col2merge], 
                                    on='Codigocliente', how='left', validate='1:1')
                
                priority_score = final_vol_ratio[f'vol_{product}_ratio_weighted_risk'].values
                
                # finalmente multiplicar por el peso ingresado en la interfaz
                final_vol_ratio[f'vol_{product}_priority_score'] = priority_score*weight

                # almacenar el resultado
                maincols = ['Codigocliente', f'vol_{product}_priority_score', f'vol_{product}_weight']
                priority_scores.append(final_vol_ratio[maincols])


            elif variable == 'Market Share':
                # recordar que el producto seleccionado
                # para esta variable debe tener tambien datos
                # para volumen
                
                # se calcula diferente hay que encontrar el MK perdido
                # con el volumen del mes anterior
                # luego las cajas perdidas se multiplican por los pesos 
                # para darle mas importancia a lo reciente
                # finalmente se calcula un valor total de cajas
                # y luego se normaliza contra el que mas perdio
                # luego se multipla con el peso de la variable
                vol_result = analysis_fun.compute_product_vol_weight(data, 
                                                                product, 
                                                                max_year, 
                                                                max_month)
                

                # 3. Ahora calcular el ratio para la variable Market Share
                mk_ratio = analysis_fun.analysis_market_share_ratio(data, product, 
                                                        max_year, max_month)

                # 4. Ahora calcular el riesgo final .. pasar del vol de mk perdido a valor normalizado
                final_mk_ratio = analysis_fun.compute_risk_minmax(mk_ratio,
                                                        f'mk_{product}_ratio_weighted')  

                
                final_mk_ratio[f'mk_{product}_priority_score'] = final_mk_ratio[f'mk_{product}_ratio_weighted_risk']*weight
                
                maincols = ['Codigocliente', f'mk_{product}_priority_score']
                priority_scores.append(final_mk_ratio[maincols])


            elif variable == 'Revenue':
                # para el revenue si se puede aplicar para sacar el important factor
                # es decir aqui no se usa el vol
                rev_result = analysis_fun.compute_product_rev_weight(data, 
                                                                product, 
                                                                max_year, 
                                                                max_month)    

                # calcular el rev ratio
                rev_ratio = analysis_fun.analysis_revenue_ratio(data, product, 
                                                    max_year, min_year, max_month) 
                
                # calcular el riesgo
                final_rev_ratio = analysis_fun.compute_risk_way2(rev_ratio,
                                                        f'rev_{product}_ratio_weighted')
                

                col2merge = ['Codigocliente', f'rev_{product}_weight']
                final_rev_ratio = final_rev_ratio.merge(rev_result[col2merge], 
                                    on='Codigocliente', how='left', validate='1:1')
                
                priority_score = final_rev_ratio[f'rev_{product}_ratio_weighted_risk'].values


                final_rev_ratio[f'rev_{product}_priority_score'] = priority_score*weight
                maincols = ['Codigocliente',f'rev_{product}_priority_score', f'rev_{product}_weight']
                priority_scores.append(final_rev_ratio[maincols])
                #result_frames.append(final_rev_ratio)

                #print(final_rev_ratio)
                #print(final_rev_ratio.columns)

                    
            elif variable == 'Portfolio':
                # Calcula el ratio para el Portfolio de este producto seleccionado
                # este ratio tiene dos partes .. el score geo
                # y el score del analisis temporal
                # este ratio ya se devuelve con los pesos para cada mes
                porf_geo_ratio, porf_ratio = analysis_fun.analysis_portfolio_ratio(data, product, 
                                                    max_year, min_year, max_month) 

                # Ahora calcular el riesgo final
                final_porf_ratio = analysis_fun.compute_risk_way2(porf_ratio,
                                                            f'porf_{product}_ratio_weighted')   
                
                # ESTAS LINEAS SE COMENTAN PORQUE SON LOS QUE HACEN LA INTEGRACIÖN CON 
                # EL IMPORTANT FACTOR Y LA FUNCION DE PONDERACION
                # SE DECIDIO INHABILITAR ESTA SECCIÖN
                
                # important factor con base en el revenue
                #porf_result = analysis_fun.compute_important_porf_factor(data, product, 
                #                                    max_year, min_year, max_month)  

                # unir el analisis temporal con los grupos de diferencias temporales
                #final_porf_ratio = final_porf_ratio.merge(porf_result, 
                #                                        on='Codigocliente', how='left', validate='1:1') 
                
                # Ahora realizar la integracion del riesgo final con el grupo
                #final_porf_ratio[f'porf_{product}_ratio_weighted_risk'] = analysis_fun.fx_integration_IF(final_porf_ratio, 
                #                                                            risk_col_name=f'porf_{product}_ratio_weighted_risk', 
                #                                                            if_col_name=f'group')

                # Ahora calcular el priority score
                # como el promedio entre el geo score y el ratio temporal
                final_porf_ratio = pd.merge(final_porf_ratio, 
                                            porf_geo_ratio, 
                                            on='Codigocliente',
                                            how='left',
                                            validate='1:1')

                # Calcular el priority score
                final_porf_ratio[f'porf_{product}_priority_score'] = (final_porf_ratio['score'] + 
                                            final_porf_ratio[f'porf_{product}_ratio_weighted_risk']) / 2

                priority_score = final_porf_ratio[f'porf_{product}_priority_score']
                # finalmente multiplicar por el peso ingresado en la interfaz
                final_porf_ratio[f'porf_{product}_priority_score'] = priority_score*weight 
                    
                maincols = ['Codigocliente', f'porf_{product}_priority_score', 'cluster', 'new_cluster']
                priority_scores.append(final_porf_ratio[maincols])      


            elif variable == 'Mix Premium':
                # Calcula el ratio para el mix Premium de este producto seleccionado
                # este ratio tiene dos partes .. el score geo
                # y el score del analisis temporal
                # este ratio ya se devuelve con los pesos para cada mes
                mixp_geo_ratio, mixp_ratio = analysis_fun.analysis_mixpremium_ratio(data, product, 
                                                    max_year, min_year, max_month) 
                
                # Ahora calcular el riesgo final
                final_mixp_ratio = analysis_fun.compute_risk_way2(mixp_ratio,
                                                            f'mixp_{product}_ratio_weighted')    
                
                # Ahora calcular el priority score
                # como el promedio entre el geo score y el ratio temporal
                final_mixp_ratio = pd.merge(final_mixp_ratio, 
                                            mixp_geo_ratio, 
                                            on='Codigocliente',
                                            how='left',
                                            validate='1:1')
                
                # Calcular el priority score
                final_mixp_ratio[f'mixp_{product}_priority_score'] = (final_mixp_ratio['score'] + 
                                            final_mixp_ratio[f'mixp_{product}_ratio_weighted_risk']) / 2

                priority_score = final_mixp_ratio[f'mixp_{product}_priority_score']
                # finalmente multiplicar por el peso ingresado en la interfaz
                final_mixp_ratio[f'mixp_{product}_priority_score'] = priority_score*weight 
                    
                maincols = ['Codigocliente', f'mixp_{product}_priority_score']
                priority_scores.append(final_mixp_ratio[maincols])              

        
        # finalmente se unen todos los priorities scores en un solo dataframe
        for ind, df_res in enumerate(priority_scores):
            if ind == 0:
                final_df = df_res
            else:
                final_df = final_df.merge(df_res, 
                                        on='Codigocliente', 
                                        validate='1:1', 
                                        how='left')
                
        # se fija como indice el codigo del cliente
        final_df.set_index('Codigocliente', inplace=True)
        # se realiza la suma de todos los priorities scores 
        # como ya se encuentran ponderados solo es sumar
        final_df['total_score'] = final_df.sum(axis=1).values
        final_df.reset_index(inplace=True)

        ###
        # Inclusión de las variables categoricas como
        # nivel de digitalización entre otras
        score_name = 'total_score'
        if parameters['var_cat'] != 'Ninguna':
            # sacar los valores unicos de la subvariable
            var_cat = parameters['var_cat']
            var_subcat = parameters['var_subcat']
            unique_list = data[var_cat].unique()
            peso_cat = float(parameters['var_subcat_peso'].split(' ')[0])
            porcentaje_restante = 1.0 
            dict_subvar_cat = dict(zip(unique_list,[porcentaje_restante]*len(unique_list)))
            dict_subvar_cat[var_subcat] = peso_cat
            # hacer merge con la variable categorica
            unique_customers = data.groupby('Codigocliente').agg({var_cat: 'first'}).reset_index()
            final_df = final_df.merge(unique_customers[['Codigocliente', var_cat]], 
                                        on='Codigocliente', 
                                        validate='1:1', 
                                        how='left')
            
            # Calcular el maximo score y normalizar
            max_weighted_score = max(customer['total_score'] * dict_subvar_cat.get(customer[var_cat], 1.0)\
                                    for _, customer in final_df.iterrows())

            for ind, row in final_df.iterrows():
                final_df.loc[final_df.Codigocliente==row.Codigocliente, 
                            'total_score_weighted'] = (row.total_score * dict_subvar_cat[row[var_cat]])/max_weighted_score
            
            # actualizar el score name en el cual se van a hacer las asignaciones 
            score_name = 'total_score_weighted'
            if len(set([var_subcat.strip()]).difference(set(unique_list))) > 0:
                messagebox.showwarning("Error", 
                    f"Revisa la subvariable categórica, puede estar mal escrita. Todas las subvariables quedan con el mismo peso (1.0). Subavariables encontradas {unique_list} subvariable ingresada: {var_subcat}")
                

        # último paso es asignar las frecuencias 
        # sobre el score total
        #print(final_df)
        if parameters['regla_2'] == 'si':
            final_df = distribute_visits(final_df, 
                                    score_name = score_name, 
                                    parameters = parameters,
                                    codes_rule_2=unique_clients_with_zero_sales)
        else:
            final_df = distribute_visits(final_df, 
                                    score_name = score_name, 
                                    parameters = parameters,
                                    codes_rule_2=None)            

        if  type(final_df) == type(False):
            return False
        
        # añadir zona, barrio, territorio, comuna
        final_df = final_df.merge(customers[['Codigocliente', 'Region',
                                            'Gerencia','Zona', 'Territorio', 'Barrio']], 
                            on='Codigocliente', 
                            validate='1:1', 
                            how='left')
        
        
        zonas_list.append(final_df)
    
    result = pd.concat(zonas_list).reset_index(drop=True)
    try:
        result.drop(['cumsum'], inplace=True, axis=1)
    except:
        pass

    return result 


    
