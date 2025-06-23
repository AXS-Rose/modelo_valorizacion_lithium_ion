## Sobre el modelo de degradación 
El código en `degradation_model.ipynb` utiliza una base de datos pública de Standford, para no subirlo al repo, dejo el link al su ubicación

https://drive.google.com/drive/folders/1mSHdfOCpTYmt3MhcqC44RVpwrRL-YhxW?usp=sharing

# Explicación del Código de Valorización de Baterías

Este repositorio contiene un modelo para la valorización económica de baterías considerando su degradación y perfil de uso.

## Estructura del repositorio

### 1. `battery_valuation.py`
Este es el script principal donde se configuran los parámetros de simulación, se definen los modelos de batería (ideal y degradada) a comparar, se genera el perfil de uso y se calcula el valor económico de cada batería. Aquí se utilizan las funciones y clases definidas en los otros archivos.

### 2. `functions.py`
Contiene funciones auxiliares clave para la simulación:

- **`profile_repeat`**: Repite un perfil de capacidad o uso de batería un número determinado de veces para simular ciclos prolongados de operación.
- **`synthetic_profile`**: Genera un perfil sintético de carga y descarga según parámetros definidos por el usuario.
- **`total_cycle`**: Calcula el número total de ciclos equivalentes que una batería puede realizar bajo un perfil de uso específico, considerando la degradación.
- **`valorización`**: Calcula el valor económico de una batería degradada en comparación con una batería ideal, en función de los ciclos útiles restantes y otros parámetros.

### 3. `models/battery.py`
Incluye el modelo de degradación de la batería:

- **`Battery_Degradation_Model`**: Clase que representa el modelo de degradación de la batería, permitiendo simular cómo disminuye la capacidad útil de la batería a lo largo de los ciclos de carga y descarga.

## ¿Cómo usar el código?

1. Ajusta los parámetros de simulación en `battery_valuation.py` según tus necesidades (capacidad, SOH inicial, ciclos de vida, perfil de uso, etc.).
2. Ejecuta el script principal para obtener el valor económico de la batería degradada y compararlo con una batería ideal.
3. Puedes modificar o crear nuevos perfiles de uso utilizando las funciones de `functions.py`.

## Notas

- El código está documentado para facilitar su comprensión y modificación.
- Si tienes dudas sobre alguna función o clase, revisa los comentarios en el código fuente o consulta este README.

---
**Cualquier usuario puede adaptar este modelo para distintos tipos de baterías y aplicaciones cambiando los parámetros y perfiles de uso.**
