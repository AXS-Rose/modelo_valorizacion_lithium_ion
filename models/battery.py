import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from scipy.stats import gaussian_kde
from functions import log_a, valorización, total_cycle, synthetic_profile

class Battery_Degradation_Model:

    def __init__(self, Qmax=4.850, degradation_percentage=0.8, life_cycles=650,ds_SR=100, degradation_data=None):
        
        self.parameters = {
            "Qmax": Qmax,  # Carga nominal (Ah)
            "degradation_percentage": degradation_percentage,  # Por ejemplo, 80% de degradación
            "life_cycles": life_cycles,  # Por ejemplo, 1000 ciclos de vida
            "SR": ds_SR,  # Por ejemplo, 1000 ciclos de vida
            "degradation_data": degradation_data if degradation_data else {
                "100-0":        [1.00000],
                "100-25":       [0.78750],
                "75-0":         [1.12525],
                "100-50":       [0.43750],
                "75-25":        [0.68750],
                "50-0":         [1.03125],
                "100-75":       [0.40625],
                "75-50":        [0.29700],
                "62.5-37.5":    [0.28125],
                "50-25":        [0.62500],
                "25-0":         [1.00000],
            },
        }
        self.memoria_soc = []  # Inicialización de memoria SOC vacía
        self.setup_knn()  # Configura el modelo k-NN
        self.set_kde()
        self.set_std_cycles()

    def setup_knn(self):
        # Preparar los datos para el modelo k-NN
        X = []
        y = []

        for sr, factors in self.parameters["degradation_data"].items():
            sr_range = [float(x) for x in sr.split("-")]
            sr_numeric = sr_range[0] - sr_range[1]  # SR
            asr_numeric = sum(sr_range) / 2  # ASR
            for std_degradation_percentage, factor in zip([0.8], factors):
                X.append([asr_numeric, sr_numeric, std_degradation_percentage])
                y.append(factor)

        # Convertir a numpy arrays
        X = np.array(X)
        y = np.array(y)

        # Entrenar el modelo k-NN
        self.knn = KNeighborsRegressor(n_neighbors=3, weights="distance")
        self.knn.fit(X, y)  # Entrenar el modelo k-NN

        print("Modelo de celda seteado con exito")

    def set_kde(self):
            path = "C:/Users/Bruno/OneDrive - Universidad de Chile/BGMG/CASE/git_repositories/degradation_model/uncertainty_characterization/eta_values_sorted.csv"
            eta_values = pd.read_csv(path,delimiter=',',header=None)
            eta_values = eta_values.values.flatten()
            self.kde = gaussian_kde(eta_values)


    def set_std_cycles(self):
            SR_0 = 100 # soc range de un ciclo equivalente 
            SR = self.parameters["SR"] # soc range de los subciclos del dataset
            eq_cycle = self.parameters["life_cycles"]*(SR/SR_0)

            eta_0 = self.parameters["degradation_percentage"]**(1/eq_cycle)
            eq_cycle08 = 1/log_a(0.8,eta_0)

            self.parameters["life_cycles"] = eq_cycle08
            self.parameters["degradation_percentage"] = 0.8
            self.parameters["SR"] = 100

    def temp_factor(self, temp):
        # definimos los coeficientes ya fiteados
        coef = np.array([-1.25736777e-11,  4.79001576e-10,  5.01975901e-08,  5.04209738e-07,
                -3.61735311e-04,  1.12614410e-02,  1.02131291e+00])
        # creamos la funcion generadora de factores por temperatura
        polynomial = np.poly1d(coef)
        # Calculamos el factor ponderador por temperatura
        factor = np.clip(polynomial(temp),0,1)
        return factor
    
    def get_factor(self, soc, temp):
            # Obtenermos el SSR y el ASSR
            ssr = max(soc) - min(soc)
            assr = np.mean(soc)

            # Obtenemos el factor para ponderar los ciclos
            knn_factor = self.knn.predict(
                np.array([[assr, ssr, self.parameters["degradation_percentage"]]])
            )

            # definimos los ciclos del KNN
            cycles_0 = self.parameters["life_cycles"]
            cycles_k = knn_factor * cycles_0

            # definimos los ciclos en función de la temperatura
            t_factor = self.temp_factor(temp)
            cycles_k_ = cycles_k * t_factor

            # definimos el eta con incertidumbre
            noise = self.kde.resample(1)[0][0] - 0.999161393145505
            etak = 0.8**(1/cycles_k_) + noise 
            etak = np.clip(etak,0,1) # definimos limites porque el ruido puede generar valores demasiados extremos que no son reales
            return etak