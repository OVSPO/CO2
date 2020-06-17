#---------Libreria para la lectura y manejo de datos
import pandas as pd
#---------Libreria para procesamiento matematico
import numpy as np
#---------Framework para visualizacion de imagenes y datos
from matplotlib import pyplot as plt
#---------Modulo donde se encuentran las funciones realizadas para el proyecto
import Clean_data as cd
#-------Librería para hacer el archivo excel
from pandas import ExcelWriter

if __name__ == '__main__':
    df = pd.read_csv('radonParques20191001.raw', header=None, error_bad_lines=False, engine='python')

    #######30/04/2020 - Para las nuevas gráficas: Se crea otro dataframe con el archivo Excel y se le da nombre a la columna para ser utilizado en futuras operaciones (también se agrega esta columna al dataframe que se crea del archivo .raw)
    df_atm = pd.read_excel("Presion_atmosférica_cocuy.xls",'cl_presionat')
    #df_atm.columns = ['Fecha', 'Presion']
    #######

    df = cd.first_filter(df)
    df = cd.info_device_filter(df)
    df = cd.data_solutions(df)
    df = cd.mp_factors(df)
    df, flujo_medio = cd.calculate_params(df, df_atm)
    #df2 = df["Fecha/Hora"]+df["J_lineal"]
    #print(df)
    #df.to_csv('FD_PINUEL_TMP38_20200119.csv', index=None)

    #esto lo agrego el 31/03/2020 20:48
    #df.columns = ['Fecha/Hora', 'Consecutivo', 'Trama', 'Red', 'Nombre_estacion', 'Metodologia', 'Puerto_serial', 'Descriptor_campo', 'Ventilador', 'Ca_ppm', 'T_sup', 'Cb_ppm', 'T_inf', 'T_ext', 'D_lineal', 'Ca', 'J_lineal', 'Ca_compT', 'Ca_compP']

    writer = ExcelWriter('./archivo_excel/radonParques20191001.xlsx')
    df.to_excel(writer, 'Hoja de datos', index = False)
    writer.save()
    #hasta aquí agregué. Las siguientes líneas ya estaban
    cd.graphs_J_lineal(df, df_atm)
    plt.show()
