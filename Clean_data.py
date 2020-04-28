# Libreria para realizar analisis de datos, y crear datos estructurados
import pandas as pd
# Libreria para trabajar con expresiones regulares de texto
import re
# Framework y libreria para trabajar con graficos y imagenes
from matplotlib import pyplot as plt

#primera función de filtro inicial, pone cabeceras y elimina las que no son de utilidad para el modelo
def first_filter(df):
    # esta funcion ingresa las cabeceras del dataframe
    df.columns = ['Fecha/Hora','Consecutivo','Trama','Red','Nombre_estacion','Metodologia','Puerto_serial','Descriptor_campo','Ventilador','ppm_sup',
                  'Temp_sup','V_lamp_sup','ppm_inf','Temp_inf','V_lamp_inf','Flujo','Contador_Radon','U_vol_k1','Temp_k1_sup','U_vol_k2',
                  'Temp_k2_inf','U_vol_k3','Temp_k3','U_vol_k4','Temp_k5','Temp_Ext','Vol_tmp','Temp_interna','Check_sum','Final']

    # en esta parte se eliminan las columnas del dataframe que no se van a utilizar
    del df['Check_sum']
    del df['Final']
    del df['Vol_tmp']
    del df['Temp_interna']
    del df['Temp_k5']
    del df['U_vol_k4']
    del df['Temp_k3']
    del df['U_vol_k3']
    del df['Temp_k2_inf']
    del df['U_vol_k2']
    del df['Temp_k1_sup']
    del df['U_vol_k1']
    del df['V_lamp_sup']
    del df['V_lamp_inf']
    del df['Contador_Radon']
    del df['Flujo']

    # en esta parte se eliminan las filas del dataframe que tienen datos iguales a 0, los cuales no sirven para el estudio
    df = df[df['ppm_sup'] != 0]
    df = df[df['ppm_inf'] != 0]

    return df

# funcion para multiplicar todos los datos por los factores que se especifican en el geodata
def mp_factors (df):
    # esta parte convierte la columna de texto a numero
    df['Temp_inf'] = pd.to_numeric(df['Temp_inf'])

    df['ppm_sup'] = df['ppm_sup']/10
    df['ppm_inf'] = df['ppm_inf']/10

    df['Temp_sup'] = df['Temp_sup']/10
    df['Temp_inf'] = df['Temp_inf']/10
    df['Temp_Ext'] = df['Temp_Ext']/100

    return df
# funcion para calcular todos los parametros y variables necesarias para sacar la solucion lineal
def calculate_params(df, p_atm, ref_Ca, ref_Cb):
#def calculate_params(df):
    # esta parte saca los promedios de temperatura de los sensores superiores e inferiores, la funcion round, redondea el promedio a un decimal
    t_sup_mean = round(pd.Series.mean(df['Temp_sup']), 1)
    t_inf_mean = round(pd.Series.mean(df['Temp_inf']), 1)

    #constantes necesarias para el calculo de la solucion lineal
    DSTP = 1.39*10**-5
    MW = 44.01
    R = 8.3157
    #P_atm = 635 #corresponde a la presion absoluta por tabla de la altura altitud: 3774
    #ref_Ca = ((404*P_atm)/1013)*(298/(273.2+t_sup_mean))

    #---------Valor de referencia 5.2 utilizando las vigencias del trabajo en campo
    #ref_Ca = 5.2
    #ref_Cb = ((404*P_atm)/1013)*(298/(273.2+t_inf_mean))
    Za = -0.03333
    f_convert = (MW*1000)/(86400)

    # Aqui se realizan todos lso calculos necesarios para tener el flujo en la solucion lineal, las ecuaciones estan en el archivo word, orden de ecuaciones.........

    #df['DSTP_lineal'] = DSTP*(((273.2+(df['Temp_sup']+df['Temp_inf'])/2)/273.2)**(1.75*(1013/P_atm)))
    df['DSTP_lineal'] = DSTP*(((273.2+df['Temp_sup'])/273.2)**(1.75*(1013/P_atm)))
    df['Ca'] =round((P_atm*MW*df['ppm_sup']*0.1)/(R*(df['Temp_sup']+273.2)),2)
    #df['Co'] =round((P_atm*MW*((ref_Ca+ref_Cb)/2)*0.1)/(R*(df['Temp_Ext']+273.2)),2)
    df['Co'] =round((P_atm*MW*((ref_Ca)/1)*0.1)/(R*(df['Temp_Ext']+273.2)),2)
    df['J_lineal'] = -df['DSTP_lineal']*(df['Ca']-df['Co'])/Za
    df['J_lineal'] = round((df['J_lineal']*f_convert),5)

    # esta funcion calcula el promedio del flujo en la solucion lineal
    J_mean = round(pd.Series.mean(df['J_lineal']),2)

    return df, J_mean

# esta funcion corrige una corrupcion de los datos en la temperatura del sensor inferior
def data_solutions (df):
    #condicional para verificar que hay datos corruptos que convierten la columna en tipo objecto
    if df['Fecha/Hora'].dtypes == df['Temp_inf'].dtypes:
        # creo una columna llamada bool donde los valores que estan en false son los datos corruptos
        df.loc[df['Temp_inf'].str.len() != 4, 'bool'] = False
        # si hay un dato falso en bool, ingresa al loop
        if False in df['bool']:
            #recorro todas las filas del dataframe y reemplazo el valor corrupto por el real
            for i in df.index:
                df.at[i, 'Temp_inf'] = df['Temp_inf'].loc[i][:4] if df['bool'][i] == False else df['Temp_inf'].loc[i]
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
    ref_Ca = float(input())

    print("Digite el valor de referencia para el sensor inferior: ")
    ref_Cb = float(input())

    print("Digite el valor del tao de subida [min]: ")
    tao_up = int(input())

    print("Digite el valor del tao de bajada [min]: ")
    tao_down = int(input())

    #esta funcion retorna multiples parametros
    return d_if, d_ef, p_atm, ref_Ca, ref_Cb, tao_up, tao_down

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
def graphs_J_lineal(df, date_ini, date_end, J_lineal_mean):
#def graphs_J_lineal(df):
    #conjunto de funciones para guardar la grafica de los ppm sup e inf
    gf_1 = df.plot(x = "Fecha/Hora", y = ["ppm_sup", "ppm_inf"])
    gf_1.set_xlabel("Tiempo")
    gf_1.set_ylabel("Concentración [PPM]")
    plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+'Concentracion.png')

    #conjunto de funciones para guardar la grafica del flujo usando la solucion lineal
    #aqui tienes que buscar como configurar el texto del titulo y mostrar en el el flujo promedio de la semana o del rango de tiempo que pide el usuario
    gf_2 = df.plot(x = "Fecha/Hora", y = "J_lineal")
    gf_2.set_xlabel("Tiempo")
    gf_2.set_ylabel("Flujo [mol/m^2*dia]")
    plt.show()
    plt.savefig('./graficas/Grafica de '+date_ini+' a '+date_end+' Flujo_lineal.png')

#funcion main que tiene todas las funciones anteriores
def main():
    #Parametros de entrada
    d_if, d_ef, p_atm, ref_Ca, ref_Cb, tao_up, tao_down = inputs_params()

    #Lectura del data frame
    df = lecture(d_if, d_ef)

    #Filtrado y limpieza de datos
    df = first_filter(df)
    df = info_device_filter(df)
    df = data_solutions(df)

    # Solución modelo lineal
    df = mp_factors(df)
    df, J_lineal_mean = calculate_params(df, p_atm, ref_Ca, ref_Cb)

    #Gráficas
    graphs_J_lineal(df, date_ini, date_end, J_lineal_mean)

    return df
