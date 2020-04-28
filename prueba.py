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
    df = pd.read_csv('FD_PINUEL_TMP38_20200119.raw', header=None, error_bad_lines=False, engine='python')
    df = cd.first_filter(df)
    df = cd.info_device_filter(df)
    df = cd.data_solutions(df)
    df = cd.mp_factors(df)
    df, flujo_medio = cd.calculate_params(df)
    #df2 = df["Fecha/Hora"]+df["J_lineal"]
    #print(df)
    #df.to_csv('FD_PINUEL_TMP38_20200119.csv', index=None)

    #esto lo agrego el 31/03/2020 20:48
    #writer = ExcelWriter('D:/OVSPOP/programapython_original/archivo_excel/FD_PINUEL_TMP38_20200119.xlsx')
    writer = ExcelWriter('./archivo_excel/FD_PINUEL_TMP38_20200119.xlsx')
    df.to_excel(writer, 'Hoja de datos', index = False)
    writer.save()
    #hasta aquí agregué. Las siguientes líneas ya estaban

    cd.graphs_J_lineal(df)
    plt.show()
