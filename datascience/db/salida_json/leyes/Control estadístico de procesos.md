---
title: "Control estadístico de procesos"
source_file: "Control estadístico de procesos.pdf"
category: "LEYES"
processed_date: "2026-08-14 00:00:28"
---

# Control estadístico de procesos

# **Capítulo** 9 # Índices de capacidad de procesos ## **Introducción** Como se estudió en el capítulo anterior, los procesos tienen variables de salida, los cuales, por lo general, deben cumplir con ciertas especifi caciones para que sea posible considerar que tal proceso funciona de manera satisfactoria. Analizar la **capacidad o habilicapacidad o habilidad de un proceso** consiste en conocer la amplitud **dad de un proceso** de la variación natural del proceso para una característica de calidad dada;

esto permitirá saber en qué medida tal característica de calidad es satisfactoria. En este capítulo se analizan los índices de capacidad que, como su nombre lo indica, son mediciones especializadas en evaluar la capacidad, que permiten comparar procesos y detectar la necesidad de mejoras. Por la sencillez de los índices, en ocasiones se abusa de su práctica y no se consideran sus limitaciones, por lo que es muy importante conocerlos bien para hacer una interpretación correcta.

166 ## **Procesos con doble especifi cación** En esta sección se supone que se tiene una característica de calidad de un producto o variable de salida de un proceso, del tipo valor nominal es mejor. Esto es que, para considerar que hay calidad, las mediciones deben ser iguales a cierto valor nominal o ideal (N), o al menos tienen que estar dentro de ciertas especifi caciones inferior (EI) y superior (ES).

###### **Ejemplo 9.1** Una característica importante de los costales de fertilizante es que su peso debe ser de 50 kg. La especifi cación inferior para el peso es EI 5 49 kg, y la superior es ES 5 51. De los datos del ejemplo 14.4 se sabe que la media del peso es m 5 49.76 y usando el rango medio se estima que la desviación estándar es s 5 0.51. Con base en esto se quiere saber en qué medida el proceso ha estado cumpliendo con especifi caciones. Una primera forma de averiguar esto es grafi car la distribución del proceso, suponiendo una distribución normal, con m 5 49.76 y s 5 0.51. Esta distribución se muestra en la fi gura 9.1, de donde se descubre que el proceso no está centrado, ya que la media del proceso es menor que 50; además, hay mucha variación ya que la distribución no cabe dentro de especifi caciones. En seguida se ve cómo las situaciones que se observan en la fi gura 9.1 son refl ejadas por los índices de capacidad.

EI ESFigura 9.1 Capacidaddel proceso del ejemplo9.1. 48 49 50 51 52 ### **Índice** **_C_** **_p_** El índice de capacidad potencial del proceso, _Cp_ se defi ne de la siguiente manera:

donde s representa la desviación estándar del proceso, y ES y EI son las especifi caciones superior e inferior para la característica de calidad. Como se puede observar, el **índice** **_Cp_** compara el ancho de las especifi caciones o variación tolerada para el proceso con la amplitud de la variación real del proceso:

Procesos con doble especifi cación ❚ 167 Decimos que 6s (seis veces la desviación estándar) es la variación real, debido a las propiedades de la distribución normal (vea el apéndice), en las que se afi rma que entre m 6 3s se encuentra 99.73% de los valores de una variable con distribución normal (incluso si no hay normalidad,1 en m 6 3s se encuentra un gran porcentaje de la distribución debido a la desigualdad de Chebyshev y la regla empírica, capítulo 8).

#### **Interpretación del índice** **_Cp_** Para que el proceso pueda considerarse potencialmente capaz de cumplir con especifi caciones, se requiere que la variación real (natural) siempre sea menor que la variación tolerada. De aquí que lo deseable es que el índice _Cp_ sea mayor que 1, y si el valor del índice _Cp_ es menor que uno, es una evidencia de que no cumple con especifi caciones. Para una mayor precisión en la interpretación, la tabla 9.1 presenta cinco categorías de procesos que dependen del valor del índice _Cp_ , suponiendo que el proceso está centrado. Ahí se ve que el _Cp_ debe ser mayor que 1.33, si se quiere tener un proceso bueno, pero debe ser mayor o igual que 2 si se quiere tener un proceso de clase mundial (calidad Seis Sigma). Además, en la tabla 9.2 se ha traducido el valor del índice en porcentaje de artículos que no cumplirían especifi caciones y en la cantidad de artículos o partes defectuosas por cada millón producido (partes por millón, PPM). Una observación que se desprende de la tabla referida es que los valores del _Cp_ no son directamente iguales a un porcentaje de defectuosos.

**Tabla 9.1** Valores del _Cp_ y su interpretación.

|**Valor del índice****_Cp_**|**Clase o categoría****de proceso**|**Decisión****(si el proceso está centrado)**| |---|---|---| |_Cp_ ≥2|Clase mundial|Se tiene calidad Seis Sigma.| |_Cp_ .1.33|1|Adecuado.| |1, _Cp_ ≤1.33|2|Parcialmente adecuado, re quiere de un control estricto.| |0.67, _Cp_ ≤1|3|No adecuado para el trabajo. Un análisis del proceso es necesario.Requiere modif caciones serias para alcanzar una calidad satisfactoria.| |_Cp_ ≤0.67|4|No adecuado para el trabajo. Requiere modif caciones muy serias.| |Nota: Si el_Cpk_ ,_Cp ,_|entonces una vez que se c|entre el proceso se tendrá la clase de proceso que se indica.| En el caso del ejemplo 9.1, el índice _Cp_ está dado por:

La variación tolerada es de 2, y la variación real es mayor, ya que es de 3.06 (vea la fi gura 9.1). De acuerdo con la tabla 9.1, el proceso es de cuarta categoría, con una capacidad totalmente inadecuada y requiere modifi caciones muy serias. En función de la tabla 9.2, se espera que si el proceso estuviera centrado entonces arrojaría casi 7% de costales fuera de especifi caciones, que corresponde a 70 000 PPM, lo cual se considera muy inadecuado.

> 1 Hay una defi nición del índice _Cp_ independiente de la distribución de la característica de calidad, creada por el reporte técnico de ISO 12783:

> 1 donde _P_ 99.865 es el percentil 99.865 de la distribución de la característica de calidad, y _P_ 0.135 es el percentil 0.135. De esta manera, cualquiera que sea la distribución, entre estos percentiles se ubicará 99.73% de los valores de la característica de calidad.

168 **Tabla 9.2** Los índices _Cp , Cpi_ y _Cps_ en términos de la cantidad de piezas malas, bajo normalidad y proceso centrado en el caso de doble especifi cación.

|**Valor del**|**Proceso con dobl****(índic**|**e especif cación****e****_Cp_)**|**Con referencia a u****(****_Cpi_,**|**na sola especif cación****_Cps_,****_Cpk_)**| |---|---|---|---|---| |**índice****(corto plazo)**|**% fuera de las dos****especif caciones**|**Partes por millón****fuera (PPM)**|**% fuera de una****especif cación**|**Partes por millón****fuera (PPM)**| |0.2|54.8506|548506.130|27.4253|274253.065| |0.3|36.8120|368120.183|18.4060|184060.092| |0.4|23.0139|230139.463|11.5070|115069.732| |0.5|13.3614|133614.458|06.6807|66807.229| |0.6|07.1861|071860.531|03.5930|35930.266| |0.7|03.5729|035728.715|01.7864|17864.357| |0.8|01.6395|016395.058|00.8198|08197.529| |0.9|00.6934|006934.046|00.3467|03467.023| |1.0|00.2700|002699.934|00.1350|01349.967| |1.1|00.0967|000966.965|00.0483|00483.483| |1.2|00.0318|000318.291|00.0159|00159.146| |1.3|00.0096|000096.231|00.0048|00048.116| |1.4|00.0027|000026.708|00.0013|00013.354| |1.5|00.0007|000006.802|00.0003|00003.401| |1.6|00.0002|000001.589|00.0001|00000.794| |1.7|00.0000|000000.340|00.0000|00000.170| |1.8|00.0000|000000.067|00.0000|00000.033| |1.9|00.0000|000000.012|00.0000|00000.006| |2.0|00.0000|000000.002|00.0000|00000.001| Un aspecto a destacar es que la interpretación que se da en las tablas 9.1 y 9.2 se fundamenta en tres supuestos: que la característica de calidad se distribuye de modo normal, que el proceso es estable (está en control estadístico) y que se conoce la desviación estándar del proceso, es decir, la desviación estándar no es una estimación con base en una muestra. La violación de alguno de estos supuestos, sobre todo de los últimos dos, afecta sensiblemente la interpretación de los índices. Más adelante se verá la interpretación de los índices cuando éstos se calculan (estiman) a partir de una muestra.

Si al analizar el proceso se encuentra que su capacidad no es compatible con las tolerancias, existen tres opciones: mejorar el proceso, cambiar las tolerancias o sufrir e inspeccionar 100% de los productos. Por el contrario, si hay capacidad excesiva, ésta se puede aprovechar, por ejemplo, reasignando productos a máquinas menos precisas, acelerando el proceso y reduciendo la cantidad de inspección.

### **Índices** **_Cpk_ ,** **_Cpi_ ,** **_Cps_** El índice _Cp_ estima la capacidad potencial del proceso para cumplir con especifi caciones, pero una de sus desventajas es que no toma en cuenta el centrado del proceso, ya que en su fórmula para calcularlo no incluye la media del proceso m. Una forma de corregir esto es evaluar por separado el Procesos con doble especifi cación ❚ 169 cumplimiento de las especifi caciones inferior y superior, a través del **índice de capacidad para la especifi cación inferior (** **_Cpi_ )** , y el **índice de capacidad para la superior (** **_Cps_ )** , que se calculan de la siguiente manera:

**índice de capacidad inferior (** **_Cpi_ ) índice de capacidad superior (** **_Cps_ )** Estos índices sí toman en cuenta m y calculan la distancia de la media del proceso a una de las especifi caciones, que representa la variación tolerada para el proceso de un solo lado de la media. A tal distancia se le divide entre 3s porque sólo se está tomando en cuenta la mitad de la variación natural del proceso. Para interpretar los índices unilaterales se puede usar la tabla 9.2, que señala el porcentaje de producto que no cumple con especifi caciones.

En el ejemplo 9.1, del peso de los costales, se tiene que:

Luego, como el índice para la especifi cación inferior, _Cpi_ , es el más pequeño y es menor que uno, entonces los mayores problemas están por la parte inferior (vea la fi gura 9.1). Si se usa la tabla 9.2, dado que _Cpi_ 5 0.50, entonces el porcentaje de producto que pesa menos que EI 5 49 kg es 6.68%. Cabe notar que también en la especifi cación superior hay problemas, ya que _Cps_ 5 0.81, por lo que el porcentaje de producto que pesa más de ES 5 51 kg es 0.82% (vea la tabla 9.2).

Por su parte, el **índice de capacidad real del proceso (** **_Cpk_ )** se puede ver como una versión corregida del _Cp_ que sí toma en cuenta el centrado del proceso. Para calcularlo hay varias formas equivalentes, una de las más comunes es la siguiente:

**índice de capacidad real del proceso (** **_Cpk_ )** Como se puede apreciar, el índice _Cpk_ es igual al valor más pequeño de entre _Cpi_ y _Cps,_ es decir, el índice _Cpk_ es igual al índice unilateral más pequeño, por lo que si el valor del _Cpk_ es satisfactorio (mayor que 1.25), eso indicará que el proceso en realidad es capaz. Si _Cpk_ , 1, entonces el proceso no cumple con por lo menos una de las especifi caciones. Algunos elementos adicionales para la interpretación del índice _Cpk_ son:

- a El índice _Cpk_ siempre será menor o igual que el índice _Cp_ . Cuando sean muy próximos, eso indicará que la media del proceso está muy cerca del punto medio de las especifi caciones, por lo que la capacidad potencial y real son similares.

- a Si el valor del índice _Cpk_ es mucho más pequeño que el _Cp_ , esto indicará que la media del proceso está alejada del centro de las especifi caciones. De esa manera, el índice _Cpk_ estará indicando la capacidad real del proceso, y si se corrige el problema de descentrado, se alcanzará la capacidad potencial indicada por el índice _Cp._ - a Cuando el valor del _Cpk_ sea mayor que 1.25 en un proceso ya existente, se considerará que se tiene un proceso con capacidad satisfactoria. Mientras que para procesos nuevos se pide un _Cpk_ . 1.45.

- a Es posible tener valores del _Cpk_ iguales a cero o negativos, e indicarán que la media del proceso está fuera de las especifi caciones.

170 A partir del ejemplo 9.1, del peso de los costales, se tiene que:

Esto en términos generales indica una capacidad muy pobre. Por lo tanto, cierta proporción de costales no tiene un peso adecuado, como ya se había visto con los índices unilaterales y en la fi gura 9.1.

Como el _Cpk_ 5 0.50 es menor que el _Cp_ 5 0.65, entonces existe un problema de centrado del proceso, como se vio en la fi gura 9.1, por lo que la primera recomendación de mejora para ese proceso sería que optimice su centrado, con lo cual alcanzaría su mejor potencial actual, que indica el valor del _C_ 5 0.65. _p_ ### **Índice** **_K_** **índice de centrado del proceso (** **_K_ )** Como se ha visto a través del ejemplo 9.1, un aspecto importante en el estudio de la capacidad de un proceso es evaluar si la distribución de la característica de calidad está centrada respecto a las especifi caciones, por ello es útil calcular el **índice de centrado del proceso (** **_K_ ),** que se calcula de la siguiente manera:

Como se aprecia, este indicador mide la diferencia entre la media del proceso, m, y el valor objetivo o nominal, _N_ (o _target_ ), para la correspondiente característica de calidad, y a esta diferencia la compara contra la mitad de la amplitud de las especifi caciones. El hecho de multiplicar por 100 ayuda a tener una medida porcentual. La interpretación usual de los valores de _K_ es la siguiente:

- a Si el signo del valor de _K_ es positivo, signifi ca que la media del proceso es mayor que el valor nominal, y será negativo cuando m , _N_ .

> a Valores de _K_ menores que 20% en términos absolutos se pueden considerar aceptables, pero a medida que el valor absoluto de _K_ sea más grande que 20%, indica un proceso muy descentrado, lo que puede contribuir de manera signifi cativa a que la capacidad del proceso para cumplir especifi caciones sea baja.

> a El valor nominal, _N_ , es la calidad objetivo y óptima; cualquier desviación respecto a este valor lleva un detrimento en la calidad. Por ello, cuando un proceso esté descentrado de manera signifi cativa, se deben hacer esfuerzos serios para centrarlo, lo que regularmente es más fácil que disminuir la variabilidad.

En el ejemplo 9.1 del peso de los costales, si se considera que el valor nominal _N_ 5 50 kg, entonces el índice _K_ es:

De esta forma, la media del proceso está desviada 24% a la izquierda del valor nominal, por lo que el centrado del proceso es inadecuado y esto contribuye de manera signifi cativa a la baja capacidad del proceso para cumplir con la especifi cación inferior, como ya se había visto a través de la fi gura 9.1 y los anteriores índices de capacidad.

Procesos con sólo una especifi cación ❚ 171 ## **Procesos con sólo una especifi cación** Existen procesos cuyas variables de salida tienen sólo una especifi cación, ya sean variables del tipo entre más grande mejor, en las que lo que interesa es que sean mayores que cierto valor mínimo (EI), o variables del tipo entre más pequeña mejor, en las que lo que se quiere es que nunca excedan un cierto valor máximo (ES). Para evaluar la capacidad de estos procesos se utilizan los índices _Cpi_ o _Cps_ que se vieron antes.

###### **Ejemplo 9.2** ##### **Especifi cación inferior** En una armadora de autos, en el área de pintado, una característica de calidad es el espesor de la capa antipiedra en la zona trasera de los arcos de rueda, que debe ser mínimo de 100 micras ( _EI_ 5 100). Para asegurar el cumplimiento de esta especifi cación, se lleva una carta de control _X_– 2 _R_ ; de la información proporcionada por esta carta se sabe que el proceso está en control estadístico y que m 5 105 y s 5 6.5. En este caso no es posible calcular el índice _Cp_ , ya que sólo se cuenta con la especifi cación inferior; más bien, dado el tipo de variable, lo que se debe calcular es el índice para la especifi cación inferior _Cpi_ que, como ya se vio, está dado por:

lo que indica que la capacidad del proceso es muy mala. Esto se corrobora con la tabla 9.2, de la que se obtiene que el proceso genera entre 18.4 y 27.4% de productos cuyo espesor de capa es menor que _EI_ 5 100. Ajustando a 22%, indica que se tienen 220 000 PPM (productos por cada millón) que no cumplen con dicha especifi cación.

### **Índice** **_Cpm_ (índice de Taguchi)** Los índices _Cp_ y _Cpk_ están pensados a partir de que lo importante para un proceso es reducir su variabilidad para cumplir con las especifi caciones. Sin embargo, desde el punto de vista de G. Taguchi, cumplir con especifi caciones no es sinónimo de buena calidad y la reducción de la variabilidad debe darse pero en torno al valor nominal (calidad óptima). Es decir, la mejora de un proceso según Taguchi debe estar orientada a reducir su variabilidad alrededor del valor nominal, _N_ , y no sólo orientada a cumplir con especifi caciones. En consecuencia de lo anterior, Taguchi (1986) propone que la capacidad del proceso se mida con el índice _Cpm_ , que está defi nido por:

donde t (tau) está dada por:

_N_ es el valor nominal de la característica de calidad, y EI y ES son las especifi caciones inferior y superior. El valor de _N_ generalmente es igual al punto medio de las especifi caciones, es decir, _N_ 5 0.5(ES 1 EI). Note que el índice _Cpm_ compara el ancho de las especifi caciones con 6t, pero t no sólo toma en cuenta la variabilidad del proceso, a través de s2 , sino que también se preocupa por su centrado a través de (m – _N_ )2 . De esta forma, si el proceso está centrado, es decir, si m 5 _N_ , entonces el _Cp_ y el _Cpm_ son iguales.

En el caso del ejemplo 9.1, sobre el peso de los costales:

172 _Interpretación._ Cuando el índice _Cpm_ es menor que 1, eso indica que el proceso no cumple con especifi caciones, ya sea por problemas de centrado o por exceso de variabilidad. Por lo que en el caso de los costales no se cumple con especifi caciones y, como se aprecia en la fi gura 9.1, se debe tanto a exceso de variación como a que el proceso está descentrado.

Por el contrario, cuando el índice _Cpm_ es mayor que uno, entonces eso querrá decir que el proceso cumple con especifi caciones y, en particular, que la media del proceso está dentro de la tercera parte media de la banda de las especifi caciones. Si _Cpm_ es mayor que 1.33, entonces el proceso cumple con especifi caciones, pero además la media del proceso está dentro de la quinta parte media del rango de especifi caciones. En el caso del ejemplo 9.1, la quinta parte media de la banda de especifi caciones es 506 (1/5).

## **Estimación de los índices mediante una muestra (estimación por intervalo)** Para calcular los índices de capacidad e interpretarlos se necesita conocer la media, m, y la desviación estándar, s, del proceso con una buena aproximación. Sin embargo, no siempre se conocen estos parámetros, por lo que en esas situaciones será necesario utilizar datos muestrales y estimar estos índices por intervalo. Sea _x_ 1, _x_ 2, . . . , _xn_ , una mu ~~estra aleatoria del~~ pr ~~oceso~~ , y _x_ y _S_ la media y la desviación estándar de tal muestra. Si lo ~~s índices se estim~~ an ~~usan~~ do _x_ y _S_ en lugar de m y s, respectivamente, entonces la estimación puntual de los índices estará dada por:

y si la muestra es pequeña, de unas cuantas decenas (menor que 80, por ejemplo), es incorrecto comparar los valores estimados con los valores mínimos recomendados para los índices. También es erróneo interpretar los valores estimados de los índices como en la tabla 9.2, ya que los valores mínimos son para los verdaderos índices, o índices poblacionales, y no para su estimación muestral. Si los índices son estimados con base en muestras pequeñas, entonces un valor grande de un índice muestral no necesariamente implica que se tiene una buena capacidad de proceso. Lo contrario también es verdad: un valor pequeño del índice estimado no necesariamente implica mala capacidad del proceso.

Por lo anterior, lo que debe hacerse es una estimación por intervalo (vea Gutiérrez Pulido y de la Vara, 2009), en la cual se toma en cuenta el error estándar de su correspondiente estimador muestral (vea Kushler y Hurley, 1992). De forma específi ca, los intervalos de confi anza para _Cp_ , _Cpk_ y _Cpm_ están dados por:

Estimación de los índices mediante una muestra ❚ 173 donde _n_ es el tamaño de muestra y _Z_ a/2 es el percentil de la distribución normal que determina la confi anza de la estimación (si se quiere trabajar con 95% de confi anza, el valor de _Z_ a/2 es 1.96). De esta manera, el verdadero valor del índice de capacidad del proceso se encontrará entre el intervalo obtenido con las expresiones anteriores, con la confi anza deseada.

###### **Ejemplo 9.3** Supongamos que una característica de calidad tiene especifi caciones de 50 6 1. Para tener una primera idea de la capacidad del proceso para cumplir con esta especifi cación, se obtiene una muestra aleatoria de 40 unidades producidas por el proceso. De las mediciones de esas 40 unidades se obtiene que la media y la desviación estándar para la muestra son: _X_– 5 50.15 y _S_ 5 0.289. Con estos valores se estiman puntualmente los índices:

Para tener una idea del valor de los índices poblacionales del proceso, se calcula un intervalo de confi anza a 95%:

El 0.26, el 0.24 y el 0.22 en las anteriores ecuaciones son los errores de estimación para cada índice. De esta manera, con una confi anza de 95%, el verdadero valor del índice _Cp_ está entre 0.89 y 1.41; el de _Cpk_ se localiza entre 0.74 y 1.22, y el de _Cpm_ entre 0.80 y 1.24. Por lo tanto, con base en la muestra sería riesgoso afi rmar que el proceso es potencialmente capaz, ya que el valor real del _Cp_ podría ser de hasta 0.89; pero también sería riesgoso afi rmar que es malo, ya que el verdadero valor del _Cp_ podría ser 1.41. Lo mismo se puede decir respecto a la capacidad real, ya que lo mismo puede ser mala ( _Cpk_ 5 0.74, _Cpm_ 5 0.80) que buena ( _Cpk_ 5 1.22, _Cpm_ 5 1.24). Para reducir esta incertidumbre y el error de estimación, es necesario medir más piezas (incrementar el tamaño de muestra).

174 ###### **Preguntas de repaso y ejercicios del capítulo 9**

1. ¿Cuándo se dice que un proceso es capaz o hábil?

2. Respecto a los índices _Cp_ y _Cpk_ explique:

- _a_ ) ¿Qué mide el índice _Cp_ ? - _b_ ) ¿Qué signifi ca que un proceso esté descentrado? Explique gráfi camente con un ejemplo (vea la fi gura 9.1).

- _c_ ) ¿El índice _Cp_ toma en cuenta lo centrado de un proceso? Argumente su respuesta.

- _d_ ) ¿Por qué se dice que el índice _Cp_ mide la capacidad potencial y el _Cpk_ la capacidad real? Apóyese en los puntos anteriores para explicar.

3. Si una característica de calidad debe estar entre 30 6 2, y se sabe que su media y desviación estándar están dadas por m 5 29.3 y s 5 0.5, calcule e interprete con detalles los siguientes índices: _Cp_ , _Cpk_ , _K_ .

4. Para el ejercicio 15 del capítulo 8, sobre el grosor de las láminas de asbesto se tiene que las especifi caciones son: EI 5 4.2 mm y ES 5 5.8 mm. Además de las mediciones hechas en los últimos tres meses, se aprecia un proceso que tiene una estabilidad aceptable, con m 5 4.75 y s 5 0.45.

- _a_ ) Calcule el índice _K_ e interprételo.

- _b_ ) Obtenga los índices _Cp_ y _Cpk_ e interprételos.

- _c_ ) Con base en la tabla 9.2 estime el porcentaje de láminas que no cumplen con especifi caciones: del lado inferior, del superior y de ambos lados.

- _d_ ) En resumen, ¿el proceso cumple con especifi caciones? Argumente su respuesta.

5. Los siguientes datos representan las mediciones de viscosidad de los últimos tres meses de un producto lácteo. El objetivo es tener una viscosidad de 80 6 10 cps.

|84|81|77|80|80|82|78|83| |---|---|---|---|---|---|---|---| |81|78|83|84|85|84|82|84| |82|80|83|84|82|78|83|81| |86|85|79|86|83|82|84|82| |83|82|84|86|81|82|81|82| |87|84|83|82|81|84|84|81| |78|83|83|80|86|83|82|86| |87|81|78|81|82|84|83|79| |80|82|86|82|80|83|82|76| |79|81|82|84|85|87|88|90| - _a_ ) Construya una gráfi ca de capacidad de este proceso (histograma con tolerancias) y genere una primera opinión sobre la capacidad.

- _b_ ) Calcule la media y la desviación estándar y, considerando estos parámetros como poblacionales,

estime los índices _Cp_ , _Cpk_ , _Cpm_ y _K_ , e interprételos con detalle.

- _c_ ) Con base en la tabla 9.2 estime el porcentaje fuera de especifi caciones.

- _d_ ) Las estimaciones hechas en los dos incisos anteriores y las correspondientes interpretaciones se deben ver con ciertas reservas dado que son estimaciones basadas en una muestra. ¿Por qué se deben ver con reservas?

6. Para el ejercicio 16 del capítulo 8, estime los índices de capacidad _Cp_ y _Cpk_ utilizando todos los datos.

7. Para el ejercicio 18 del capítulo 8, estime los índices de capacidad _Cp_ y _Cpk_ para cada propuesta. ¿Cuál propuesta parece mejor?

8. Una característica importante en la calidad de la leche de vaca es la concentración de grasa. En una industria en particular se ha fi jado que el estándar mínimo que debe cumplir el producto que se recibe directamente de los establos lecheros es de 3.0%. Si de los datos históricos se sabe que m 5 4.1 y s 5 0.38.

- _a_ ) Calcule el _Cpi_ e interprételo.

- _b_ ) Con base en la tabla 9.2 estime el porcentaje fuera de especifi caciones.

- _c_ ) ¿La calidad es satisfactoria?

9. En una empresa que elabora productos lácteos se tiene como criterio de calidad para la crema que ésta tenga un porcentaje de grasa de 45 con una tolerancia de 65. De acuerdo con los muestreos de los últimos meses, se tiene una media de 44.5 con una desviación estándar de 1.3. Haga un análisis de capacidad para ver si se está cumpliendo con la calidad exigida ( _Cp_ , _Cpk_ , _K_ , _Cpm_ , _límites reales_ ), represente gráfi camente sus resultados y comente.

10. El volumen en un proceso de envasado debe estar entre 310 y 330 ml. De acuerdo con los datos históricos se tiene que m 5 318 y s 5 4. ¿El proceso de envasado funciona bien en cuanto al volumen? Argumente su respuesta.

11. El porcentaje de productos defectuosos en un proceso es de 2.3%. Con base en la tabla 9.2 estime el _Cp_ de este proceso.

12. Si un proceso tiene un _Cps_ 5 1.3, estime las PPM fuera de especifi caciones (apóyese en la tabla 9.2).

13. La especifi cación del peso de una preforma en un proceso de inyección de plástico es de 60 6 1 g. Para hacer una primera valoración de la capacidad del proceso se obtiene una muestra aleatoria de _n_ 5 40 piezas, y se obtiene que _X_– 5 59.88 y _S_ 5 0.25.

Preguntas de repaso y ejercicios del capítulo 9 ❚ 175 - _a_ ) Estime, con un intervalo de confi anza de 95%, los índices _Cp_ , _Cpk_ y _Cpm_ e interprete cada uno de ellos.

- _b_ ) ¿Hay seguridad de que la capacidad del proceso sea satisfactoria? - _c_ ) ¿Por qué fue necesario estimar por intervalo?

14. Conteste los primeros incisos del problema anterior, pero ahora suponiendo que el tamaño de la muestra fue de _n_ 5 140. ¿Las conclusiones serían las mismas?

15. Resuelva el problema 13, pero con _n_ 5 40 piezas, _X_– 5 59.88 y _S_ 5 0.15.