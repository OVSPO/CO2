# Libreria para realizar analisis de datos, y crear datos estructurados
import pandas as pd
# Libreria para trabajar con expresiones regulares de texto
import re
# Framework y libreria para trabajar con graficos y imagenes
from matplotlib import pyplot as plt

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
def calculate_params(df):#"""<--- aquí cambié -es lo de arriba-, 31/03/2020 17:08"""


    # esta parte saca los promedios de temperatura de los sensores superiores e inferiores, la funcion round, redondea el promedio a un decimal
    t_sup_mean = round(pd.Series.mean(df['TEM_CO2_SUPERIOR']), 1)
    t_inf_mean = round(pd.Series.mean(df['TEM_CO2_INFERIOR']), 1)

    #constantes necesarias para el calculo de la solucion lineal
    DSTP = 1.39*10**-5
    MW = 44.01
    R = 8.3157
    P_atm = 635 #corresponde a la presion absoluta por tabla de la altura altitud: 3774#was commented 31/03/2020 20:07
    Ca_ref = ((404*P_atm)/1013)*(298/(273.2+t_sup_mean))#was commented 31/03 20:09

    #---------Valor de referencia 5.2 utilizando las vigencias del trabajo en campo
    #Ca_ref = 5.2
    #Cb_ref = ((404*P_atm)/1013)*(298/(273.2+t_inf_mean))
    Za = -0.03333
    f_convert = (MW*1000)/(86400)

    # Aqui se realizan todos lso calculos necesarios para tener el flujo en la solucion lineal, las ecuaciones estan en el archivo word, orden de ecuaciones.........

    #df['D_lineal'] = DSTP*(((273.2+(df['TEM_CO2_SUPERIOR']+df['TEM_CO2_INFERIOR'])/2)/273.2)**(1.75*(1013/P_atm)))
    df['D_lineal'] = DSTP*(((273.2+df['TEM_CO2_SUPERIOR'])/273.2)**(1.75*(1013/P_atm)))
    df['Ca'] =round((P_atm*MW*df['CO2_PPM_SUPERIOR']*0.1)/(R*(df['TEM_CO2_SUPERIOR']+273.2)),2)
    #df['Co'] =round((P_atm*MW*((Ca_ref+Cb_ref)/2)*0.1)/(R*(df['TEMPERATURA_EXT']+273.2)),2)
    df['Co'] =round((P_atm*MW*((Ca_ref)/1)*0.1)/(R*(df['TEMPERATURA_EXT']+273.2)),2)
    df['J_lineal'] = -df['D_lineal']*(df['Ca']-df['Co'])/Za
    df['J_lineal'] = round((df['J_lineal']*f_convert),5)

    # esta funcion calcula el promedio del flujo en la solucion lineal
    J_mean = round(pd.Series.mean(df['J_lineal']),2)

    return df, J_mean

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
def graphs_J_lineal(df):# """ <-- aquí cambié 31/03/2020 17:04"""
    #conjunto de funciones para guardar la grafica de los ppm sup e inf
    gf_1 = df.plot(x = "Fecha/Hora", y = ["Ca_ppm", "Cb_ppm"])
    gf_1.set_xlabel("Tiempo")
    gf_1.set_ylabel("Concentración [PPM]")
    plt.title('Concentración')
    #plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+'Concentracion.png') esto no ibaen coment 18:27 31/03/2020
    plt.savefig('./Gráficas/Grafica de Concentracion.png')

    #conjunto de funciones para guardar la grafica del flujo usando la solucion lineal
    #aqui tienes que buscar como configurar el texto del titulo y mostrar en el el flujo promedio de la semana o del rango de tiempo que pide el usuario
    gf_2 = df.plot(x = "Fecha/Hora", y = ["J_lineal"])
    gf_2.set_xlabel("Tiempo")
    gf_2.set_ylabel("Flujo [mol/m^2*dia]")
    plt.title('Flujo lineal')
    #plt.show()
    #plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+' Flujo_lineal.png') esto lo puse en coment: 18:22 31/03/2020
    plt.savefig('./Gráficas/Grafica de Flujo_lineal.png')

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
