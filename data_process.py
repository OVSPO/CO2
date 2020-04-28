#---------Libreria para la lectura y manejo de datos
import pandas as pd
#---------Framework para visualizacion de imagenes y datos
from matplotlib import pyplot as plt
#---------Modulo donde se encuentran las funciones realizadas para el proyecto
import Clean_data as cd
"""
def week_dataframe():
    #month = {'01':'Enero','02':'Febrero','03':'Marzo','04':'Abril','05':'Mayo','06':'Junio',
    #        '07':'Julio','08':'Agosto','09':'Septiembre', '10':'Octubre', '11':'Noviembre','12':'Diciembre'}
    return df
"""
if __name__ == '__main__':

    cd.main()
    
    #week_dataframe()

    """
    for i in range(21,20):
        df = pd.read_csv('./raw_files_piñuelas_2020/FD_PINUEL_TMP38_202002'+str(i)+'.raw', header=None, error_bad_lines=False, engine='python')
        df = main(df)
        df.to_csv('./csv_files_piñuelas_2020/FD_PINUEL_TMP38_202002'+str(i)+'.csv', index=None)
        """
    #df.plot(x = "Fecha/Hora", y = ["ppm_sup", "ppm_inf"])
    #df.plot(x = "Fecha/Hora", y = "J_lineal")
    #plt.show()
