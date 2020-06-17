# Libreria para realizar analisis de datos, y crear datos estructurados
import pandas as pd
# Libreria para trabajar con expresiones regulares de texto
import re
# Framework y libreria para trabajar con graficos y imagenes
from matplotlib import pyplot as plt
from math import *
from numpy import *
#import seaborn as sns



#primera función de filtro inicial, pone cabeceras y elimina las que no son de utilidad para el modelo
def first_filter(df):
    # esta funcion ingresa las cabeceras del dataframe
    df.columns = ['Fecha/Hora','Consecutivo','Trama','Red','Nombre_estacion','Metodologia','Puerto_serial','Descriptor_campo','Ventilador','CO2_PPM_SUPERIOR',
                  'TEM_CO2_SUPERIOR','Vol_CO2_lamp_superior','CO2_PPM_INFERIOR','TEM_CO2_INFERIOR','Vol_CO2_lamp_inferior','Flujo','Contador_Radon','U_vol_k1','C1_TEMPERATURA','U_vol_k2',
                  'C2_TEMPERATURA','U_vol_k3','Temp_k3','U_vol_k4','Temp_k5','TEMPERATURA_EXT','Vol_tmp','TEMPERATURA_INT','Check_sum','Final']


    # en esta parte se eliminan las columnas del dataframe que no se van a utilizar
    del df['Check_sum']
    del df['Final']
    del df['Vol_tmp']
    del df['TEMPERATURA_INT']
    del df['Temp_k5']
    del df['U_vol_k4']
    del df['Temp_k3']
    del df['U_vol_k3']
    del df['C2_TEMPERATURA']
    del df['U_vol_k2']
    del df['C1_TEMPERATURA']
    del df['U_vol_k1']
    del df['Vol_CO2_lamp_superior']
    del df['Vol_CO2_lamp_inferior']
    del df['Contador_Radon']
    del df['Flujo']

    # en esta parte se eliminan las filas del dataframe que tienen datos iguales a 0, los cuales no sirven para el estudio
    df = df[df['CO2_PPM_SUPERIOR'] != 0]
    df = df[df['CO2_PPM_INFERIOR'] != 0]

    return df

# funcion para multiplicar todos los datos por los factores que se especifican en el geodata
def mp_factors (df):
    # esta parte convierte la columna de texto a numero
    df['TEM_CO2_INFERIOR'] = pd.to_numeric(df['TEM_CO2_INFERIOR'])

    df['CO2_PPM_SUPERIOR'] = df['CO2_PPM_SUPERIOR']/10# = Ca_ppm
    df['CO2_PPM_INFERIOR'] = df['CO2_PPM_INFERIOR']/10# = Cb_ppm

    df['TEM_CO2_SUPERIOR'] = df['TEM_CO2_SUPERIOR']/10# = T_sup
    df['TEM_CO2_INFERIOR'] = df['TEM_CO2_INFERIOR']/10# = T_inf
    df['TEMPERATURA_EXT'] = df['TEMPERATURA_EXT']/100# = T_ext

    return df
# funcion para calcular todos los parametros y variables necesarias para sacar la solucion lineal
#def calculate_params(df, p_atm, Ca_ref, Cb_ref):
def calculate_params(df, df_atm):#"""<--- aquí cambié -es lo de arriba-, 31/03/2020 17:08"""

    #df['Presion_atmos'] = df_atm['Presion_atm']

    # esta parte saca los promedios de temperatura de los sensores superiores e inferiores, la funcion round, redondea el promedio a un decimal
    t_sup_mean = round(pd.Series.mean(df['TEM_CO2_SUPERIOR']), 3)
    t_inf_mean = round(pd.Series.mean(df['TEM_CO2_INFERIOR']), 3)

    #constantes necesarias para el calculo de la solucion lineal
    D_stp = 1.39*(10**-5)  #(m^2/s)
    MW = 44.01   #(g/mol)
    R = 8.3157   #(m^3*Pa)/(K*mol)
    P_atm = 636 #corresponde a la presion absoluta por tabla de la altura altitud: 3774#was commented 31/03/2020 20:07
    #Ca_ref = ((404*P_atm)/1013)*(298/(273.2+t_sup_mean))#was commented 31/03 20:09#vuelve a comentarse 29/04/2020

    #---------Valor de referencia 5.2 utilizando las vigencias del trabajo en campo
    Ca_ref = 87.6 #73.5#estaba comentado hasta el: 29/04/2020 #se cambia el valor por el menor de los CO2_PPM_SUPERIOR
    Ta_ref = 23.7#temperatura de referencia para el sensor superior
    #Cb_ref = ((404*P_atm)/1013)*(298/(273.2+t_inf_mean))
    Za = -0.03333
    f_convert = (MW*1000)/(86400)

    # Aqui se realizan todos lso calculos necesarios para tener el flujo en la solucion lineal, las ecuaciones estan en el archivo word, orden de ecuaciones.........

    #df['D_lineal'] = D_stp*(((273.2+(df['TEM_CO2_SUPERIOR']+df['TEM_CO2_INFERIOR'])/2)/273.2)**(1.75*(1013/P_atm)))
    ######Creo que la ecuación de arriba está mal. La corrigo a continuación:
    df['suma media de tem'] = (df['TEM_CO2_SUPERIOR'] + df['TEMPERATURA_EXT']) / 2
    df['elevado 1.75'] = ((273.2 + df['suma media de tem']) / 273.2) ** 1.75
    df['mul_D_stp'] = D_stp * df['elevado 1.75']
    df['D_lineal'] = df['mul_D_stp'] * (1013 / P_atm)
    ######
    #df['D_lineal'] = D_stp*(((273.2+df['TEM_CO2_SUPERIOR'])/273.2)**(1.75*(1013/P_atm)))
    df['Ca_1'] =round((P_atm*MW*df['CO2_PPM_SUPERIOR']*0.1)/(R*(df['TEM_CO2_SUPERIOR']+273.2)),5)
    #df['Co'] =round((P_atm*MW*((Ca_ref+Cb_ref)/2)*0.1)/(R*(df['TEMPERATURA_EXT']+273.2)),2)
    #####df['Cao'] =round((P_atm*MW*((Ca_ref)/1)*0.1)/(R*(Ta_ref+273.2)),3)
    Cao = round((P_atm*MW*Ca_ref*0.1)/(R*(Ta_ref+273.2)),5)
    #####df['J_lineal'] = -df['D_lineal']*(df['Ca_1']-df['Cao'])/Za
    df['J_lineal'] = -(df['D_lineal'])*((df['Ca_1'] - Cao)/Za)
    #df['J_lineal'] = round((df['J_lineal']*f_convert),3)

    # esta funcion calcula el promedio del flujo en la solucion lineal
    J_mean = round(pd.Series.mean(df['J_lineal']), 5)
    df['J_lineal_est'] = round((df['J_lineal'])*1.99, 5)

#######Se agregarán las fórmulas para tener dos gráficas más: una donde se varía solo la Presión y se tiene pero se usa t_sup_mean; y otra donde se varía la temperatura, pero se deja la P_atm_media. Para esta presión media se utiliza el documento descargado de la estación meteorológica de Cocuy4. Se utiliza la ecuación 3 del documento "Orden de las ecuaciones..."

    ####Compensación de la temperatura -> se usa la media de la Presión atmosférica, con la ayuda del archivo que se exportó de la estación meteorológica de Cocuy4 y el dataframe creado con su columna:
    P_atm_media = round(pd.Series.mean(df_atm['Presion']), 5)
    df['Ca_compT'] = round((P_atm_media * MW * df['CO2_PPM_SUPERIOR'] * 0.1) / (R * (df['TEM_CO2_SUPERIOR'] + 273.2)), 5)
    ####Compensación de la presión -> se usa la media de la teperatura superior:
    df['Ca_compP'] = round((df_atm['Presion'] * MW * df['CO2_PPM_SUPERIOR'] * 0.1) / (R * (t_sup_mean + 273.2)), 5)
    #####Con la variación de la temperatura y la presión:
    df['Ca'] = round((df_atm['Presion'] * MW * df['CO2_PPM_SUPERIOR'] * 0.1) / (R * (df['TEM_CO2_SUPERIOR'] + 273.2)), 5)

    return df, J_mean

    ############29/04/2020: Una nueva función solo para que calcule el promedio del flujo en la solución lineal, y lo quito de la función calculate_params:
def J_lineal_medio(df):
    f_medio = round(pd.Series.mean(df['J_lineal']),5)
    return f_medio

# esta funcion corrige una corrupcion de los datos en la temperatura del sensor inferior
def data_solutions (df):
    #condicional para verificar que hay datos corruptos que convierten la columna en tipo objecto
    if df['Fecha/Hora'].dtypes == df['TEM_CO2_INFERIOR'].dtypes:
        # creo una columna llamada bool donde los valores que estan en false son los datos corruptos
        df.loc[df['TEM_CO2_INFERIOR'].str.len() != 4, 'bool'] = False
        # si hay un dato falso en bool, ingresa al loop
        if False in df['bool']:
            #recorro todas las filas del dataframe y reemplazo el valor corrupto por el real
            for i in df.index:
                df.at[i, 'TEM_CO2_INFERIOR'] = df['TEM_CO2_INFERIOR'].loc[i][:4] if df['bool'][i] == False else df['TEM_CO2_INFERIOR'].loc[i]
            # elimino la columna bool
            del df['bool']

    return df
#funcion para eliminar datos corruptos por reinicio del dispositivo
def info_device_filter (df):
    #convierto el primer dato del dataframe en string
    date = str(df['Fecha/Hora'][0])
    #verifico que la fecha exista por problema de datos de fecha faltantes en algunos archivos
    if len(date) == 21:
        #creo el patron de la expresion regular para buscarlo en el dataframe
        pattern = re.compile(r'^([0-2][0-9]|3[0-1])(\/|-)(0[1-9]|1[0-2])\2(\d{4})(\s)([0-2][0-9]):([0-5][0-9]):([0-5][0-9])(\s)([S])$')
        #evaluo si en la columna Fecha/Hora existe el patron, si no existe manda falso, y se guarda en una columna llamada bool
        df['bool'] = df['Fecha/Hora'].str.contains(pattern)
        # guardo todos los valores que hayan dado verdadero en la columna bool
        df = df[df['bool'] == True]
        #elimino la columna bool
        del df['bool']
    else:
        #que me guarde todos los datos donde el caracter es 1, asi elimino la informacion del reboot
        df = df[df['Fecha/Hora'].str.len() == 1]
    return df
#funcion para verificar que la fecha de entrada si tiene el formato correcto
def ver_date(date):
    #creo el patron de strings para leer correctamente la fecha
    pattern = re.compile(r'^([0-2][0-9]|3[0-1])(-)(0[1-9]|1[0-2])\2(\d{4})$')
    #hago un bucle infinito que solo terminara al entrar a un break
    while True:
        #evaluo si el dato de entrada del usuario concuerda con el patron de la expresion regular
        match = re.search(pattern, date)
        # si concuerda, se sale del blucle infinito
        if match:
            break
        #si no concuerda, vuelve a pedir el datos, hasta que tenga el formato correcto
        else:
            #aqui pido el dato del usuario
            print("Ingrese una fecha correcta (dd-mm-yyyy)")
            date = input()
    return date
#funcion que le pide al usuario todos los datos de entrada, fecha de evaluacion y parametros necesarios
def inputs_params():

    print("Fecha de inicio para la carga de datos (dd-mm-yyyy): ")
    d_i = input()
    #hago el llamado a la funcion ver_date para verificar el formato del dato fecha
    d_if = ver_date(d_i)

    print("Fecha de finalización para la carga de datos (dd-mm-yyyy): ")
    d_e = input()
    d_ef = ver_date(d_e)

    print("Digite el valor de la presión atmosférica: ")
    p_atm = float(input())

    print("Digite el valor de referencia para el sensor superior: ")
    Ca_ref = float(input())

    print("Digite el valor de referencia para el sensor inferior: ")
    Cb_ref = float(input())

    print("Digite el valor del tao de subida [min]: ")
    tao_up = int(input())

    print("Digite el valor del tao de bajada [min]: ")
    tao_down = int(input())

    #esta funcion retorna multiples parametros
    return d_if, d_ef, p_atm, Ca_ref, Cb_ref, tao_up, tao_down

#funcion que debe de leer todos los dias que el usuario desee
def lecture(date_ini, date_end):

    year = {'01':31, '02':28, '03':31, '04':30, '05':31, '06':30, '07':31, '08':31, '09':30, '10':31, '11':30, '12':31}
    df = pd.DataFrame()
    print(df)

    for i in range(int(date_ini[3:5]),int(date_end[3:5])+1):

        if date_ini[3:5] == date_end[3:5]:
            for j in range(int(date_ini[0:2]),int(date_end[0:2])+1):
                df_i = pd.read_csv('./raw_files_piñuelas_2020/FD_PINUEL_TMP38_2020'+date_ini[3:5]+'dfweg'+'.raw', header=None, error_bad_lines=False, engine='python')


        #for j in range(year['0'+str(i)]+1):
    return df
#funcion para graficar los datos del dataframe
#def graphs_J_lineal(df, date_ini, date_end, J_lineal_mean):
def graphs_J_lineal(df, df_atm):# """ <-- aquí cambié 31/03/2020 17:04"""

    #conjunto de funciones para guardar la grafica de los ppm sup e inf
    gf_1 = df.plot(x = "Fecha/Hora", y = ["CO2_PPM_SUPERIOR", "CO2_PPM_INFERIOR"])
    gf_1.set_xlabel("Tiempo [s]")
    gf_1.set_ylabel("Concentración [PPM]")
    plt.title('Concentración de CO2')
    #plt.text(40, 0.5, "texto 1", fontsize = 20)
    plt.xticks(rotation = 25)

    ######
    ####Colores para las lineas
    #gf_1.xaxis.label.set_color('red')
    #gf_1.tick_params(axis = 'x', colors = 'red')
    #plt.legend('Ca_1', 'Cb')
    ######
    #gf_1.subtitle('no sé D:', fontsize = 10, fontweight = 'bold')
    #plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+'Concentracion.png') esto no ibaen coment 18:27 31/03/2020
    plt.savefig('./Gráficas/Concentracion.png')

    #conjunto de funciones para guardar la grafica del flujo usando la solucion lineal
    #aqui tienes que buscar como configurar el texto del titulo y mostrar en el el flujo promedio de la semana o del rango de tiempo que pide el usuario

##### esto se lo agrego para el flujo medio:

    flujo_medio = round(J_lineal_medio(df), 5)
    #flujo_medio_est = round((flujo_medio * 1.999), 3)
    flujo_medio = str(flujo_medio)
    #flujo_medio_est = str(flujo_medio_est)
    gf_2 = df.plot(x = "Fecha/Hora", y = ["J_lineal"])
    gf_2.set_xlabel("Tiempo")
    gf_2.set_ylabel("Flujo [mol/m^2*dia]")
    plt.xticks(rotation = 25)

    plt.title('Flujo de CO2 lineal\n\n *Flujo_prom = ' + flujo_medio + ' [mol/m^2*día]')
    #plt.show()
    #plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+' Flujo_lineal.png') esto lo puse en coment: 18:22 31/03/2020
    plt.savefig('./Gráficas/Flujo_lineal.png')
    #########################################################

    ###############Gráfica para el flujo medio estimado:
    flujo_medio = round(J_lineal_medio(df), 5)
    flujo_medio_est = round((flujo_medio * 1.999), 5)
    flujo_medio = str(flujo_medio)
    flujo_medio_est = str(flujo_medio_est)
    gf_4 = df.plot(x = "Fecha/Hora", y = ["J_lineal_est"])
    gf_4.set_xlabel("Tiempo [s]")
    gf_4.set_ylabel("Flujo [mol/m^2*dia]")
    plt.xticks(rotation = 25)
    plt.title('Flujo de CO2 lineal estimado \n\ne = 1.99\n *Flujo_prom_est = Flujo_prom * e = ' + flujo_medio_est + ' [mol/m^2*día]')
    #plt.show()
    #plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+' Flujo_lineal.png') esto lo puse en coment: 18:22 31/03/2020
    plt.savefig('./Gráficas/Flujo_lineal_estimado.png')
    ###################################################

    ####################30/04/2020 - Nueva gráfica, con la Compensaciónde la temperatura:
    gf_3 = df.plot(x = "Fecha/Hora", y = ["Ca_compT", "Ca_compP", 'Ca'])
    gf_3.set_xlabel("Tiempo [s]")
    gf_3.set_ylabel("Concentración [mg/m^3]")
    plt.xticks(rotation = 25)
    plt.title('Concentración de CO2 con compensación')
    plt.savefig('./Gráficas/Concentracion compensada.png')
    ###################################

    ####################gráfica para la presión
    gf_5 = df_atm.plot(x = "Fecha", y = ['Presion'])
    gf_5.set_xlabel("Tiempo [s]")
    gf_5.set_ylabel("Presión atmosférica [hPas]")
    plt.xticks(rotation = 25)
    plt.title('Presión atmosférica')
    plt.savefig('./Gráficas/Presión atmosférica.png')
    ###################################

    ####################gráfica para la presión
    gf_5 = df.plot(x = "Fecha/Hora", y = ['TEM_CO2_SUPERIOR'])
    gf_5.set_xlabel("Tiempo [s]")
    gf_5.set_ylabel("Temperatura [°C]")
    plt.xticks(rotation = 25)
    plt.title('Temperatura')
    plt.savefig('./Gráficas/Temperatura.png')
    ###################################
#funcion main que tiene todas las funciones anteriores
def main():
    #Parametros de entrada
    d_if, d_ef, p_atm, Ca_ref, Cb_ref, tao_up, tao_down = inputs_params()

    #Lectura del data frame
    df = lecture(d_if, d_ef)

    #Filtrado y limpieza de datos
    df = first_filter(df)
    df = info_device_filter(df)
    df = data_solutions(df)

    # Solución modelo lineal
    df = mp_factors(df)
    #df, J_lineal_mean = calculate_params(df, p_atm, Ca_ref, Cb_ref)
    df
    J_lineal_mean = calculate_params(df)#"""<-- estaba lo que está en el renglón 215"""

    #Gráficas
    #graphs_J_lineal(df, date_ini, date_end, J_lineal_mean)
    graphs_J_lineal(df)#"""<-- aquí también cambie y estaba lo de la linea 219"""

    return df
