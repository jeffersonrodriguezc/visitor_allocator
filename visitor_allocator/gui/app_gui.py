import os
#import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import pandas as pd
#from collections import defaultdict


from visitor_allocator.analysis.variable_analysis import run_analysis
#from analysis.variable_analysis import run_analysis
#import gui.utils as u
import visitor_allocator.gui.utils as u

def run_app():

    class MultiViewApp(tk.Tk):
        def __init__(self):
            tk.Tk.__init__(self)
            self.title("Orusexpert: Asignador de visitas")
            self.geometry("500x700")

            # Left Pane
            left_pane = tk.Frame(self, width=150, height=700, bg="lightgray")
            left_pane.pack(side=tk.LEFT, fill=tk.Y)

            # Logo
            logo_path = u.resource_path("assets/logo.png")
            #logo_path = os.getcwd()+"/assets/logo.png"
            logo_img = tk.PhotoImage(file=logo_path).subsample(5,5)  # Replace with your logo path
            logo_label = tk.Label(left_pane, image=logo_img, bg="lightgray")
            logo_label.image = logo_img
            logo_label.pack(pady=(10, 0))

            # Separator
            separator = ttk.Separator(left_pane, orient="horizontal")
            separator.pack(fill="x", pady=(10, 0))

            # Buttons
            start_button = tk.Button(left_pane, text="Inicio", command=self.show_view1)
            start_button.pack(pady=(20, 5))

            set_rules_button = tk.Button(left_pane, text="Fijar reglas", command=self.show_view2)
            set_rules_button.pack(pady=(5, 20))

            # Panel derecho
            self.right_pane = tk.Frame(self)
            self.right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Initializa all attibutes 
            self.initialize_attributes()

            # Inicializar la vista principal
            self.show_view1()

        def initialize_attributes(self):
            """
            Method to initialize attributes
            """
            # Inicializar las variables por defecto
            self.variables_for_view1 = {}
            # Crear la variable por defecto en el diccionario de variables
            self.variables_for_view1[f'product_1'] = "Aguasabor"
            self.variables_for_view1[f'product_2'] = "Aguasabor"
            self.variables_for_view1[f'product_3'] = "Alimentos"
            # Crear la variable por defecto en el diccionario de variables
            self.variables_for_view1[f'variable_1'] = "Volumen" 
            self.variables_for_view1[f'variable_2'] = "Market Share" 
            self.variables_for_view1[f'variable_3'] = "Revenue"
            # Crear la variable por defecto en el diccionario de variables
            self.variables_for_view1[f'peso_1'] = "40"
            self.variables_for_view1[f'peso_2'] = "30"
            self.variables_for_view1[f'peso_3'] = "30"

            # Crear las variables categoricas en el diccionario por defecto
            self.variables_for_view1[f'var_cat'] = "Nivel de digitalización"
            self.variables_for_view1[f'var_subcat'] = "Alta"
            self.variables_for_view1[f'var_subcat_peso'] = "1.5"

            # Crear la variable para la bolsa de visitas
            self.default_visitas = "500"
            self.variables_for_view1[f'total_visits_0'] = self.default_visitas

            # Crear variables por defecto para la segunda vista
            self.opciones = ['Semanal', 'Trisemanal','Quincenal', 'Mensual']
            self.variables_for_view1[f'Regla_1_var_X1'] = "Semanal"
            self.variables_for_view1[f'Regla_1_var_X2'] = "50"
            self.variables_for_view1[f'Regla_2_var_X1'] = "Semanal"
            self.variables_for_view1[f'Regla_2_var_X2'] = "2"
            self.variables_for_view1[f'Regla_3_var_X1'] = "1"
            self.variables_for_view1[f'Regla_3_var_X2'] = "4"
            self.variables_for_view1[f'regla_1'] = "no"
            self.variables_for_view1[f'regla_2'] = "no"
            self.variables_for_view1[f'regla_3'] = "no"

            # valores por defecto
            self.defaults_per = ["40", "30", "30"]
            self.defaults_var = ["Volumen","Market Share","Revenue"]
            self.defaults_pro = ["Aguasabor", "Aguasabor", "Alimentos"]
            self.defaults_cat = ["Nivel de digitalización"]
            self.defaults_subcat = ["Alta"]
            self.defaults_cat_w = ["1.5"]

            # Variable para verificar si ya se cargaron los datos
            self.data_loaded = False

            # Variable para verificar si ya se ejecuto un proceso
            self.process_executed = False
            
        def show_view1(self):
            self.clear_right_pane()

            # Upper Part
            upper_frame = tk.Frame(self.right_pane, width=350, height=550)
            upper_frame.pack_propagate(False)
            upper_frame.pack()

            # Title "Variables"
            tk.Label(upper_frame, 
                     text="Productos - Variables - Pesos", 
                     font=("Helvetica", 16)).pack(pady=(15, 0), anchor="w")

            # crear función de validación
            validate_cmd = upper_frame.register(u.validate_input_percent)
            # Select Boxes, Text Boxes, and Labels
            for indx in range(3):
                ### Caja para seleccionar producto
                product_box = ttk.Combobox(upper_frame, 
                                           values=["Aguasabor", "Agua Vitam", "Alimentos"],)
                product_box.pack(anchor="w") 
                # fijar el valor inicial o el ultimo seleccionado
                product_box.set(self.variables_for_view1[f'product_{indx + 1}'])
                # Definir función para actualización del select
                product_box.bind("<<ComboboxSelected>>", 
                                 lambda event, 
                                 index=indx+1, 
                                 box=product_box: self.update_variable(event, index, 'product_', box))
                
                #### Caja para seleccionar variable
                select_box = ttk.Combobox(upper_frame, 
                                          values=["Volumen", "Market Share", "Revenue",
                                                   "Portfolio", "Mix Premium"])
                select_box.pack(anchor="w")
                # fijar valor por defecto en la caja de texto
                # Definir función para actualización del select
                select_box.set(self.variables_for_view1[f'variable_{indx + 1}'])
                select_box.bind("<<ComboboxSelected>>", 
                                lambda event, 
                                index=indx+1, 
                                box=select_box: self.update_variable(event, index, 'variable_', box))

                #### Caja para ingresar peso
                text_box = tk.Entry(upper_frame, 
                                    width=5, validate='key',
                                    validatecommand=(validate_cmd, "%P"))
                text_box.pack(anchor="w", pady=(0,20))
                # Definir función para actualización de la caja de texto
                text_box.insert(0, self.variables_for_view1[f'peso_{indx + 1}'])
                text_box.bind("<FocusOut>", 
                              lambda event, 
                              index=indx+1, 
                              box=text_box: self.update_variable(event, index, 'peso_', box))
            
            # Variables categoricas
            tk.Label(upper_frame, text="Variables Categóricas", 
                     font=("Helvetica", 14)).pack(pady=(10, 0), anchor="w")

            ### Seleccionar la varible categorica deseada
            select_catbox = ttk.Combobox(upper_frame, 
                                          values=["Nivel de digitalización", "Subcanal", "Ninguna"])
            select_catbox.pack(anchor="w")
            select_catbox.set(self.variables_for_view1[f'var_cat'])
            select_catbox.bind("<<ComboboxSelected>>", 
                                lambda event, 
                                index='', 
                                box=select_catbox: self.update_variable(event, index, 'var_cat', box))

            # Label para escribir el valor de la variable a poner mas atención
            label = tk.Label(upper_frame, text="Subvalor principal y peso:")
            label.pack( pady=(10,0), anchor="w")

            # Nombre de la variable a poner mas atención
            cat_value_entry = tk.Entry(upper_frame, width=10)
            cat_value_entry.pack(pady=(0,0), anchor="w")
            cat_value_entry.insert(0, self.variables_for_view1[f'var_subcat'])
            cat_value_entry.bind("<FocusOut>", 
                              lambda event, 
                              index='', 
                              box=cat_value_entry: self.update_variable(event, index, 'var_subcat', box))

            # Peso de la variable, recuerde que el resto de variables 
            # tendran el mismo peso restante
            validate_cmd_3 = upper_frame.register(u.validate_input_float_range)
            cat_weight_entry = tk.Entry(upper_frame, width=5,
                                        validate='key',
                                        validatecommand=(validate_cmd_3, "%P"))
            cat_weight_entry.pack(pady=(0,0), anchor="w")
            cat_weight_entry.insert(0, self.variables_for_view1[f'var_subcat_peso'])
            cat_weight_entry.bind("<FocusOut>", 
                              lambda event, 
                              index='', 
                              box=cat_weight_entry: self.update_variable(event, index, 'var_subcat_peso', box))

            ###############################################
            # Visits Bag Title
            tk.Label(upper_frame, text="Bolsa de Visitas", 
                     font=("Helvetica", 14)).pack(pady=(15, 0), anchor="w")

            # Monthly Visits Subtitle
            tk.Label(upper_frame, text="Visitas totales").pack(pady=(0, 0), 
                                                               padx=0, anchor="w",
                                                               )
            validate_cmd_2 = upper_frame.register(u.validate_input_positive)
            text_input_visits = tk.Entry(upper_frame, width=5,
                                        validate='key',
                                        validatecommand=(validate_cmd_2, "%P"))
            text_input_visits.pack(pady=(0, 0), padx=0, anchor="w", )
            text_input_visits.insert(0, self.variables_for_view1[f'total_visits_0'])
            text_input_visits.bind("<FocusOut>", 
                                   lambda event, 
                                   index=0, 
                                   box=text_input_visits: self.update_variable(event, index, 'total_visits_', box))

            #tk.Button(upper_frame, text="Guardar").pack(pady=(10, 0), padx=15, anchor="w")
            
            # Horizontal Divider
            ttk.Separator(self.right_pane, orient="horizontal").pack(fill="x", pady=(10,10))

            # Bottom Part
            bottom_frame = tk.Frame(self.right_pane, width=350, height=350)
            bottom_frame.pack_propagate(False)
            bottom_frame.pack(side=tk.BOTTOM)

            # Buttons in View 1
            load_data_button = tk.Button(bottom_frame, text="Cargar datos", command=self.load_data)
            load_data_button.pack(side=tk.LEFT, padx=10)

            execute_button = tk.Button(bottom_frame, text="Ejecutar", command=self.execute_procedure)
            execute_button.pack(side=tk.LEFT, padx=10)

            download_button = tk.Button(bottom_frame, text="Resultados", command=self.download_results)
            download_button.pack(side=tk.LEFT, padx=10)

            restart_button = tk.Button(bottom_frame, text="Restaurar", command=self.restart)
            restart_button.pack(side=tk.LEFT, padx=10)

        def show_view2(self):
            self.clear_right_pane()

            # Title
            tk.Label(self.right_pane, 
                     text="Configuración de reglas", 
                     font=("Helvetica", 16)).pack(pady=(10, 0))

            # Tab Control
            tab_control = ttk.Notebook(self.right_pane)
            tab_control.pack(expand=True, fill=tk.BOTH)

            reglas_definiciones = ["Def: Visita 'X1' para los clientes que generan el 'X2' del volumen total.",
                                   "Def: Visita 'X1' para los clientes que tienen 'X2' meses sin cobertura en aguas.",
                                   "Def: Todos los clientes deben tener minimo 'X1' visita al mes, y un cliente no puede exceder 'X2' visitas al mes."]

            # Rule Tabs
            for rule_number in range(1, 4):
                tab = ttk.Frame(tab_control)
                tab_control.add(tab, text=f"Regla {rule_number}")
                validate_cmd = tab.register(u.validate_input_percent)
                validate_cmd_2 = tab.register(u.validate_input_number_days)

                # Sentence
                lenght = int(len(reglas_definiciones[rule_number-1])/2)
                tk.Label(tab, 
                         text=reglas_definiciones[rule_number-1][:lenght]).pack(pady=0)
                tk.Label(tab, 
                         text=reglas_definiciones[rule_number-1][lenght:]).pack(pady=0)

                # Select Box and Text Inputs
                for label_text in ["X1", "X2"]:
                    if label_text == 'X1' and rule_number in [1,2]:
                        tk.Label(tab, text=label_text+':').pack(pady=(15,0), padx=10, anchor="w")
                        freq_box = ttk.Combobox(tab, values=self.opciones)
                        freq_box.pack(padx=10, anchor="w")
                        freq_box.set(self.variables_for_view1[f'Regla_{rule_number}_var_{label_text}'])
                        # Definir función para actualización del select
                        freq_box.bind("<<ComboboxSelected>>", 
                                lambda event, 
                                index=(rule_number,label_text), 
                                box=freq_box: self.update_variable_view2(event, index, 'Regla_{}_var_{}', box))
                        #tk.Entry(tab).pack(padx=10)

                    elif label_text == 'X2' and rule_number==1:
                        tk.Label(tab, text=label_text+':').pack(pady=(15,0), padx=10, anchor="w")
                        text_vol_total = tk.Entry(tab, width=5, validate='key',
                                                  validatecommand=(validate_cmd, "%P"))
                        text_vol_total.pack(padx=10, anchor="w")
                        text_vol_total.insert(0, self.variables_for_view1[f'Regla_{rule_number}_var_{label_text}'])
                        text_vol_total.bind("<Leave>", 
                                   lambda event, 
                                   index=(rule_number,label_text), 
                                   box=text_vol_total: self.update_variable_view2(event, index, 'Regla_{}_var_{}', box))



                    elif label_text == 'X2' and rule_number==2:
                        tk.Label(tab, text=label_text+':').pack(pady=(15,0), padx=10, anchor="w")
                        text_meses = tk.Entry(tab, width=5)
                        text_meses.pack(padx=10, anchor="w")
                        text_meses.insert(0, self.variables_for_view1[f'Regla_{rule_number}_var_{label_text}'])  
                        text_meses.bind("<Leave>", 
                                   lambda event, 
                                   index=(rule_number,label_text), 
                                   box=text_meses: self.update_variable_view2(event, index, 'Regla_{}_var_{}', box))

                    elif label_text == 'X1' and rule_number==3: 
                        tk.Label(tab, text=label_text+':').pack(pady=(15,0), padx=10, anchor="w")
                        text_min_vis = tk.Entry(tab, width=5,
                                                validate='key',
                                                validatecommand=(validate_cmd_2, "%P"))
                        text_min_vis.pack(padx=10, anchor="w")  
                        text_min_vis.insert(0, self.variables_for_view1[f'Regla_{rule_number}_var_{label_text}'])
                        text_min_vis.bind("<Leave>", 
                                   lambda event, 
                                   index=(rule_number,label_text), 
                                   box=text_min_vis: self.update_variable_view2(event, index, 'Regla_{}_var_{}', box))                      

                    elif label_text == 'X2' and rule_number==3: 
                        tk.Label(tab, text=label_text+':').pack(pady=(15,0), padx=10, anchor="w")
                        text_max_vis = tk.Entry(tab, width=5,
                                                validate='key',
                                                validatecommand=(validate_cmd_2, "%P"))
                        text_max_vis.pack(padx=10, anchor="w") 
                        text_max_vis.insert(0, self.variables_for_view1[f'Regla_{rule_number}_var_{label_text}'])
                        text_max_vis.bind("<Leave>", 
                                   lambda event, 
                                   index=(rule_number,label_text), 
                                   box=text_max_vis: self.update_variable_view2(event, index, 'Regla_{}_var_{}', box))                                               
                    
                # Radio Buttons
                # crear radio button en una funcion para que se puedan actualizar todos 
                self.create_radio_button(tab, rule_number)


        def clear_right_pane(self):
            for widget in self.right_pane.winfo_children():
                widget.destroy()

        def load_data(self):
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                try:
                    data = pd.read_excel(file_path)
                    # Process data as needed
                    self.data = data
                    self.data_loaded = True
                    messagebox.showinfo("Success", "Datos cargados correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error cargando datos: {str(e)}")

        def execute_procedure(self):
            # Placeholder for execute procedure functionality
            # hacer check de que se hayan cargado los datos

            # La primera valiadación que debo hacer es que hayan datos
            if self.data_loaded==False:
                    tk.messagebox.showwarning("No hay datos cargados", 
                        "Por favor lea un archivo excel antes de ejecutar el análisis.")
            else:
                flag = True
                # primero hacer validaciones
                validacion_sum = int(self.variables_for_view1['peso_1']) + \
                                int(self.variables_for_view1['peso_2']) + \
                                int(self.variables_for_view1['peso_3'])
                
                if validacion_sum != 100:
                    flag = False
                    messagebox.showerror("Input inválido", 
                    "La suma de los pesos debe ser igual a 100. Cambie la distribución de pesos antes de continuar.")

                if flag:
                    try:
                        self.analysis_result = run_analysis(self.data, self.variables_for_view1)
                        if type(self.analysis_result) == type(False):
                            messagebox.showerror("Error", f"Ajuste adecuadamente la regla 1, bolsa de visitas no es suficiente para cubrir el {self.variables_for_view1['Regla_1_var_X2']}% de clientes con mayor importancia.")
                        else:
                            self.process_executed = True
                            messagebox.showinfo("Success", "Ejecución finalizada")
                    except Exception as e:
                            messagebox.showerror("Error", f"No se han cargado datos: {str(e)}")

        def download_results(self):
            if self.process_executed:
                file = filedialog.asksaveasfilename(defaultextension=".xlsx")
                try:
                    self.analysis_result.to_excel(str(file), index=False)
                    messagebox.showinfo("Success", f"Datos almacenados en: {file}")
                except Exception as e:
                        messagebox.showerror("Error", f"No se ha podido almacenar: {str(e)}")
            else:
                tk.messagebox.showwarning("No hay análisis ejecutados", 
                        "Por favor ejecute el análisis")
                
        def restart(self):
            """
            """
            # re initialize attributes
            #self.initialize_attributes()
            self.process_executed = False
            self.data_loaded = False
            del self.data
            del self.analysis_result

            messagebox.showinfo("Success", f"Valores por defecto. Ahora es posible cargar nuevamente datos.")


        def update_variable(self, event, index, key, widget):
            value = widget.get()
            self.variables_for_view1[f'{key}{index}'] = value
            #self.print_variables()

        def update_variable_view2(self, event, index, key, widget):
            value = widget.get()
            self.variables_for_view1[key.format(index[0],index[1])] = value
            #self.print_variables()

        def on_radio_select(self, index, key, widget):
            value = widget.get()
            self.variables_for_view1[f'{key}{index}'] = value
            #self.print_variables()

        def print_variables(self):
            print("Current Variables:")
            for key, value in self.variables_for_view1.items():
                print(f"{key}: {value}")

        def create_radio_button(self, tab, rule_number):
            use_rule_var = tk.StringVar()
            use_rule_var.set(self.variables_for_view1[f'regla_{rule_number}'])
            tk.Label(tab, text="Usar regla?").pack(anchor="w", pady=(15,0))
            radio_button = tk.Radiobutton(tab, 
                                        text="Si", 
                                        variable=use_rule_var, 
                                        value="si",
                                        command=lambda index=rule_number, key='regla_': self.on_radio_select(index, key, use_rule_var))
            radio_button.pack(anchor="w")

            radio_button = tk.Radiobutton(tab, 
                                        text="No", 
                                        variable=use_rule_var, 
                                        value="no",
                                        command=lambda index=rule_number, key='regla_': self.on_radio_select(index, key, use_rule_var))
            radio_button.pack(anchor="w")


    app = MultiViewApp()
    app.mainloop()
    
